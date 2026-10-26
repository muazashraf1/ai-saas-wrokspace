import datetime
from decimal import Decimal
from typing import Tuple, Dict, Any
from django.utils import timezone
from django.db.models import Sum
from .models import PlanLimit, UsageRecord


def get_plan_limits_for_workspace(workspace) -> PlanLimit:
    """Retrieves plan limits for the workspace's plan (defaults to 'free' if missing)."""
    plan_name = getattr(workspace, 'plan', 'free') or 'free'
    limits = PlanLimit.objects.filter(plan=plan_name).first()
    if not limits:
        # Fallback defaults if seed data not yet populated
        defaults = {
            'free': {'daily_questions': 20, 'monthly_tokens': 100000, 'max_documents': 10, 'max_file_mb': 10},
            'pro': {'daily_questions': 200, 'monthly_tokens': 2000000, 'max_documents': 100, 'max_file_mb': 50},
        }.get(plan_name, {'daily_questions': 20, 'monthly_tokens': 100000, 'max_documents': 10, 'max_file_mb': 10})
        limits, _ = PlanLimit.objects.get_or_create(plan=plan_name, defaults=defaults)
    return limits


def get_next_utc_midnight() -> str:
    """Returns the next UTC midnight timestamp in ISO 8601 format."""
    now_utc = timezone.now()
    tomorrow_utc = (now_utc + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return tomorrow_utc.isoformat().replace('+00:00', 'Z')


def check_question_quotas(user, workspace) -> Tuple[bool, Dict[str, Any]]:
    """
    Checks daily question and monthly token quotas for a user/workspace.

    The daily counter includes pending, answered and unsupported questions. Failed
    provider calls are excluded, as they are not charged. Callers serialize this
    check with a user row lock before creating a pending request.
    Returns:
      (True, {"used": int, "limit": int, "remaining": int}) if allowed.
      (False, {"detail": str, "resets_at": str}) if limit reached (HTTP 429).
    """
    limits = get_plan_limits_for_workspace(workspace)
    today_utc = timezone.now().date()

    from qa.models import AskRequest

    questions_used_today = AskRequest.objects.filter(
        user=user,
        workspace=workspace,
        created_at__date=today_utc,
        status__in=['pending', 'answered', 'unsupported'],
    ).count()

    start_of_month = today_utc.replace(day=1)
    tokens_this_month = UsageRecord.objects.filter(
        user=user,
        workspace=workspace,
        period_day__gte=start_of_month,
    ).aggregate(total=Sum('tokens_used'))['total'] or 0

    daily_limit = limits.daily_questions

    if questions_used_today >= daily_limit:
        return False, {
            "detail": "Daily question limit reached.",
            "resets_at": get_next_utc_midnight(),
            "questions_today": questions_used_today,
            "daily_limit": daily_limit,
            "monthly_tokens_used": tokens_this_month,
            "monthly_tokens_limit": limits.monthly_tokens,
        }

    if tokens_this_month >= limits.monthly_tokens:
        return False, {
            "detail": "Monthly token limit reached.",
            "resets_at": get_next_utc_month_start(),
            "questions_today": questions_used_today,
            "daily_limit": daily_limit,
            "monthly_tokens_used": tokens_this_month,
            "monthly_tokens_limit": limits.monthly_tokens,
        }

    return True, {
        "questions_today": questions_used_today,
        "daily_limit": daily_limit,
        "questions_remaining": daily_limit - questions_used_today,
        "monthly_tokens_used": tokens_this_month,
        "monthly_tokens_limit": limits.monthly_tokens,
    }


def check_daily_question_quota(user, workspace) -> Tuple[bool, Dict[str, Any]]:
    """Backward-compatible alias for callers and older tests."""
    return check_question_quotas(user, workspace)


def get_next_utc_month_start() -> str:
    now_utc = timezone.now()
    if now_utc.month == 12:
        next_month = now_utc.replace(year=now_utc.year + 1, month=1, day=1)
    else:
        next_month = now_utc.replace(month=now_utc.month + 1, day=1)
    return next_month.replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace('+00:00', 'Z')


def calculate_estimated_cost(tokens_used: int, kind: str = 'question') -> Decimal:
    """
    Calculates estimated cost based on standard model pricing.
    Baseline: $0.150 per 1M input tokens, $0.600 per 1M output tokens (approx $0.00000035/token average).
    """
    cost_per_token = Decimal('0.00000035')
    return Decimal(tokens_used) * cost_per_token


def record_usage(
    user,
    workspace,
    request_obj,
    tokens_used: int,
    kind: str = 'question'
) -> UsageRecord:
    """
    Persists an immutable UsageRecord linked 1-to-1 with an AskRequest.
    Guarantees no double charging on retries.
    """
    cost = calculate_estimated_cost(tokens_used, kind)
    today_utc = timezone.now().date()

    usage_record, _ = UsageRecord.objects.get_or_create(
        request=request_obj,
        defaults={
            'user': user,
            'workspace': workspace,
            'kind': kind,
            'tokens_used': tokens_used,
            'estimated_cost': cost,
            'period_day': today_utc,
        },
    )
    return usage_record


def get_user_workspace_usage_summary(user, workspace) -> Dict[str, Any]:
    """Compiles a complete usage and limits summary for the user in this workspace."""
    limits = get_plan_limits_for_workspace(workspace)
    today_utc = timezone.now().date()
    start_of_month = today_utc.replace(day=1)

    from qa.models import AskRequest

    questions_today = AskRequest.objects.filter(
        user=user,
        workspace=workspace,
        created_at__date=today_utc,
        status__in=['pending', 'answered', 'unsupported'],
    ).count()

    # Month's tokens
    tokens_this_month = UsageRecord.objects.filter(
        user=user,
        workspace=workspace,
        period_day__gte=start_of_month
    ).aggregate(total=Sum('tokens_used'))['total'] or 0
    estimated_cost = UsageRecord.objects.filter(
        user=user,
        workspace=workspace,
        period_day__gte=start_of_month,
    ).aggregate(total=Sum('estimated_cost'))['total'] or Decimal('0')

    return {
        "plan": workspace.plan,
        "daily_questions_used": questions_today,
        "daily_questions_limit": limits.daily_questions,
        "daily_questions_remaining": max(0, limits.daily_questions - questions_today),
        "monthly_tokens_used": tokens_this_month,
        "monthly_tokens_limit": limits.monthly_tokens,
        "monthly_tokens_remaining": max(0, limits.monthly_tokens - tokens_this_month),
        "estimated_cost_usd": estimated_cost,
        "max_documents_limit": limits.max_documents,
        "max_file_mb_limit": limits.max_file_mb,
        "resets_at": get_next_utc_midnight(),
    }
