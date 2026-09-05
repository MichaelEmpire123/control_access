from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from pilot.views import (
    # Users
    UserListView, UserCreateView, UserUpdateView, UserMeView, GetUserID,
    # Contractors
    ContractorListView, ContractorCreateView, ContractorDetailView,
    ContractorUpdateView, ContractorDeleteView,
    ContractorComplianceView, ContractorRecheckView,
    # Documents
    DocumentListView, DocumentCreateView, DocumentDetailView,
    DocumentUpdateView, DocumentDeleteView, DocumentByContractorView,
    # Employees
    EmployeeListView, EmployeeCreateView, EmployeeDetailView,
    EmployeeUpdateView, EmployeeDeleteView, EmployeeByContractorView,
    # Passes
    PassListView, PassCreateView, PassDetailView, PassUpdateView,
    PassDeleteView, PassActivateView, PassDeactivateView,
    PassCheckView, PassByEmployeeView,
    # Blacklist
    BlacklistListView, BlacklistAddView, BlacklistRemoveView, BlacklistCheckView,
)



urlpatterns = [
    # ============ AUTH ============
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path("drf-auth/", include('rest_framework.urls')),

    # ============ USERS ============
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/', GetUserID.as_view(), name='user_detail'),
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user_update'),
    path('users/me/', UserMeView.as_view(), name='user_me'),

    # ============ CONTRACTORS ============
    path('contractors/', ContractorListView.as_view(), name='contractor_list'),
    path('contractors/create/', ContractorCreateView.as_view(), name='contractor_create'),
    path('contractors/<int:pk>/', ContractorDetailView.as_view(), name='contractor_detail'),
    path('contractors/<int:pk>/update/', ContractorUpdateView.as_view(), name='contractor_update'),
    path('contractors/<int:pk>/delete/', ContractorDeleteView.as_view(), name='contractor_delete'),
    path('contractors/<int:pk>/compliance/', ContractorComplianceView.as_view(), name='contractor_compliance'),
    path('contractors/<int:pk>/recheck/', ContractorRecheckView.as_view(), name='contractor_recheck'),

    # ============ DOCUMENTS ============
    path('documents/', DocumentListView.as_view(), name='document_list'),
    path('documents/create/', DocumentCreateView.as_view(), name='document_create'),
    path('documents/<int:pk>/', DocumentDetailView.as_view(), name='document_detail'),
    path('documents/<int:pk>/update/', DocumentUpdateView.as_view(), name='document_update'),
    path('documents/<int:pk>/delete/', DocumentDeleteView.as_view(), name='document_delete'),
    path('documents/by-contractor/<int:contractor_id>/', DocumentByContractorView.as_view(),
         name='document_by_contractor'),

    # ============ EMPLOYEES ============
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employees/create/', EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/', EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('employees/<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee_delete'),
    path('employees/by-contractor/<int:contractor_id>/', EmployeeByContractorView.as_view(),
         name='employee_by_contractor'),

    # ============ ACCESS PASSES ============
    path('passes/', PassListView.as_view(), name='pass_list'),
    path('passes/create/', PassCreateView.as_view(), name='pass_create'),
    path('passes/<int:pk>/', PassDetailView.as_view(), name='pass_detail'),
    path('passes/<int:pk>/update/', PassUpdateView.as_view(), name='pass_update'),
    path('passes/<int:pk>/delete/', PassDeleteView.as_view(), name='pass_delete'),
    path('passes/<int:pk>/activate/', PassActivateView.as_view(), name='pass_activate'),
    path('passes/<int:pk>/deactivate/', PassDeactivateView.as_view(), name='pass_deactivate'),
    path('passes/check/', PassCheckView.as_view(), name='pass_check'),
    path('passes/by-employee/<int:employee_id>/', PassByEmployeeView.as_view(), name='pass_by_employee'),

    # ============ BLACKLIST ============
    path('blacklist/', BlacklistListView.as_view(), name='blacklist_list'),
    path('blacklist/add/', BlacklistAddView.as_view(), name='blacklist_add'),
    path('blacklist/<int:pk>/remove/', BlacklistRemoveView.as_view(), name='blacklist_remove'),
    path('blacklist/check/', BlacklistCheckView.as_view(), name='blacklist_check'),

    # ============ SCHEMA & DOCS ============
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]