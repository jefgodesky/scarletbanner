from django import forms

from scarletbanner.users.models import User
from wiki.models import Revision, WikiPage


class WikiPageForm(forms.ModelForm):
    page_type = forms.ChoiceField(choices=Revision.PAGE_TYPES)
    title = forms.CharField(max_length=255)
    slug = forms.SlugField(max_length=255)
    body = forms.CharField(widget=forms.Textarea)
    owner = forms.ModelChoiceField(queryset=User.objects.all())
    read = forms.ChoiceField(choices=Revision.SECURITY_CHOICES)
    write = forms.ChoiceField(choices=Revision.SECURITY_CHOICES)

    class Meta:
        model = WikiPage
        fields = []
