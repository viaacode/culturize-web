from celery import shared_task
from datetime import datetime
import os
import subprocess

from api.models import Export

from django.db.models import Subquery
from django.core.paginator import Paginator

@shared_task()
def export_records():
    ts = datetime.now()
    print("starting record export")
    my_env = os.environ.copy()
    my_env["PGPASSWORD"] = os.environ.get("SQL_PASSWORD", "password")
    filename = f"record-export-{ts.strftime('%Y%m%d%H%M%S')}.zip"
    fullpath = f"/export-data/{filename}"
    cmd = ["psql",
           "-h", os.environ.get("SQL_HOST", "db"),
           "-U", os.environ.get("SQL_USER", "culturize"),
           "-d", os.environ.get("SQL_DATABASE", "culturize"),
           "-c", "'COPY (SELECT * FROM api_record) TO STDOUT WITH CSV HEADER;'",
           "|",
           "zip", fullpath, "-"]
    cmd = " ".join(cmd)
    print(cmd)
    r = subprocess.run(cmd, shell=True, env=my_env)
    if r.returncode == 0:
        print("export successful")
        Export(datetime=ts, export_type='R', filename=filename).save()
    print("end record export")

@shared_task()
def export_logs():
    ts = datetime.now()
    print("starting log export")
    my_env = os.environ.copy()
    my_env["PGPASSWORD"] = os.environ.get("SQL_PASSWORD", "password")
    filename = f"log-export-{ts.strftime('%Y%m%d%H%M%S')}.zip"
    fullpath = f"/export-data/{filename}"
    cmd = ["psql",
           "-h", os.environ.get("SQL_HOST", "db"),
           "-U", os.environ.get("SQL_USER", "culturize"),
           "-d", os.environ.get("SQL_DATABASE", "culturize"),
           "-c", "'COPY (select datetime, persistent_url, referer from api_requestlog AS l INNER JOIN api_record AS r ON record_id = r.id) TO STDOUT WITH CSV HEADER;'",
           "|",
           "zip", fullpath, "-"]
    cmd = " ".join(cmd)
    print(cmd)
    r = subprocess.run(cmd, shell=True, env=my_env)
    if r.returncode == 0:
        print("export successful")
        Export(datetime=ts, export_type='L', filename=filename).save()
    print("end log export")

@shared_task()
def cleanup():
    logs_to_keep = Export.objects.filter(export_type='L').order_by('-id')[:3].values('id')

    logs_query = Export.objects.filter(export_type='L').exclude(id__in=Subquery(logs_to_keep))

    for log in logs_query.all():
        print(f"deleting {log.filename}")
        os.remove(f"/export-data/{log.filename}")
        log.delete()

    records_to_keep = Export.objects.filter(export_type='R').order_by('-id')[:3].values('id')

    records_query = Export.objects.filter(export_type='R').exclude(id__in=Subquery(records_to_keep))

    for record in records_query.all():
        print(f"deleting {record.filename}")
        os.remove(f"/export-data/{record.filename}")
        record.delete()
