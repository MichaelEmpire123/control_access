from typing import Any

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from pilot.models import User, Contractor, ComplianceDocument, ContractorEmployee, AccessPass, Blacklist
from .permissions import (
    CanManageContractors, IsAdmin, CanManageDocuments, CanManageEmployees,
    CanManagePasses, IsAdminOrManagerOrSecurity, IsAdminOrSecurity,
    CanManageBlacklist, IsAdminOrManager
)
from .serializers.access_pass_serializers import AccessPassSerializer
from .serializers.blacklist_serializers import BlacklistSerializer
from .serializers.contractor_serializers import ContractorSerializer, EmployeeSerializer
from .serializers.document_serializers import DocumentSerializer
from .serializers.user_serializers import UserSerializer
from .services.access_pass_service import AccessPassService
from .services.blacklist_service import BlacklistService
from .services.contractor_service import ContractorService, EmployeeService
from .services.document_service import DocumentService
from .utils import ComplianceError, BlacklistError
from .mixins import (
    ListViewMixin, DetailViewMixin, BaseCreateView,
    BaseDeleteView, BaseActionView
)


# ============ USERS ============

@extend_schema(summary='Вывод всех пользователей системы')
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]


@extend_schema(summary='Вывод конкретного пользователя')
class GetUserID(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]


@extend_schema(summary='Создать пользователя')
class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]


@extend_schema(summary='Изменить данные пользователя')
class UserUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]


@extend_schema(summary='Проверка текущего пользователя')
class UserMeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ============ CONTRACTORS ============

@extend_schema(summary='Список подрядчиков')
class ContractorListView(ListViewMixin, generics.ListAPIView):
    queryset = Contractor.objects.all()
    serializer_class = ContractorSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageContractors]
    filterset_fields = ['status_accreditation']
    search_fields = ['name', 'inn']
    ordering_fields = ['name']


@extend_schema(summary='Создать подрядчика')
class ContractorCreateView(generics.CreateAPIView):
    serializer_class = ContractorSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageContractors]

    def perform_create(self, serializer):
        return ContractorService.create(serializer.validated_data)


@extend_schema(summary='Просмотр данных конкретного подрядчика')
class ContractorDetailView(DetailViewMixin, generics.RetrieveAPIView):
    queryset = Contractor.objects.all()
    serializer_class = ContractorSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageContractors]


@extend_schema(summary='Изменить данные подрядчика')
class ContractorUpdateView(generics.UpdateAPIView):
    queryset = Contractor.objects.all()
    serializer_class = ContractorSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageContractors]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        contractor = ContractorService.update(instance.id, serializer.validated_data)
        return Response(ContractorSerializer(contractor).data)


@extend_schema(summary='Удалить подрядчика')
class ContractorDeleteView(BaseDeleteView):
    queryset = Contractor.objects.all()
    serializer_class = ContractorSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin, CanManageContractors]

    def get_success_message(self):
        return 'Подрядчик успешно удален'


@extend_schema(summary='Проверка аккредитованности подрядчика')
class ContractorComplianceView(BaseActionView):
    permission_classes = [permissions.IsAuthenticated, CanManageContractors]
    serializer_class = ContractorSerializer

    def get(self, request, pk):
        try:
            ContractorService.check_compliance(pk)
            return Response({
                'status': '200',
                'message': 'Все документы в порядке, компания аккредитована'
            })
        except ComplianceError as e:
            return Response(e.detail, status=status.HTTP_403_FORBIDDEN)


@extend_schema(summary='Перепроверка аккредитации подрядчика')
class ContractorRecheckView(BaseActionView):
    permission_classes = [permissions.IsAuthenticated, CanManageContractors]
    serializer_class = ContractorSerializer

    def post(self, request, pk):
        contractor = ContractorService.recheck_accreditation(pk)
        if contractor and contractor.status_accreditation == 'Accreditate':
            return Response({
                'status': '200',
                'message': 'Компания аккредитована',
                'accreditation': 'Accreditate'
            })
        else:
            return Response({
                'status': '403',
                'message': 'Компания не аккредитована',
                'accreditation': 'Noaccreditate'
            })


# ============ DOCUMENTS ============

@extend_schema(summary='Список документов')
class DocumentListView(ListViewMixin, generics.ListAPIView):
    queryset = ComplianceDocument.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    filterset_fields = ['type', 'id_contractor']


@extend_schema(summary='Создать документ')
class DocumentCreateView(BaseCreateView):
    queryset = ComplianceDocument.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]

    def perform_create(self, serializer):
        return DocumentService.create_document(serializer.validated_data)


@extend_schema(summary='Просмотр документа')
class DocumentDetailView(DetailViewMixin, generics.RetrieveAPIView):
    queryset = ComplianceDocument.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]


@extend_schema(summary='Обновить документ')
class DocumentUpdateView(generics.UpdateAPIView):
    queryset = ComplianceDocument.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]


@extend_schema(summary='Удалить документ')
class DocumentDeleteView(BaseDeleteView):
    queryset = ComplianceDocument.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]

    def destroy(self, request, *args, **kwargs):
        doc_id = self.kwargs['pk']
        DocumentService.delete_document(doc_id)
        return Response(
            {'message': 'Документ успешно удален'},
            status=status.HTTP_200_OK
        )


@extend_schema(summary='Документы по подрядчику')
class DocumentByContractorView(generics.ListAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]

    def get_queryset(self):
        contractor_id = self.kwargs['id_contractor']
        user = self.request.user

        if user.role not in ['Admin', 'Manager', 'Security']:
            if user.role == 'Contractor' and user.contractor:
                if user.contractor.id != contractor_id:
                    return ComplianceDocument.objects.none()
            else:
                return ComplianceDocument.objects.none()

        return ComplianceDocument.objects.filter(id_contractor_id=contractor_id)


# ============ EMPLOYEES ============

@extend_schema(summary='Список сотрудников')
class EmployeeListView(ListViewMixin, generics.ListAPIView):
    queryset = ContractorEmployee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageEmployees]
    search_fields = ['last_name', 'first_name', 'passport']


@extend_schema(summary='Создать сотрудника (Добавляет но выводит ошибку 500) исправлю')
class EmployeeCreateView(BaseCreateView):
    queryset = ContractorEmployee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageEmployees]

    def perform_create(self, serializer):
        return EmployeeService.create_employee_with_check(serializer.validated_data)


@extend_schema(summary='Просмотр сотрудника')
class EmployeeDetailView(DetailViewMixin, generics.RetrieveAPIView):
    queryset = ContractorEmployee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageEmployees]


@extend_schema(summary='Обновить сотрудника')
class EmployeeUpdateView(generics.UpdateAPIView):
    queryset = ContractorEmployee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageEmployees]


@extend_schema(summary='Удалить сотрудника')
class EmployeeDeleteView(BaseDeleteView):
    queryset = ContractorEmployee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageEmployees]

    def get_success_message(self):
        return 'Сотрудник успешно удален'


@extend_schema(summary='Сотрудники по подрядчику')
class EmployeeByContractorView(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageEmployees]

    def get_queryset(self):
        contractor_id = self.kwargs['contractor_id']
        user = self.request.user

        if user.role not in ['Admin', 'Manager', 'Security']:
            if user.role == 'Contractor' and user.contractor:
                if user.contractor.id != contractor_id:
                    return ContractorEmployee.objects.none()
            else:
                return ContractorEmployee.objects.none()

        return ContractorEmployee.objects.filter(id_contractor_id=contractor_id)


# ============ ACCESS PASSES ============

@extend_schema(summary='Список пропусков')
class PassListView(ListViewMixin, generics.ListAPIView):
    queryset = AccessPass.objects.all()
    serializer_class = AccessPassSerializer
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]
    filterset_fields = ['status', 'type']


@extend_schema(summary='Создать пропуск')
class PassCreateView(BaseCreateView):
    queryset = AccessPass.objects.all()
    serializer_class = AccessPassSerializer
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]

    def perform_create(self, serializer):
        return AccessPassService.create_pass(serializer.validated_data)


@extend_schema(summary='Просмотр пропуска')
class PassDetailView(DetailViewMixin, generics.RetrieveAPIView):
    queryset = AccessPass.objects.all()
    serializer_class = AccessPassSerializer
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]


@extend_schema(summary='Обновить пропуск')
class PassUpdateView(generics.UpdateAPIView):
    queryset = AccessPass.objects.all()
    serializer_class = AccessPassSerializer
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]


@extend_schema(summary='Удалить пропуск')
class PassDeleteView(BaseDeleteView):
    queryset = AccessPass.objects.all()
    serializer_class = AccessPassSerializer
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]

    def get_success_message(self):
        return 'Пропуск успешно удален'


@extend_schema(summary='Активировать пропуск')
class PassActivateView(BaseActionView):
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]
    serializer_class = AccessPassSerializer

    def post(self, request, pk):
        try:
            pass_instance = AccessPass.objects.get(id=pk)
            employee = pass_instance.id_employee
            ContractorService.check_compliance(employee.id_contractor_id)

            updated = AccessPassService.activate_pass(pk)
            if updated:
                return Response({
                    'status': 'success',
                    'message': 'Пропуск активирован'
                })
        except (ComplianceError, BlacklistError) as e:
            return Response(e.detail, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(summary='Деактивировать пропуск')
class PassDeactivateView(BaseActionView):
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]
    serializer_class = AccessPassSerializer

    def post(self, request, pk):
        updated = AccessPassService.deactivate_pass(pk)
        if updated:
            return Response({
                'status': 'success',
                'message': 'Пропуск деактивирован'
            })
        return Response(
            {'error': 'Пропуск не найден'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(summary='Проверить пропуск')
class PassCheckView(BaseActionView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrSecurity]
    serializer_class = AccessPassSerializer

    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response(
                {'error': 'employee_id обязательный параметр'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = AccessPassService.check_pass_status(employee_id)
        return Response(result)


@extend_schema(summary='Пропуска по сотруднику')
class PassByEmployeeView(generics.ListAPIView):
    serializer_class = AccessPassSerializer
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]

    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        user = self.request.user

        if user.role not in ['Admin', 'Manager', 'Security']:
            if user.role == 'Contractor' and user.contractor:
                employee = ContractorEmployee.objects.filter(id=employee_id).first()
                if employee and employee.id_contractor_id != user.contractor.id:
                    return AccessPass.objects.none()
            else:
                return AccessPass.objects.none()

        return AccessPass.objects.filter(id_employee_id=employee_id)


# ============ BLACKLIST ============

@extend_schema(summary='Список черного списка')
class BlacklistListView(generics.ListAPIView):
    serializer_class = BlacklistSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageBlacklist]
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    search_fields = ['reason', 'entity_id']
    queryset = Blacklist.objects.all()


@extend_schema(summary='Добавить в черный список')
class BlacklistAddView(BaseCreateView):
    serializer_class = BlacklistSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageBlacklist]

    def perform_create(self, serializer):
        entity_type = self.request.data.get('entity_type')
        entity_id = self.request.data.get('entity_id')
        reason = self.request.data.get('reason')

        if not all([entity_type, entity_id, reason]):
            raise ValueError("Необходимы поля: entity_type, entity_id, reason")

        BlacklistService.add_to_blacklist(
            entity_type=entity_type,
            entity_id=entity_id,
            reason=reason,
            added_by=self.request.user
        )


@extend_schema(summary='Удалить из черного списка')
class BlacklistRemoveView(BaseDeleteView):
    queryset = Blacklist.objects.all()
    serializer_class = BlacklistSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageBlacklist]

    def get_success_message(self):
        return 'Запись удалена из черного списка'


@extend_schema(summary='Проверить в черном списке (НЕРАБОТАЕТ')
class BlacklistCheckView(BaseActionView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSecurity]
    serializer_class = BlacklistSerializer

    def get(self, request):
        entity_type = request.query_params.get('entity_type')
        entity_id = request.query_params.get('entity_id')

        if not all([entity_type, entity_id]):
            return Response(
                {'error': 'Необходимы параметры: entity_type, entity_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_blacklisted = BlacklistService.is_blacklisted(entity_type, entity_id)

        if is_blacklisted:
            entry = Blacklist.objects.filter(
                entity_type=entity_type,
                entity_id=str(entity_id)
            ).first()

            return Response({
                'is_blacklisted': True,
                'reason': entry.reason if entry else None,
                'date_added': entry.date if entry else None
            })
        else:
            return Response({
                'is_blacklisted': False
            })