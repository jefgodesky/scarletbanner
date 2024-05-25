from django import forms

from wiki.models import Revision, WikiPage


class WikiPageForm(forms.ModelForm):
    title = forms.CharField(max_length=255)
    slug = forms.SlugField(max_length=255)
    body = forms.CharField(widget=forms.Textarea)
    read = forms.ChoiceField(choices=Revision.SECURITY_CHOICES)
    write = forms.ChoiceField(choices=Revision.SECURITY_CHOICES)

    class Meta:
        model = WikiPage
        fields = []
