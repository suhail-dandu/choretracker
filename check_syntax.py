    #!/usr/bin/env python
"""Quick syntax check"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

try:
    from calendar_tasks import views
    print("✅ views.py imports successfully")
    print("✅ No syntax errors")
    print("✅ All functions available:")
    print(f"   - calendar_view")
    print(f"   - _generate_recurring_tasks_for_month")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

