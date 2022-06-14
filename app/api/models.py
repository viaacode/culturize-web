from django.db import models


class Record(models.Model):
    resource_url = models.URLField()
    persistent_url = models.CharField(max_length=100, unique=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return f'mapping of {self.persistent_url} to {self.resource_url}'

class RequestLog(models.Model):
    datetime = models.DateTimeField(auto_now=True)
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    referer = models.CharField(max_length=100, null=True)

    

