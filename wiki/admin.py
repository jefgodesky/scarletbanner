from django.contrib import admin

from wiki.enums import PageType, PermissionLevel
from wiki.forms import WikiPageForm
from wiki.models import Revision, WikiPage


class RevisionInline(admin.TabularInline):
    model = Revision
    fk_name = "page"
    extra = 0


@admin.register(WikiPage)
class WikiPageAdmin(admin.ModelAdmin):
    form = WikiPageForm
    inlines = [RevisionInline]
    list_display = ("title", "slug", "page_type")
    search_fields = ("title", "slug", "body", "page_type")

    def page_type(self, obj):
        return obj.latest.page_type

    def title(self, obj):
        return obj.latest.title

    def slug(self, obj):
        return obj.latest.slug

    def body(self, obj):
        return obj.latest.body

    def owner(self, obj):
        return obj.latest.owner

    def read(self, obj):
        return obj.latest.read

    def write(self, obj):
        return obj.latest.write

    @admin.display(
        description="Last Updated",
        ordering="revisions__timestamp",
    )
    def updated(self, obj):
        return obj.latest.timestamp

    ordering = ("-revisions__timestamp",)

    fieldsets = (
        (None, {"fields": ("page_type", "title", "slug", "body")}),
        ("Permissions", {"fields": ("owner", "read", "write")}),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            latest = obj.latest
            form.base_fields["page_type"].initial = latest.page_type
            form.base_fields["title"].initial = latest.title
            form.base_fields["slug"].initial = latest.slug
            form.base_fields["body"].initial = latest.body
            form.base_fields["owner"].initial = latest.owner
            form.base_fields["read"].initial = latest.read
            form.base_fields["write"].initial = latest.write
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.update(
            page_type=PageType(form.cleaned_data["page_type"]),
            title=form.cleaned_data["title"],
            slug=form.cleaned_data["slug"],
            body=form.cleaned_data["body"],
            editor=request.user,
            owner=form.cleaned_data["owner"],
            read=PermissionLevel(form.cleaned_data["read"]),
            write=PermissionLevel(form.cleaned_data["write"]),
        )
        obj.save()
