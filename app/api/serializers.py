from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from api.models import Record, RequestLog

from django.db.utils import IntegrityError


class RecordSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, required=False)
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

class RecordRequestLogSerializer(serializers.Serializer):
    click_count = serializers.SerializerMethodField(method_name='get_click_count')

    def __init__(self, record_id):
        self.record_id = record_id

    def get_click_count(self):
        return RequestLog.objects.filter(pk=self.record_id).count()
        
