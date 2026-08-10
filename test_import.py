import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agro_connect.settings')
django.setup()

try:
    from agro_connect import urls
    print("Import successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
