#!/usr/bin/env python
import os
import sys
import django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aip_project.settings')

django.setup()

from processing_app.models import ProjectStatus
import json

out = []
for s in ProjectStatus.objects():
    out.append({'project_id': s.project_id, 'running': s.running, 'completed': s.completed, 'result_present': bool(s.result)})
print(json.dumps(out, indent=2))
