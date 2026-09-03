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
        fields = ['id', 'id_contractor', 'name', 'first_name', 'last_name', 'passport', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.last_name} {obj.first_name} {obj.name}".strip()