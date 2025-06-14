from django import forms
from django.core.exceptions import ValidationError

class RatingForm(forms.Form):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        label='Rate the Worker',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',  # or 'input input-bordered' for Tailwind
            'placeholder': '1 (worst) - 5 (best)',
            'type': 'number',
            'step': '1',
            'min': '1',
            'max': '5',
        })
    )

    feedback = forms.CharField(
        label='Your Feedback (optional)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',  # or 'textarea textarea-bordered' for Tailwind
            'rows': 3,
            'placeholder': 'Write something about the worker's service...',
        })
    )

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None:
            raise ValidationError("Rating is required.")
        if not (1 <= rating <= 5):
            raise ValidationError("Rating must be between 1 and 5.")
        return rating