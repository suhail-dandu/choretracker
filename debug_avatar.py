#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from accounts.forms import AddChildForm
from accounts.models import User

# Check if avatar choices exist
print("=" * 60)
print("DEBUGGING AVATAR FORM ISSUE")
print("=" * 60)

print("\n1. User.AVATAR_CHOICES:")
print(User.AVATAR_CHOICES)
print(f"   Count: {len(User.AVATAR_CHOICES)}")

print("\n2. Creating AddChildForm instance:")
form = AddChildForm()

print("\n3. Avatar field properties:")
avatar_field = form.fields['avatar']
print(f"   Field type: {type(avatar_field)}")
print(f"   Field class: {avatar_field.__class__.__name__}")
print(f"   Required: {avatar_field.required}")
print(f"   Widget: {type(avatar_field.widget)}")
print(f"   Choices: {avatar_field.choices}")
print(f"   Choices count: {len(avatar_field.choices)}")

print("\n4. Form HTML rendering:")
html = str(form['avatar'])
print(f"   HTML length: {len(html)}")
print(f"   Contains <select>: {'<select' in html}")
print(f"   Contains <option>: {'<option' in html}")
print(f"\n   First 500 chars of HTML:\n{html[:500]}")

print("\n5. Testing form data submission:")
test_data = {
    'first_name': 'Test',
    'last_name': 'Child',
    'username': 'testuser123',
    'avatar': '🦁',
    'date_of_birth': '2020-01-01',
    'password': 'testpass123'
}
form2 = AddChildForm(test_data)
print(f"   Form is valid: {form2.is_valid()}")
if not form2.is_valid():
    print(f"   Errors: {form2.errors}")
else:
    print(f"   Avatar cleaned: {form2.cleaned_data['avatar']}")

print("\n" + "=" * 60)
print("END DEBUG")
print("=" * 60)

