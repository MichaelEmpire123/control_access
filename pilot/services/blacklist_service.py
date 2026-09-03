from pilot.models import Blacklist, Contractor, ContractorEmployee
from pilot.services.base_service import BaseService


class BlacklistService(BaseService):
    model = Blacklist

    @classmethod
    def is_blacklisted(cls, entity_type, entity_id):
        return cls.model.objects.filter(
            entity_type=entity_type,
            entity_id=str(entity_id)
        ).exists()

    @classmethod
    def add_to_blacklist(cls, entity_type, entity_id, reason, added_by):
        if entity_type == 'Yurlico' and not Contractor.objects.filter(id=entity_id).exists():
            raise ValueError("Компания не найдена")
        if entity_type == 'Fizlico' and not ContractorEmployee.objects.filter(id=entity_id).exists():
            raise ValueError("Сотрудник не найден")

        if cls.is_blacklisted(entity_type, entity_id):
            raise ValueError("Уже в черном списке")

        return cls.create({
            'entity_type': entity_type,
            'entity_id': str(entity_id),
            'reason': reason,
            'added_by': added_by
        })

    @classmethod
    def remove_from_blacklist(cls, entity_type, entity_id):
        try:
            instance = cls.model.objects.get(
                entity_type=entity_type,
                entity_id=str(entity_id)
            )
            instance.delete()
            return True
        except cls.model.DoesNotExist:
            return False