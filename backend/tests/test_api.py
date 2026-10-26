import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from workspaces.models import Workspace, WorkspaceMember
from usage.models import PlanLimit
from usage.models import UsageRecord
from qa.models import AskRequest
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from documents.models import Document, DocumentChunk
from ai.mock_provider import MockAIProvider

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    user = User.objects.create_user(
        email="testuser@example.com",
        password="TestPassword123!",
        full_name="Test User"
    )
    return user


@pytest.fixture
def other_user(db):
    user = User.objects.create_user(
        email="otheruser@example.com",
        password="OtherPassword123!",
        full_name="Other User"
    )
    return user


@pytest.fixture
def test_workspace(db, test_user):
    ws = Workspace.objects.create(name="Primary Workspace", owner=test_user, plan='free')
    WorkspaceMember.objects.create(workspace=ws, user=test_user, role='owner')
    PlanLimit.objects.get_or_create(
        plan='free',
        defaults={'daily_questions': 20, 'monthly_tokens': 100000, 'max_documents': 10, 'max_file_mb': 10}
    )
    return ws


@pytest.fixture
def other_workspace(db, other_user):
    ws = Workspace.objects.create(name="Isolated Workspace", owner=other_user, plan='free')
    WorkspaceMember.objects.create(workspace=ws, user=other_user, role='owner')
    return ws


@pytest.mark.django_db
def test_user_registration_api(api_client):
    """AC1: User registration via public API endpoint."""
    payload = {
        "email": "newbie@example.com",
        "full_name": "Newbie User",
        "password": "SecurePassword123!",
        "password_confirm": "SecurePassword123!"
    }
    response = api_client.post("/api/v1/auth/register/", payload, format='json')
    assert response.status_code == 201
    assert response.data['user']['email'] == "newbie@example.com"


@pytest.mark.django_db
def test_user_login_jwt_api(api_client, test_user):
    """AC1: User login returning JWT access and refresh tokens with user payload."""
    payload = {
        "email": "testuser@example.com",
        "password": "TestPassword123!"
    }
    response = api_client.post("/api/v1/auth/login/", payload, format='json')
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data['user']['email'] == "testuser@example.com"


@pytest.mark.django_db
def test_workspace_creation_assigns_owner(api_client, test_user):
    """AC1: Creating workspace automatically assigns creator as owner member."""
    api_client.force_authenticate(user=test_user)
    payload = {"name": "Engineering Team", "plan": "free"}
    response = api_client.post("/api/v1/workspaces/", payload, format='json')
    assert response.status_code == 201
    ws_id = response.data['id']

    # Verify database membership
    member = WorkspaceMember.objects.filter(workspace_id=ws_id, user=test_user).first()
    assert member is not None
    assert member.role == 'owner'


@pytest.mark.django_db
def test_tenant_isolation_cannot_access_other_workspace(api_client, test_user, other_workspace):
    """AC10: User in Workspace A cannot list or access documents of Workspace B (HTTP 404)."""
    api_client.force_authenticate(user=test_user)
    # Attempt to access other_workspace's document endpoint
    response = api_client.get(f"/api/v1/workspaces/{other_workspace.id}/documents/")
    assert response.status_code in [403, 404]


@pytest.mark.django_db
def test_unsupported_question_guard_no_ai_call(api_client, test_user, test_workspace):
    """AC5: When no matching documents exist, system replies 'not found' and marks unsupported."""
    api_client.force_authenticate(user=test_user)
    headers = {'HTTP_IDEMPOTENCY_KEY': '11111111-2222-3333-4444-555555555555'}
    payload = {"question": "What is the capital of Mars?"}

    response = api_client.post(
        f"/api/v1/workspaces/{test_workspace.id}/ask/",
        payload,
        format='json',
        **headers
    )
    assert response.status_code == 200
    assert response.data['status'] == "unsupported"
    assert "could not find this in your documents" in response.data['answer'].lower()
    assert response.data['sources'] == []


@pytest.mark.django_db
def test_idempotency_key_prevents_duplicate_charge(api_client, test_user, test_workspace):
    """AC9: Submitting the same Idempotency-Key twice returns the saved result without double charge."""
    api_client.force_authenticate(user=test_user)
    headers = {'HTTP_IDEMPOTENCY_KEY': 'retry-key-uuid-1234'}
    payload = {"question": "What are the rules?"}

    # First request
    resp1 = api_client.post(f"/api/v1/workspaces/{test_workspace.id}/ask/", payload, format='json', **headers)
    assert resp1.status_code == 200
    req_id = resp1.data['request_id']

    # Duplicate request with same key
    resp2 = api_client.post(f"/api/v1/workspaces/{test_workspace.id}/ask/", payload, format='json', **headers)
    assert resp2.status_code == 200
    assert resp2.data['request_id'] == req_id
    assert resp2.data.get('cached') is True


@pytest.mark.django_db
def test_monthly_token_limit_returns_429(api_client, test_user, test_workspace):
    """Monthly token ceilings are enforced before retrieval/provider work."""
    limits = PlanLimit.objects.get(plan='free')
    limits.monthly_tokens = 100
    limits.save(update_fields=['monthly_tokens'])
    previous = AskRequest.objects.create(
        workspace=test_workspace,
        user=test_user,
        question='Previous question',
        answer='Previous answer [1].',
        status='answered',
        idempotency_key='previous-request',
    )
    UsageRecord.objects.create(
        user=test_user,
        workspace=test_workspace,
        request=previous,
        kind='question',
        tokens_used=100,
        estimated_cost=Decimal('0.000035'),
    )
    api_client.force_authenticate(user=test_user)
    response = api_client.post(
        f"/api/v1/workspaces/{test_workspace.id}/ask/",
        {"question": "What is the policy?"},
        format='json',
        HTTP_IDEMPOTENCY_KEY='monthly-limit-test',
    )
    assert response.status_code == 429
    assert 'Monthly token limit' in response.data['detail']


@pytest.mark.django_db
def test_usage_response_contract_matches_frontend(api_client, test_user, test_workspace):
    api_client.force_authenticate(user=test_user)
    response = api_client.get(f"/api/v1/workspaces/{test_workspace.id}/usage/")
    assert response.status_code == 200
    for field in (
        'daily_questions_used',
        'daily_questions_limit',
        'monthly_tokens_used',
        'monthly_tokens_limit',
        'estimated_cost_usd',
    ):
        assert field in response.data


@pytest.mark.django_db
def test_workspace_document_limit_is_enforced(api_client, test_user, test_workspace):
    limits = PlanLimit.objects.get(plan='free')
    limits.max_documents = 0
    limits.save(update_fields=['max_documents'])
    api_client.force_authenticate(user=test_user)
    upload = SimpleUploadedFile('policy.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf')
    response = api_client.post(
        f"/api/v1/workspaces/{test_workspace.id}/documents/",
        {'file': upload},
        format='multipart',
    )
    assert response.status_code == 400
    assert 'document limit' in str(response.data).lower()


@pytest.mark.django_db
def test_grounded_question_returns_citation_from_workspace_document(api_client, test_user, test_workspace):
    """AC3/AC4: Mock-mode RAG answers from a ready workspace document with a citation."""
    document = Document.objects.create(
        workspace=test_workspace,
        uploaded_by=test_user,
        original_name='leave-policy.txt',
        storage_key='storage/test-uploads/leave-policy.txt',
        mime_type='text/plain',
        size_bytes=60,
        content_hash='a' * 64,
        status='ready',
        page_count=1,
    )
    content = 'Employees receive 10 paid sick leaves per calendar year.'
    DocumentChunk.objects.create(
        document=document,
        workspace=test_workspace,
        chunk_index=0,
        page_number=1,
        content=content,
        token_count=12,
        embedding=MockAIProvider().embed_text(content),
    )
    api_client.force_authenticate(user=test_user)
    response = api_client.post(
        f"/api/v1/workspaces/{test_workspace.id}/ask/",
        {"question": "How many sick leaves do employees get per year?"},
        format='json',
        HTTP_IDEMPOTENCY_KEY='grounded-answer-with-citation',
    )
    assert response.status_code == 200
    assert response.data['status'] == 'answered'
    assert '[1]' in response.data['answer']
    assert response.data['sources'][0]['document'] == 'leave-policy.txt'


@pytest.mark.django_db
def test_failed_request_can_retry_same_idempotency_key(api_client, test_user, test_workspace):
    failed = AskRequest.objects.create(
        workspace=test_workspace,
        user=test_user,
        question='What is the policy?',
        status='failed',
        failure_code='provider_error',
        idempotency_key='retry-provider-failure',
    )
    api_client.force_authenticate(user=test_user)
    response = api_client.post(
        f"/api/v1/workspaces/{test_workspace.id}/ask/",
        {"question": "What is the policy?"},
        format='json',
        HTTP_IDEMPOTENCY_KEY='retry-provider-failure',
    )
    assert response.status_code == 200
    failed.refresh_from_db()
    assert failed.status == 'unsupported'
    assert AskRequest.objects.filter(idempotency_key='retry-provider-failure').count() == 1
