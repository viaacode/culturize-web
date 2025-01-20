from django.db import models


class Record(models.Model):
    resource_url = models.URLField()
    persistent_url = models.CharField(max_length=100, unique=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return f'mapping of {self.persistent_url} to {self.resource_url}'

    class Meta:
        indexes = [
            models.Index(name="not-enabled", fields=['enabled'], condition=models.Q(enabled=False)),
        ]

class RequestLog(models.Model):
    datetime = models.DateTimeField(auto_now=True)
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    referer = models.CharField(max_length=100, null=True)

    
class Export(models.Model):
    export_type = models.CharField(max_length=1) # 'R' for record, 'L' for log
    datetime = models.DateTimeField(auto_now=True)
    filename = models.CharField(max_length=100)

