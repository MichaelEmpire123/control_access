from rest_framework import serializers

from pilot.models import Blacklist


class BlacklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blacklist
        fields = '__all__'