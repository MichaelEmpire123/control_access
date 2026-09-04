from typing import Any

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from pilot.models import User, Contractor, ComplianceDocument, ContractorEmployee, AccessPass, Blacklist
from .permissions import CanManageContractors, IsAdmin, CanManageDocuments, CanManageEmployees, CanManagePasses, \
    IsAdminOrManagerOrSecurity, IsAdminOrSecurity, CanManageBlacklist, IsAdminOrManager
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

@extend_schema(summary='Вывод всех пользователей системы')
# Работа с User
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]

@extend_schema(summary='Вывод конкретного пользователя')
class GetUserID(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]

    def retrieve(self, request: Request, *args: Any, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

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

@extend_schema(summary='Проверка текущего пользлователя')
class UserMeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# Работа с Contractor

@extend_schema(summary='Список подрядчиков')
class ContractorListView(generics.ListAPIView):
    serializer_class = ContractorSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status_accreditation']
    search_fields = ['name', 'inn']
    ordering_fields = ['name']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['Admin', 'Manager', 'Security']:
            return Contractor.objects.all()
        if user.role == 'Contractor' and user.contractor:
            return Contractor.objects.filter(id=user.contractor.id)
        return Contractor.objects.none()

@extend_schema(summary='Создать подрядчика')
class ContractorCreateView(generics.CreateAPIView):
    serializer_class = ContractorSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageContractors]

    def perform_create(self, serializer):
        return ContractorService.create(serializer.validated_data)

@extend_schema(summary='Просмотр данных конкретного подрядчика по айди')
class ContractorDetailView(generics.RetrieveAPIView):
    serializer_class = ContractorSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Contractor.objects.all()

@extend_schema(summary='Измена данных подрядчика')
class ContractorUpdateView(generics.UpdateAPIView):
    serializer_class = ContractorSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageContractors]
    queryset = Contractor.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        contractor = ContractorService.update(instance.id, serializer.validated_data)
        return Response(ContractorSerializer(contractor).data)

@extend_schema(summary='Удалить подрядчика')
class ContractorDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = Contractor.objects.all()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        ContractorService.delete(instance.id)
        return Response(
            {'message': 'Подрядчик успешно удален'},
            status=status.HTTP_200_OK
        )

@extend_schema(summary='Проверка аккредитованности подрядчика')
class ContractorComplianceView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            ContractorService.check_compliance(pk)
            return Response({
                'status': '200',
                'message': 'Все документы в порядке, компания аккредитована'
            })
        except ComplianceError as e:
            return Response(e.detail, status=status.HTTP_403_FORBIDDEN)


class ContractorRecheckView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, CanManageContractors]

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


class DocumentListView(generics.ListAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type', 'id_contractor']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['Admin', 'Manager', 'Security']:
            return ComplianceDocument.objects.all()
        if user.role == 'Contractor' and user.contractor:
            return ComplianceDocument.objects.filter(id_contractor_id=user.contractor.id)
        return ComplianceDocument.objects.none()


class DocumentCreateView(generics.CreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]

    def perform_create(self, serializer):
        return DocumentService.create_document(serializer.validated_data)


class DocumentDetailView(generics.RetrieveAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ComplianceDocument.objects.all()


class DocumentUpdateView(generics.UpdateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    queryset = ComplianceDocument.objects.all()


class DocumentDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    queryset = ComplianceDocument.objects.all()

    def destroy(self, request, *args, **kwargs):
        doc_id = self.kwargs['pk']
        DocumentService.delete_document(doc_id)
        return Response(
            {'message': 'Документ успешно удален'},
            status=status.HTTP_200_OK
        )


class DocumentByContractorView(generics.ListAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        contractor_id = self.kwargs['id_contractor']
        user = self.request.user

        # Проверка прав: если не Admin/Manager/Security, то только свой подрядчик
        if user.role not in ['Admin', 'Manager', 'Security']:
            if user.role == 'Contractor' and user.contractor:
                if user.contractor.id != contractor_id:
                    return ComplianceDocument.objects.none()
            else:
                return ComplianceDocument.objects.none()

        return ComplianceDocument.objects.filter(contractor_id=user.contractor.id)


class EmployeeListView(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    search_fields = ['last_name', 'first_name', 'passport']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['Admin', 'Manager', 'Security']:
            return ContractorEmployee.objects.all()
        if user.role == 'Contractor' and user.contractor:
            return ContractorEmployee.objects.filter(contractor_id=user.contractor.id)
        return ContractorEmployee.objects.none()


class EmployeeCreateView(generics.CreateAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageEmployees]

    def perform_create(self, serializer):
        return EmployeeService.create_employee_with_check(serializer.validated_data)


class EmployeeDetailView(generics.RetrieveAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ContractorEmployee.objects.all()


class EmployeeUpdateView(generics.UpdateAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageEmployees]
    queryset = ContractorEmployee.objects.all()


class EmployeeDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, CanManageEmployees]
    queryset = ContractorEmployee.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        EmployeeService.delete(instance.id)
        return Response(
            {'message': 'Сотрудник успешно удален'},
            status=status.HTTP_200_OK
        )


class EmployeeByContractorView(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        contractor_id = self.kwargs['contractor_id']
        user = self.request.user

        if user.role not in ['Admin', 'Manager', 'Security']:
            if user.role == 'Contractor' and user.contractor:
                if user.contractor.id != contractor_id:
                    return ContractorEmployee.objects.none()
            else:
                return ContractorEmployee.objects.none()

        return ContractorEmployee.objects.filter(contractor_id=contractor_id)


class PassListView(generics.ListAPIView):
    serializer_class = AccessPassSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'type']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['Admin', 'Manager', 'Security']:
            return AccessPass.objects.all()
        if user.role == 'Contractor' and user.contractor:
            employee_ids = ContractorEmployee.objects.filter(
                contractor_id=user.contractor.id
            ).values_list('id', flat=True)
            return AccessPass.objects.filter(employee_id__in=employee_ids)
        return AccessPass.objects.none()


class PassCreateView(generics.CreateAPIView):
    serializer_class = AccessPassSerializer
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]

    def perform_create(self, serializer):
        return AccessPassService.create_pass(serializer.validated_data)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except (ComplianceError, BlacklistError) as e:
            return Response(e.detail, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PassDetailView(generics.RetrieveAPIView):
    serializer_class = AccessPassSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AccessPass.objects.all()


class PassUpdateView(generics.UpdateAPIView):
    serializer_class = AccessPassSerializer
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]
    queryset = AccessPass.objects.all()


class PassDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]
    queryset = AccessPass.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        AccessPassService.delete(instance.id)
        return Response(
            {'message': 'Пропуск успешно удален'},
            status=status.HTTP_200_OK
        )


class PassActivateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]

    def post(self, request, pk):
        try:
            pass_instance = AccessPass.objects.get(id=pk)
            employee = pass_instance.employee
            ContractorService.check_compliance(employee.contractor_id)

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


class PassDeactivateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, CanManagePasses]

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


class PassCheckView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrSecurity]

    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response(
                {'error': 'employee_id обязательный параметр'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = AccessPassService.check_pass_status(employee_id)
        return Response(result)


class PassByEmployeeView(generics.ListAPIView):
    serializer_class = AccessPassSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        user = self.request.user

        if user.role not in ['Admin', 'Manager', 'Security']:
            if user.role == 'Contractor' and user.contractor:
                employee = ContractorEmployee.objects.filter(id=employee_id).first()
                if employee and employee.contractor_id != user.contractor.id:
                    return AccessPass.objects.none()
            else:
                return AccessPass.objects.none()

        return AccessPass.objects.filter(employee_id=employee_id)


class BlacklistListView(generics.ListAPIView):
    serializer_class = BlacklistSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageBlacklist]
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    search_fields = ['reason', 'entity_id']
    queryset = Blacklist.objects.all()


class BlacklistAddView(generics.CreateAPIView):
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

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class BlacklistRemoveView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, CanManageBlacklist]
    queryset = Blacklist.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        BlacklistService.remove_from_blacklist(
            instance.entity_type,
            instance.entity_id
        )
        return Response(
            {'message': 'Запись удалена из черного списка'},
            status=status.HTTP_200_OK
        )


class BlacklistCheckView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSecurity]

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
                entity_id=entity_id
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
