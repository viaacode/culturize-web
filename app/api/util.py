import os
from django.conf import settings

access_key = None

def load_access_key():
    global access_key
    key_file = os.path.join(settings.PROJECT_ROOT, "accesskey")
    try:
        with open(key_file) as f:
            access_key = f.read().strip()
    except FileNotFoundError:
        access_key = os.environ.get("CULTURIZE_ACCESS_KEY")



