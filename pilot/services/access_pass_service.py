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
        # Получаем сотрудника из данных
        employee = data.get('id_employee')

        # Если employee - это число (ID), ищем сотрудника
        if isinstance(employee, int):
            employee_obj = EmployeeService.get_by_id(employee)
            if not employee_obj:
                raise ValueError(f"Сотрудник с ID {employee} не найден")
            employee = employee_obj

        # Если employee - это объект, берем его ID
        if hasattr(employee, 'id'):
            employee_id = employee.id
            employee_obj = employee
        else:
            raise ValueError("Некорректные данные сотрудника")

        # Проверка черного списка (сотрудник)
        if BlacklistService.is_blacklisted('Fizlico', employee_id):
            raise BlacklistError("Сотрудник в черном списке", 'Fizlico', employee_id)

        # Проверка черного списка (компания)
        if BlacklistService.is_blacklisted('Yurlico', employee_obj.id_contractor_id):
            raise BlacklistError("Компания в черном списке", 'Yurlico', employee_obj.id_contractor_id)

        # Проверка комплаенса
        ContractorService.check_compliance(employee_obj.id_contractor_id)

        # Создаем пропуск - передаем объект сотрудника
        create_data = data.copy()
        create_data['id_employee'] = employee_obj

        return cls.create(create_data)

    @classmethod
    def get_by_employee(cls, employee_id):
        return cls.model.objects.filter(id_employee_id=employee_id)

    @classmethod
    def check_pass_status(cls, employee_id):
        passes = cls.model.objects.filter(
            id_employee_id=employee_id,
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