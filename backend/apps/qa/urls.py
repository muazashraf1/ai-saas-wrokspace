from django.urls import path
from .views import (
    AskQuestionView,
    RequestHistoryListView,
    RequestHistoryDetailView,
)

urlpatterns = [
    # Ask a question
    path('ask/', AskQuestionView.as_view(), name='ask_question'),

    # Request history
    path('requests/', RequestHistoryListView.as_view(), name='request_history_list'),
    path('requests/<int:id>/', RequestHistoryDetailView.as_view(), name='request_history_detail'),
]
