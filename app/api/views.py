from django.shortcuts import render, redirect

from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, pagination

import csv
import json
import logging


from api.models import Record, RequestLog
from api.serializers import RecordSerializer, RequestLogSerializer, RecordRequestLogSerializer
from api.util import access_key

logger = logging.getLogger("django")

class ServiceInfo(APIView):
    def get(self, request, format=None):
        key = request.META.get("HTTP_CULTURIZE_KEY")
        if key != access_key:
            return HttpResponse('Unauthorized', status=401)
        service_info = {}
        service_info["record_count"] = Record.objects.count()
        service_info["enabled_count"] = Record.objects.filter(enabled=True).count()
        service_info["click_count"] = RequestLog.objects.count()
        #general_data["base_url"] = ""

        return Response(service_info)

class RecordList(APIView):
    def get(self, request, format=None):
        key = request.META.get("HTTP_CULTURIZE_KEY")
        if key != access_key:
            return HttpResponse('Unauthorized', status=401)
        records = Record.objects.all().order_by("id")
        paginator = pagination.PageNumberPagination()
        result_page = paginator.paginate_queryset(records, request)
        serializer = RecordSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        key = request.META.get("HTTP_CULTURIZE_KEY")
        if key != access_key:
            return HttpResponse('Unauthorized', status=401)
        data = request.data
        if isinstance(data, list):
            serializer = RecordSerializer(data=data, many=True)
        else:
            serializer = RecordSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RecordDetail(APIView):
    def get_record(self, rid):
        try:
            return Record.objects.get(pk=rid)
        except Record.DoesNotExist:
            raise Http404

    def get(self, request, rid, format=None):
        key = request.META.get("HTTP_CULTURIZE_KEY")
        if key != access_key:
            return HttpResponse('Unauthorized', status=401)
        record = self.get_record(rid)
        serializer = RecordSerializer(record)
        return Response(serializer.data)

    def put(self, request, rid, format=None):
        key = request.META.get("HTTP_CULTURIZE_KEY")
        if key != access_key:
            return HttpResponse('Unauthorized', status=401)
        record = self.get_record(rid)
        serializer = RecordSerializer(record, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, rid, format=None):
        key = request.META.get("HTTP_CULTURIZE_KEY")
        if key != access_key:
            return HttpResponse('Unauthorized', status=401)
        record = self.get_record(rid)
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogList(APIView):
    def get(self, request, format=None):
        key = request.META.get("HTTP_CULTURIZE_KEY")
        if key != access_key:
            return HttpResponse('Unauthorized', status=401)
        logs = RequestLog.objects.all().order_by("id")
        paginator = pagination.PageNumberPagination()
        result_page = paginator.paginate_queryset(logs, request)
        serializer = RequestLogSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

class RecordLogDetail(APIView):
    def get_record_log_count(self, rid):
        try:
            r = Record.objects.get(pk=rid)
            c = RequestLog.objects.filter(record=r).count()
            return c
        except Record.DoesNotExist as e:
            return 0

    def get(self, request, rid, format=None):
        key = request.META.get("HTTP_CULTURIZE_KEY")
        if key != access_key:
            return HttpResponse('Unauthorized', status=401)
        return Response({"click_count": self.get_record_log_count(rid)})

class LogCSVExportView(APIView):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="export.csv"'
        writer = csv.writer(response)

        for log in RequestLog.objects.all():
            row = [log.datetime.isoformat(), log.record.persistent_url, str(log.referer)]
            writer.writerow(row)
        return response


class Login(APIView):
    def post(self, request, format=None):
        key = request.META.get("HTTP_CULTURIZE_KEY")
        if key != access_key:
            return HttpResponse('Unauthorized', status=401)
        return HttpResponse()

def redirect_view(request, persistent_path):
    persistent_url = f"{request.META['HTTP_HOST']}/{persistent_path}"
    
    try:
        record = Record.objects.get(persistent_url=persistent_url)
    except Record.DoesNotExist:
        return HttpResponse(status=404)
    
    if not record.enabled:
        return HttpResponse(status=404)

    rlog = RequestLog(record=record, referer=request.META.get("HTTP_REFERER", None))
    rlog.save()

    return redirect(record.resource_url)
