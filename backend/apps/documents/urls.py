from django.urls import path
from .views import (
    DocumentListCreateView,
    DocumentDetailView,
    DocumentRetryView,
)

urlpatterns = [
    path('', DocumentListCreateView.as_view(), name='document_list_create'),
    path('<int:id>/', DocumentDetailView.as_view(), name='document_detail'),
    path('<int:id>/retry/', DocumentRetryView.as_view(), name='document_retry'),
]
