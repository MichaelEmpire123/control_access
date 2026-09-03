from rest_framework import serializers

from pilot.models import AccessPass


class AccessPassSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessPass
        fields = '__all__'

