from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from api.models import Record

from django.db.utils import IntegrityError


class RecordSerializer(serializers.Serializer):
    resource_url = serializers.URLField(required=True)
    persistent_url = serializers.CharField(required=True)
    enabled = serializers.BooleanField(required=False)

    def create(self, validated_data):
        try:
            record = Record.objects.create(**validated_data)
        except IntegrityError as e:
            record = Record.objects.get(persistent_url=validated_data["persistent_url"])
            self.update(record, validated_data)
        return record

    def update(self, instance, validated_data):
        instance.resource_url = validated_data.get('resource_url', instance.resource_url)
        instance.enabled = validated_data.get('enabled', instance.enabled)
        instance.save()
        return instance

class RequestLogSerializer(serializers.Serializer):
    datetime = serializers.DateTimeField(required=True)
    persistent_url = serializers.CharField(required=True, source="record.persistent_url")
    referer = serializers.CharField()

