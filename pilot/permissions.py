from rest_framework.permissions import BasePermission

from pilot.models import ContractorEmployee


class IsAdmin(BasePermission):
    """Только администратор"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Admin'


class IsManager(BasePermission):
    """Только менеджер"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Manager'


class IsSecurity(BasePermission):
    """Только охрана"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Security'


class IsContractor(BasePermission):
    """Только подрядчик"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Contractor'


class IsAdminOrManager(BasePermission):
    """Администратор или менеджер"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Admin', 'Manager']


class IsAdminOrSecurity(BasePermission):
    """Администратор или охрана"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Admin', 'Security']


class IsAdminOrManagerOrSecurity(BasePermission):
    """Администратор, менеджер или охрана"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Admin', 'Manager', 'Security']


class CanViewAllUsers(BasePermission):
    """Может просматривать всех пользователей (Admin и Manager)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Admin', 'Manager']


class CanViewAllContractors(BasePermission):
    """Может просматривать всех подрядчиков (Admin, Manager, Security)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Admin', 'Manager', 'Security']


class CanManageBlacklist(BasePermission):
    """Может управлять черным списком (Admin и Security)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Admin', 'Security']


class CanManagePasses(BasePermission):
    """Может управлять пропусками (Admin и Manager)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Admin', 'Manager']


class CanManageContractors(BasePermission):
    """Может управлять подрядчиками (Admin и Manager)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Admin', 'Manager']


class CanManageEmployees(BasePermission):
    """Может управлять сотрудниками (Admin и Manager)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Admin', 'Manager']


class CanManageDocuments(BasePermission):
    """Может управлять документами (Admin и Manager)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Admin', 'Manager']


class CanViewOnlySelf(BasePermission):
    """Может видеть только себя (Contractor и Security)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Contractor', 'Security']

    def filter_queryset(self, request, queryset, view):
        # Фильтруем queryset, чтобы показывать только себя
        return queryset.filter(id=request.user.id)


class CanViewOwnContractor(BasePermission):
    """Может видеть только своего подрядчика (Contractor)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Contractor'

    def filter_queryset(self, request, queryset, view):
        # Фильтруем по подрядчику пользователя
        if hasattr(request.user, 'contractor_id') and request.user.contractor_id:
            return queryset.filter(id=request.user.contractor_id)
        return queryset.none()


class CanViewOwnDocuments(BasePermission):
    """Может видеть только свои документы (Contractor)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Contractor'

    def filter_queryset(self, request, queryset, view):
        if hasattr(request.user, 'contractor_id') and request.user.contractor_id:
            return queryset.filter(contractor_id=request.user.contractor_id)
        return queryset.none()


class CanViewOwnEmployees(BasePermission):
    """Может видеть только своих сотрудников (Contractor)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Contractor'

    def filter_queryset(self, request, queryset, view):
        if hasattr(request.user, 'contractor_id') and request.user.contractor_id:
            return queryset.filter(contractor_id=request.user.contractor_id)
        return queryset.none()


class CanViewOwnPasses(BasePermission):
    """Может видеть только свои пропуска (Contractor)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Contractor'

    def filter_queryset(self, request, queryset, view):
        if hasattr(request.user, 'contractor_id') and request.user.contractor_id:
            # Пропуска сотрудников своего подрядчика
            employee_ids = ContractorEmployee.objects.filter(
                contractor_id=request.user.contractor_id
            ).values_list('id', flat=True)
            return queryset.filter(employee_id__in=employee_ids)
        return queryset.none()