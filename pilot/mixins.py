from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination

from pilot.models import ContractorEmployee
from pilot.utils import BlacklistError, ComplianceError


class ListViewMixin:
    """Миксин для списковых view с пагинацией и фильтрацией"""
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        user = self.request.user
        model = self.queryset.model

        # Admin, Manager, Security - видят все
        if user.role in ['Admin', 'Manager', 'Security']:
            return self.queryset

        # Contractor - видят только свое
        if user.role == 'Contractor' and user.contractor:
            return self._filter_by_contractor(user)

        return self.queryset.none()

    def _filter_by_contractor(self, user):
        """Фильтрация по подрядчику в зависимости от модели"""
        model = self.queryset.model
        model_name = model.__name__

        if model_name == 'Contractor':
            return self.queryset.filter(id=user.contractor.id)
        elif model_name == 'ComplianceDocument':
            return self.queryset.filter(id_contractor_id=user.contractor.id)
        elif model_name == 'ContractorEmployee':
            return self.queryset.filter(id_contractor_id=user.contractor.id)
        elif model_name == 'AccessPass':
            employee_ids = ContractorEmployee.objects.filter(
                id_contractor_id=user.contractor.id
            ).values_list('id', flat=True)
            return self.queryset.filter(id_employee_id__in=employee_ids)
        return self.queryset.none()


class DetailViewMixin:
    """Миксин для детальных view с проверкой доступа"""

    def get_queryset(self):
        user = self.request.user
        model = self.queryset.model

        if user.role in ['Admin', 'Manager', 'Security']:
            return self.queryset

        if user.role == 'Contractor' and user.contractor:
            return self._filter_by_contractor(user)

        return self.queryset.none()

    def _filter_by_contractor(self, user):
        """Фильтрация по подрядчику для детального просмотра"""
        model = self.queryset.model
        model_name = model.__name__

        if model_name == 'Contractor':
            return self.queryset.filter(id=user.contractor.id)
        elif model_name == 'ComplianceDocument':
            return self.queryset.filter(id_contractor_id=user.contractor.id)
        elif model_name == 'ContractorEmployee':
            return self.queryset.filter(id_contractor_id=user.contractor.id)
        elif model_name == 'AccessPass':
            employee_ids = ContractorEmployee.objects.filter(
                id_contractor_id=user.contractor.id
            ).values_list('id', flat=True)
            return self.queryset.filter(id_employee_id__in=employee_ids)
        return self.queryset.none()


class BaseCreateView(generics.CreateAPIView):
    """Базовый класс для создания объектов с обработкой ошибок"""

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


class BaseDeleteView(generics.DestroyAPIView):
    """Базовый класс для удаления с единым ответом"""

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': f'{self.get_success_message()}'},
            status=status.HTTP_200_OK
        )

    def get_success_message(self):
        """Переопределить для кастомного сообщения"""
        model_name = self.queryset.model._meta.verbose_name
        return f'{model_name} успешно удален'


class BaseActionView(generics.GenericAPIView):
    """Базовый класс для action-view (активация, деактивация и т.д.)"""

    def get_queryset(self):
        return self.queryset

    def handle_exception(self, exc):
        if isinstance(exc, (ComplianceError, BlacklistError)):
            return Response(exc.detail, status=status.HTTP_403_FORBIDDEN)
        return super().handle_exception(exc)