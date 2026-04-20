from django import forms
from .models import Chore, ChoreAssignment
from accounts.models import User


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = ['title', 'description', 'points', 'category', 'icon', 'is_recurring']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Clean bedroom'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What needs to be done?'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 25 or -10'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '⭐', 'maxlength': 2}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['points'].help_text = "Positive for rewards, negative for penalties"


class AssignChoreForm(forms.Form):
    assigned_to_multiple = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Assign to"
    )
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        label="Due Date & Time"
    )

    def __init__(self, family, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to_multiple'].queryset = User.objects.filter(family=family, role=User.ROLE_CHILD)


class CompleteChoreForm(forms.Form):
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Tell your parent what you did! (optional)'
        }),
        label="Leave a note"
    )


class RejectChoreForm(forms.Form):
    reason = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Why are you rejecting this? (optional)'
        }),
        label="Rejection reason"
    )


class PayoutForm(forms.Form):
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'e.g. June pocket money payout'
        }),
        label="Note"
    )
