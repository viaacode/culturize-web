import os
from django.conf import settings

access_key = None

def load_access_key():
    global access_key
    with open(os.path.join(settings.PROJECT_ROOT, "accesskey")) as f:
        access_key = f.read().strip()



