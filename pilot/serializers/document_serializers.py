from rest_framework import serializers

from pilot.models import ComplianceDocument


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceDocument
        fields = '__all__'