from django import forms
from django.forms import modelform_factory
from scarletbanner.wiki.models import Page


class PageForm(forms.ModelForm):
    type = forms.ChoiceField(
        choices=[
            ("page", "Page"),
            ("character", "Character"),
            ("file", "File"),
            ("image", "Image"),
        ]
    )

    class Meta:
        model = Page
        fields = ["title", "slug", "body", "parent", "read", "write"]

    def __init__(self, *args, **kwargs):
        super(PageForm, self).__init__(*args, **kwargs)
        self.add_subclass_fields()

        if self.instance.pk:
            self.fields["type"].initial = self.instance.polymorphic_ctype.model

    def add_subclass_fields(self):
        for name, field in self.get_all_fields().items():
            if name not in self.fields:
                self.fields[name] = field

    @staticmethod
    def get_all_fields():
        fields = {}
        for model in Page.__subclasses__():
            model_form = modelform_factory(model, exclude=())
            for name, field in model_form().fields.items():
                fields[name] = field
        return fields
