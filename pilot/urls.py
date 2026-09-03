from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from pilot.views import UserListView, UserCreateView, UserUpdateView, ContractorListView, ContractorCreateView, \
    ContractorDeleteView, ContractorDetailView, ContractorUpdateView, ContractorComplianceView, ContractorRecheckView, \
    DocumentListView, DocumentCreateView, DocumentDetailView, DocumentUpdateView, DocumentDeleteView, \
    DocumentByContractorView, EmployeeListView, EmployeeCreateView, EmployeeDetailView, EmployeeUpdateView, \
    EmployeeDeleteView, EmployeeByContractorView, PassListView, PassCreateView, PassDetailView, PassUpdateView, \
    PassDeleteView, PassActivateView, PassDeactivateView, PassCheckView, PassByEmployeeView, BlacklistListView, \
    BlacklistAddView, BlacklistRemoveView, BlacklistCheckView, UserMeView

urlpatterns = [
    path('userlist/', UserListView.as_view(), name='user_list'),
    path('user_create/', UserCreateView.as_view(), name='user_create'),
    path('user_update/<int:pk>/', UserUpdateView.as_view(), name='user_update'),
    path('user/me', UserMeView.as_view(), name='user_me'),

    # ============ CONTRACTORS ============
    path('contractors/get_contractors/', ContractorListView.as_view(), name='contractor_list'),
    path('contractors/create_contractor/', ContractorCreateView.as_view(), name='contractor_create'),
    path('contractors/get_contractor/<int:pk>/', ContractorDetailView.as_view(), name='contractor_detail'),
    path('contractors/update_contractor/<int:pk>/', ContractorUpdateView.as_view(), name='contractor_update'),
    path('contractors/delete_contractor/<int:pk>/', ContractorDeleteView.as_view(), name='contractor_delete'),
    path('contractors/check_compliance/<int:pk>/', ContractorComplianceView.as_view(),
         name='contractor_compliance'),
    path('contractors/recheck_accreditation/<int:pk>/', ContractorRecheckView.as_view(),
         name='contractor_recheck'),

    # ============ DOCUMENTS ============
    path('documents/get_documents/', DocumentListView.as_view(), name='document_list'),
    path('documents/create_document/', DocumentCreateView.as_view(), name='document_create'),
    path('documents/get_document/<int:pk>/', DocumentDetailView.as_view(), name='document_detail'),
    path('documents/update_document/<int:pk>/', DocumentUpdateView.as_view(), name='document_update'),
    path('documents/delete_document/<int:pk>/', DocumentDeleteView.as_view(), name='document_delete'),
    path('documents/get_by_contractor/<int:contractor_id>/', DocumentByContractorView.as_view(),
         name='document_by_contractor'),

    # ============ EMPLOYEES ============
    path('employees/get_employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employees/create_employee/', EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/get_employee/<int:pk>/', EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/update_employee/<int:pk>/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('employees/delete_employee/<int:pk>/', EmployeeDeleteView.as_view(), name='employee_delete'),
    path('employees/get_by_contractor/<int:contractor_id>/', EmployeeByContractorView.as_view(),
         name='employee_by_contractor'),

    # ============ ACCESS PASSES ============
    path('passes/get_passes/', PassListView.as_view(), name='pass_list'),
    path('passes/create_pass/', PassCreateView.as_view(), name='pass_create'),
    path('passes/get_pass/<int:pk>/', PassDetailView.as_view(), name='pass_detail'),
    path('passes/update_pass/<int:pk>/', PassUpdateView.as_view(), name='pass_update'),
    path('passes/delete_pass/<int:pk>/', PassDeleteView.as_view(), name='pass_delete'),
    path('passes/activate_pass/<int:pk>/', PassActivateView.as_view(), name='pass_activate'),
    path('passes/deactivate_pass/<int:pk>/', PassDeactivateView.as_view(), name='pass_deactivate'),
    path('passes/check_pass/', PassCheckView.as_view(), name='pass_check'),
    path('passes/get_by_employee/<int:employee_id>/', PassByEmployeeView.as_view(), name='pass_by_employee'),

    # ============ BLACKLIST ============
    path('blacklist/get_blacklist/', BlacklistListView.as_view(), name='blacklist_list'),
    path('blacklist/add_to_blacklist/', BlacklistAddView.as_view(), name='blacklist_add'),
    path('blacklist/remove_from_blacklist/<int:pk>/', BlacklistRemoveView.as_view(), name='blacklist_remove'),
    path('blacklist/check_blacklist/', BlacklistCheckView.as_view(), name='blacklist_check'),

    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path("drf-auth/", include('rest_framework.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
