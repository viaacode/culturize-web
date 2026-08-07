from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from api.models import Record, RequestLog

from django.conf import settings

class RecordSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, required=False)
    resource_url = serializers.URLField(required=True)
    persistent_url = serializers.CharField(required=True)
    enabled = serializers.BooleanField(required=False)
    status = serializers.CharField(read_only=True, required=False)

    def create(self, validated_data):
        defaults = {k: v for k, v in validated_data.items() if k != "persistent_url"}
        record, _ = Record.objects.update_or_create(
            persistent_url=validated_data["persistent_url"],
            defaults=defaults,
        )
        return record

    def update(self, instance, validated_data):
        instance.resource_url = validated_data.get('resource_url', instance.resource_url)
        instance.enabled = validated_data.get('enabled', instance.enabled)
        instance.save()
        return instance

    def validate_persistent_url(self, value):
        if not settings.PURI_CHECK:
            return value

        if value.startswith(f"{settings.ALLOWED_HOSTS[0]}/") and len(value) > len(f"{settings.ALLOWED_HOSTS[0]}/"):
            return value
        raise serializers.ValidationError("persistent_url should start with the domain name followed by a slash + something")



class RequestLogSerializer(serializers.Serializer):
    datetime = serializers.DateTimeField(required=True)
    persistent_url = serializers.CharField(required=True, source="record.persistent_url")
    referer = serializers.CharField()

class RecordRequestLogSerializer(serializers.Serializer):
    click_count = serializers.SerializerMethodField(method_name='get_click_count')

    def __init__(self, record_id):
        self.record_id = record_id

    def get_click_count(self):
        return RequestLog.objects.filter(pk=self.record_id).count()
        
