from rest_framework import serializers

from pilot.models import AccessPass, ContractorEmployee


class AccessPassSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessPass
        fields = '__all__'

    def validate_id_employee(self, value):
        """Проверка существования сотрудника"""
        # Если value - это число (ID)
        if isinstance(value, int):
            try:
                employee = ContractorEmployee.objects.get(id=value)
                return employee  # Возвращаем объект, а не ID
            except ContractorEmployee.DoesNotExist:
                raise serializers.ValidationError(f"Сотрудник с ID {value} не найден")

        # Если value - это объект
        if hasattr(value, 'id'):
            try:
                employee = ContractorEmployee.objects.get(id=value.id)
                return employee
            except ContractorEmployee.DoesNotExist:
                raise serializers.ValidationError(f"Сотрудник с ID {value.id} не найден")

        raise serializers.ValidationError("Некорректный ID сотрудника")

    def to_internal_value(self, data):
        """Преобразуем данные перед валидацией"""
        # Если id_employee - это число, оставляем как есть
        # Валидатор сам найдет сотрудника
        return super().to_internal_value(data)