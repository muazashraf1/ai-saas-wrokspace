import time
import logging
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import AskRequest, RequestSource
from .serializers import (
    AskQuestionInputSerializer,
    AskResponseSerializer,
    AskRequestListSerializer,
    AskRequestDetailSerializer,
    RequestSourceSerializer,
)
from .retrieval import retrieve_relevant_chunks
from .prompt import assemble_qa_prompt, extract_and_validate_citations
from ai.factory import get_ai_provider
from workspaces.models import Workspace, WorkspaceMember
from workspaces.permissions import IsWorkspaceMember
from usage.services import check_question_quotas, record_usage

logger = logging.getLogger(__name__)


def get_workspace_for_user(user, ws_id):
    """Ensures user is an active member of the workspace."""
    return get_object_or_404(
        Workspace.objects.filter(memberships__user=user),
        id=ws_id
    )


from drf_spectacular.utils import extend_schema


class AskQuestionView(APIView):
    """
    POST /api/v1/workspaces/{ws}/ask/
    Core RAG Q&A Endpoint.
    Enforces 'Idempotency-Key' header and daily question limits (Section 8.2 & 7.8).
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]

    @extend_schema(request=AskQuestionInputSerializer, responses={200: AskResponseSerializer})
    def post(self, request, ws):
        workspace = get_workspace_for_user(request.user, ws)

        # 1. Enforce Idempotency-Key header
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response(
                {"detail": "Idempotency-Key header is required for question requests."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if len(idempotency_key) > 64:
            return Response(
                {"detail": "Idempotency-Key must be 64 characters or fewer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Validate input question
        serializer = AskQuestionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data['question']

        # 3. Atomically reserve the request. Locking the user serializes quota
        # checks and idempotency keys for concurrent requests from that user.
        User = get_user_model()
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            ask_request = AskRequest.objects.filter(
                user=request.user,
                idempotency_key=idempotency_key,
            ).first()

            if ask_request and ask_request.question.strip() != question.strip():
                return Response(
                    {"detail": "Conflict: This Idempotency-Key was already used with a different question."},
                    status=status.HTTP_409_CONFLICT,
                )

            if ask_request and ask_request.status in ('answered', 'unsupported'):
                sources_data = RequestSourceSerializer(ask_request.sources.all(), many=True).data
                return Response({
                    "request_id": ask_request.id,
                    "status": ask_request.status,
                    "answer": ask_request.answer,
                    "sources": sources_data,
                    "cached": True,
                })

            if ask_request and ask_request.status == 'pending':
                return Response({
                    "request_id": ask_request.id,
                    "status": "pending",
                    "detail": "This request is already being processed.",
                }, status=status.HTTP_202_ACCEPTED)

            quota_allowed, quota_data = check_question_quotas(request.user, workspace)
            if not quota_allowed:
                return Response({
                    "detail": quota_data['detail'],
                    "resets_at": quota_data['resets_at'],
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            if ask_request:
                # A provider failure may be retried with the same key without a
                # duplicate charge or a second history row.
                ask_request.status = 'pending'
                ask_request.answer = None
                ask_request.failure_code = None
                ask_request.prompt_tokens = 0
                ask_request.completion_tokens = 0
                ask_request.latency_ms = 0
                ask_request.sources.all().delete()
                ask_request.save()
            else:
                ask_request = AskRequest.objects.create(
                    workspace=workspace,
                    user=request.user,
                    question=question,
                    status='pending',
                    provider='pending',
                    idempotency_key=idempotency_key,
                )

        # 5. Tenant-Isolated Vector Retrieval
        try:
            retrieval_res = retrieve_relevant_chunks(
                workspace_id=workspace.id,
                query_text=question,
            )
        except Exception as exc:
            logger.error("Embedding/retrieval provider failure", exc_info=True)
            ask_request.status = 'failed'
            ask_request.failure_code = 'provider_error'
            ask_request.answer = None
            ask_request.save(update_fields=['status', 'failure_code', 'answer'])
            return Response({
                "detail": "The AI service is not available right now. Please try again.",
                "request_id": ask_request.id,
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 6. Unsupported Question Guard (Section 7.3 & 8.2)
        # If evidence is below similarity threshold, do NOT call AI. Reply directly.
        if not retrieval_res['is_supported']:
            ask_request.answer = "I could not find this in your documents."
            ask_request.status = 'unsupported'
            ask_request.failure_code = 'threshold_miss'
            ask_request.provider = 'system'
            ask_request.latency_ms = 0
            ask_request.save(update_fields=['answer', 'status', 'failure_code', 'provider', 'latency_ms'])
            return Response(
                {
                    "request_id": ask_request.id,
                    "status": "unsupported",
                    "answer": ask_request.answer,
                    "sources": [],
                },
                status=status.HTTP_200_OK
            )

        # 7. Prompt Assembly & Injection Defense
        system_prompt, user_content, included_chunks = assemble_qa_prompt(
            question=question,
            chunks=retrieval_res['chunks']
        )

        # 8. AI Provider Execution with Latency Measurement
        start_time = time.time()

        try:
            ai_provider = get_ai_provider()
            ai_res = ai_provider.generate_answer(
                system_prompt=system_prompt,
                context_chunks=included_chunks,
                question=question
            )
        except Exception as exc:
            logger.error(f"AI Provider failure for workspace {workspace.id}: {str(exc)}", exc_info=True)
            ask_request.status = 'failed'
            ask_request.failure_code = 'provider_error'
            ask_request.provider = getattr(locals().get('ai_provider'), 'provider_name', 'configuration')
            ask_request.model = getattr(locals().get('ai_provider'), 'model_name', '')
            ask_request.save(update_fields=['status', 'failure_code', 'provider', 'model'])
            # Failed requests do NOT count towards usage limits
            return Response(
                {
                    "detail": "The AI service is not available right now. Please try again.",
                    "request_id": ask_request.id,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        latency_ms = int((time.time() - start_time) * 1000)

        # 9. Citation Extraction & Verification
        sanitized_answer, cited_chunks = extract_and_validate_citations(
            answer_text=ai_res['answer'],
            included_chunks=included_chunks
        )

        if "could not find this in your documents" in sanitized_answer.lower():
            ask_request.answer = "I could not find this in your documents."
            ask_request.status = 'unsupported'
            ask_request.failure_code = 'model_unsupported'
            ask_request.provider = ai_res.get('provider', ai_provider.provider_name)
            ask_request.model = ai_res.get('model', ai_provider.model_name)
            ask_request.latency_ms = latency_ms
            ask_request.save()
            return Response({
                "request_id": ask_request.id,
                "status": "unsupported",
                "answer": ask_request.answer,
                "sources": [],
            })

        if not cited_chunks:
            ask_request.status = 'failed'
            ask_request.failure_code = 'invalid_citations'
            ask_request.provider = ai_res.get('provider', ai_provider.provider_name)
            ask_request.model = ai_res.get('model', ai_provider.model_name)
            ask_request.latency_ms = latency_ms
            ask_request.save()
            return Response({
                "detail": "The AI response could not be verified against the retrieved sources. Please retry.",
                "request_id": ask_request.id,
            }, status=status.HTTP_502_BAD_GATEWAY)

        # 10. Atomic Transaction: Persist AskRequest, Citations, and UsageRecord together
        with transaction.atomic():
            ask_request = AskRequest.objects.select_for_update().get(pk=ask_request.pk)
            ask_request.answer = sanitized_answer
            ask_request.status = 'answered'
            ask_request.failure_code = None
            ask_request.provider = ai_res.get('provider', ai_provider.provider_name)
            ask_request.model = ai_res.get('model', ai_provider.model_name)
            ask_request.prompt_tokens = ai_res.get('prompt_tokens', 0)
            ask_request.completion_tokens = ai_res.get('completion_tokens', 0)
            ask_request.latency_ms = latency_ms
            ask_request.save()

            source_objects = []
            for rank, chunk in enumerate(cited_chunks, start=1):
                source_objects.append(
                    RequestSource(
                        request=ask_request,
                        chunk_id=chunk.get('chunk_id'),
                        document_name=chunk.get('document_name', 'Unknown'),
                        page_number=chunk.get('page_number', 1),
                        similarity_score=chunk.get('similarity_score', 0.0),
                        rank=rank,
                    )
                )

            if source_objects:
                RequestSource.objects.bulk_create(source_objects)

            # Record usage atomically (Section 6.4 & 7.8)
            total_tokens = ask_request.prompt_tokens + ask_request.completion_tokens
            record_usage(
                user=request.user,
                workspace=workspace,
                request_obj=ask_request,
                tokens_used=total_tokens,
                kind='question'
            )

        sources_data = RequestSourceSerializer(ask_request.sources.all(), many=True).data

        # Success response structure matching Section 8.2
        return Response(
            {
                "request_id": ask_request.id,
                "status": "answered",
                "answer": ask_request.answer,
                "sources": sources_data,
                "usage": {
                    "questions_today": quota_data['questions_today'] + 1,
                    "daily_limit": quota_data['daily_limit']
                }
            },
            status=status.HTTP_200_OK
        )


class RequestHistoryListView(generics.ListAPIView):
    """
    GET /api/v1/workspaces/{ws}/requests/
    List request history.
    - Members: see their own requests.
    - Admin/Owner: see all requests in the workspace (Section 8.1).
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
    serializer_class = AskRequestListSerializer
    lookup_url_kwarg = 'ws'

    def get_queryset(self):
        workspace = get_workspace_for_user(self.request.user, self.kwargs.get('ws'))
        membership = WorkspaceMember.objects.filter(workspace=workspace, user=self.request.user).first()

        qs = AskRequest.objects.filter(workspace=workspace).select_related('user').prefetch_related('sources')

        # Role-based scoping: Admins see all, Members see only their own
        if membership and not membership.is_admin_or_owner:
            qs = qs.filter(user=self.request.user)

        return qs.order_by('-created_at')


class RequestHistoryDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/workspaces/{ws}/requests/{id}/
    Retrieve request detail including citations and token metrics.
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
    serializer_class = AskRequestDetailSerializer
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        workspace = get_workspace_for_user(self.request.user, self.kwargs.get('ws'))
        membership = WorkspaceMember.objects.filter(workspace=workspace, user=self.request.user).first()

        qs = AskRequest.objects.filter(workspace=workspace).select_related('user').prefetch_related('sources__chunk')
        if membership and not membership.is_admin_or_owner:
            qs = qs.filter(user=self.request.user)

        return qs
