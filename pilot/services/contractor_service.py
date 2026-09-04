from datetime import date

from pilot.models import Contractor, ComplianceDocument, ContractorEmployee
from pilot.services.base_service import BaseService
from pilot.utils import ComplianceError



class ContractorService(BaseService):
    model = Contractor

    @classmethod
    def get_by_inn(cls, inn):
        return cls.model.objects.get(inn=inn)

    @classmethod
    def create_contractor_with_check(cls, data):
        existing = cls.get_by_inn(data.get('inn'))
        if existing:
            raise ValueError(f"Компания с паспортом {data.get('inn')} уже существует")
        return cls.create(data)

    @classmethod
    def check_compliance(cls, contractor_id):
        docs = ComplianceDocument.objects.filter(id_contractor_id=contractor_id)
        today = date.today()

        # Проверяем просроченные документы
        expired_docs = []
        for doc in docs:
            if doc.expiration_date < today:
                expired_docs.append(doc)

        if expired_docs:
            # Если есть просроченные - компания НЕ аккредитована
            cls._update_accreditation(contractor_id, 'Noaccreditate')
            raise ComplianceError(
                f"Просрочен документ: {expired_docs[0].get_type_display()}",
                doc_id=expired_docs[0].id,
                expiry_date=expired_docs[0].expiration_date,
            )

        # Проверяем наличие обязательных документов
        has_insurance = docs.filter(
            type='Insurance',
            expiration_date__gte=today
        ).exists()

        has_registry = docs.filter(
            type='Registry',
            expiration_date__gte=today
        ).exists()

        # Если есть оба документа - аккредитуем
        if has_insurance and has_registry:
            cls._update_accreditation(contractor_id, 'Accreditate')
            return True


        cls._update_accreditation(contractor_id, 'Noaccreditate')
        raise ComplianceError(
            "Отсутствуют обязательные документы (Страхование и СРО)"
        )

    @classmethod
    def _update_accreditation(cls, contractor_id, status):

        contractor = cls.get_by_id(contractor_id)
        if contractor and contractor.status_accreditation != status:
            contractor.status_accreditation = status
            contractor.save(update_fields=['status_accreditation'])
            return contractor
        return contractor

    @classmethod
    def recheck_accreditation(cls, contractor_id):
        # Перепроверка аккредитованности компании (подрядчика)
        contractor = cls.get_by_id(contractor_id)
        if not contractor:
            return None

        docs = ComplianceDocument.objects.filter(id_contractor_id=contractor_id)
        today = date.today()

        # Проверяем все документы
        has_valid_insurance = docs.filter(
            type='Insurance',
            expiration_date__gte=today
        ).exists()

        has_valid_registry = docs.filter(
            type='Registry',
            expiration_date__gte=today
        ).exists()

        # нет ли просроченных документов
        has_expired = docs.filter(expiration_date__lt=today).exists()

        # все документы и нет просроченных, автоматически аккредитация
        if has_valid_insurance and has_valid_registry and not has_expired:
            return cls._update_accreditation(contractor_id, 'Accreditate')
        else:
            return cls._update_accreditation(contractor_id, 'Noaccreditate')


class EmployeeService(BaseService):
    model = ContractorEmployee

    @classmethod
    def get_by_passport(cls, passport):
        return cls.model.objects.filter(passport=passport).first()

    @classmethod
    def create_employee_with_check(cls, data):
        existing = cls.get_by_passport(data.get('passport'))
        if existing:
            raise ValueError(f"Сотрудник с паспортом {data.get('passport')} уже существует")
        return cls.create(data)

