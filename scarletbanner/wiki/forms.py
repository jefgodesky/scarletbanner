from django import forms

from scarletbanner.users.models import User
from scarletbanner.wiki.enums import PageType, PermissionLevel
from scarletbanner.wiki.models import WikiPage


class WikiPageForm(forms.ModelForm):
    page_type = forms.ChoiceField(choices=PageType.get_choices())
    title = forms.CharField(max_length=255)
    slug = forms.SlugField(max_length=255)
    body = forms.CharField(widget=forms.Textarea)
    owner = forms.ModelChoiceField(queryset=User.objects.all())
    read = forms.ChoiceField(choices=PermissionLevel.get_choices())
    write = forms.ChoiceField(choices=PermissionLevel.get_choices())

    class Meta:
        model = WikiPage
        fields = []
