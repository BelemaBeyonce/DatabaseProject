from django import forms
from .models import UploadLAS

class UploadLASForm(forms.ModelForm):
    class Meta:
        model = UploadLAS
        fields = ['files']