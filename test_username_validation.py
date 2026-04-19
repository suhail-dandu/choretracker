#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'choretracker.settings')
django.setup()

from accounts.forms import AddChildForm
from accounts.models import User
from datetime import date

print("Testing AddChildForm username validation...")

# Create a test user with a specific username
test_username = "testchild123"
try:
    # Clean up any existing test users
    User.objects.filter(username=test_username).delete()

    # Create a test user
    test_user = User.objects.create_user(
        username=test_username,
        password='temppass123',
        first_name='Test',
        role='child'
    )
    print(f"✓ Created test user: {test_username}")

    # Now try to create another user with the same username via the form
    form_data = {
        'first_name': 'NewChild',
        'last_name': 'TestLast',
        'username': test_username,  # Duplicate!
        'password': 'newpass123',
        'date_of_birth': '2015-01-01',
        'avatar': '🦁'
    }

    form = AddChildForm(data=form_data)

    if form.is_valid():
        print("✗ FAIL: Form should have rejected duplicate username!")
    else:
        if 'username' in form.errors:
            print(f"✓ PASS: Form correctly rejected duplicate username")
            print(f"  Error message: {form.errors['username'][0]}")
        else:
            print(f"✗ FAIL: Username error not in form.errors")
            print(f"  Errors: {form.errors}")

    # Clean up
    test_user.delete()
    print("\n✓ Test completed successfully!")

except Exception as e:
    print(f"✗ Error during test: {e}")
    import traceback
    traceback.print_exc()

