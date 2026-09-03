from django.db import transaction

from pilot.models import AccessPass
from pilot.services.base_service import BaseService
from pilot.services.blacklist_service import BlacklistService
from pilot.services.contractor_service import EmployeeService, ContractorService
from pilot.utils import BlacklistError


class AccessPassService(BaseService):
    model = AccessPass

    @classmethod
    @transaction.atomic
    def create_pass(cls, data):
        employee_id = data.get('employee_id')
        employee = EmployeeService.get_by_id(employee_id)
        if not employee:
            raise ValueError("Сотрудник не найден")

        # Проверка черного списка
        if BlacklistService.is_blacklisted('Fizlico', employee_id):
            raise BlacklistError("Сотрудник в черном списке", 'Fizlico', employee_id)

        if BlacklistService.is_blacklisted('Yurlico', employee.contractor_id):
            raise BlacklistError("Компания в черном списке", 'Yurlico', employee.contractor_id)

        # Проверка комплаенса
        ContractorService.check_compliance(employee.contractor_id)

        return cls.create(data)

    @classmethod
    def get_by_employee(cls, employee_id):
        return cls.model.objects.filter(employee_id=employee_id)

    @classmethod
    def check_pass_status(cls, employee_id):
        passes = cls.model.objects.filter(
            employee_id=employee_id,
            status='active'
        )
        return {
            'has_access': passes.exists(),
            'passes': [{'type': p.type, 'zona': p.zona_access} for p in passes]
        }

    @classmethod
    def activate_pass(cls, pass_id):
        return cls.update(pass_id, {'status': 'active'})

    @classmethod
    def deactivate_pass(cls, pass_id):
        return cls.update(pass_id, {'status': 'passive'})