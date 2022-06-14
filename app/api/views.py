from django.shortcuts import render, redirect

from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


from api.models import Record, RequestLog
from api.serializers import RecordSerializer, RequestLogSerializer
from api.util import access_key

class RecordList(APIView):
    def get(self, request, format=None):
        key = request.META.get("HTTP_CULTURIZE_KEY")
        if key != access_key:
            return HttpResponse('Unauthorized', status=401)
        records = Record.objects.all()
        #paginator = LimitOffsetPagination()
        serializer = RecordSerializer(instance=records, many=True)
        return Response(serializer.data)

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

class LogList(APIView):
    def get(self, request, format=None):
        key = request.META.get("HTTP_CULTURIZE_KEY")
        if key != access_key:
            return HttpResponse('Unauthorized', status=401)
        logs = RequestLog.objects.all()
        serializer = RequestLogSerializer(instance=logs, many=True)
        return Response(serializer.data)

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
