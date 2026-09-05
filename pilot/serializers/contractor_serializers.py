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

    def get_full_name(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name} {obj.patronymic}".strip()