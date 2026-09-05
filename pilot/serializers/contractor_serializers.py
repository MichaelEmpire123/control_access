from rest_framework import serializers

from pilot.models import Contractor, ContractorEmployee


class ContractorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contractor
        fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = ContractorEmployee
        fields = ['id', 'id_contractor', 'first_name', 'last_name', 'patronymic', 'passport', 'full_name']

    def get_full_name(self, obj):
        """
        Возвращает полное имя сотрудника.
        obj может быть моделью или словарем.
        """
        # Если obj - это словарь
        if isinstance(obj, dict):
            first_name = obj.get('first_name', '')
            last_name = obj.get('last_name', '')
            patronymic = obj.get('patronymic', '')
            parts = [last_name, first_name]
            if patronymic:
                parts.append(patronymic)
            return ' '.join(parts).strip()

        # Если obj - это модель
        try:
            parts = [obj.last_name, obj.first_name]
            if hasattr(obj, 'patronymic') and obj.patronymic:
                parts.append(obj.patronymic)
            return ' '.join(parts).strip()
        except (AttributeError, TypeError):
            return str(obj)