from django import forms
from .models import RecurringChoreTemplate, CalendarTask, SchedulePattern, BadDeed, BadDeedInstance
from accounts.models import User


class RecurringChoreTemplateForm(forms.ModelForm):
    """Form for creating/editing recurring chores."""

    class Meta:
        model = RecurringChoreTemplate
        fields = [
            'chore_title', 'chore_description', 'points', 'category',
            'frequency', 'days_of_week', 'day_of_month',
            'assigned_to', 'scheduled_time', 'start_date', 'end_date'
        ]
        widgets = {
            'chore_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title'}),
            'chore_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '25'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'days_of_week': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0,1,2,3,4 (Monday-Friday). Leave blank for all days'
            }),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '15', 'min': '1', 'max': '31'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'scheduled_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, family, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(
            family=family, role=User.ROLE_CHILD
        )

    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get('frequency')

        if frequency == 'weekly' and not cleaned_data.get('days_of_week'):
            # Empty means all days, which is valid
            pass
        elif frequency == 'monthly' and not cleaned_data.get('day_of_month'):
            raise forms.ValidationError("Day of month is required for monthly recurrence")

        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError("End date must be after start date")

        return cleaned_data


class CalendarTaskForm(forms.ModelForm):
    """Form for creating/editing calendar tasks."""

    class Meta:
        model = CalendarTask
        fields = ['title', 'description', 'points', 'category', 'scheduled_date', 'scheduled_time', 'due_time']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '25'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'scheduled_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'due_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }


class CalendarTaskCompleteForm(forms.Form):
    """Form for marking calendar task as complete."""
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Tell your parent what you did! (optional)'
        }),
        label="Leave a note"
    )


class CalendarTaskRejectForm(forms.Form):
    """Form for rejecting a calendar task."""
    reason = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Why are you rejecting this? (optional)'
        }),
        label="Rejection reason"
    )


class SchedulePatternForm(forms.ModelForm):
    """Form for creating schedule patterns (holidays, breaks, etc.)."""

    class Meta:
        model = SchedulePattern
        fields = ['name', 'pattern_type', 'start_date', 'end_date', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Christmas Break'}),
            'pattern_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError("End date must be after start date")
        return cleaned_data


class BadDeedForm(forms.ModelForm):
    """Form for creating bad deeds (recurring or one-time)."""

    class Meta:
        model = BadDeed
        fields = [
            'title', 'description', 'negative_points', 'category',
            'is_recurring', 'frequency', 'days_of_week', 'day_of_month',
            'assigned_to', 'scheduled_time', 'start_date', 'end_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Talking back, Fighting'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'negative_points': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5', 'min': '1'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'days_of_week': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0,1,2,3,4 (Mon-Fri). Leave blank for all days'
            }),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '15', 'min': '1', 'max': '31'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'scheduled_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, family, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(
            family=family, role=User.ROLE_CHILD
        )

    def clean(self):
        cleaned_data = super().clean()
        is_recurring = cleaned_data.get('is_recurring')
        frequency = cleaned_data.get('frequency')

        if is_recurring and frequency == 'monthly' and not cleaned_data.get('day_of_month'):
            raise forms.ValidationError("Day of month is required for monthly recurrence")

        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError("End date must be after start date")

        return cleaned_data


class BadDeedInstanceForm(forms.ModelForm):
    """Form for creating one-time bad deed instances."""

    class Meta:
        model = BadDeedInstance
        fields = ['title', 'description', 'negative_points', 'category', 'reason']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bad deed/behavior'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Description'}),
            'negative_points': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5', 'min': '1'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explain why points are being deducted'
            }),
        }
