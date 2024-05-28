from django.contrib import admin
from django.shortcuts import render
from django.urls import reverse

from wiki.enums import PageType, PermissionLevel
from wiki.forms import WikiPageForm
from wiki.models import Revision, Secret, SecretCategory, WikiPage


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


@admin.register(Secret)
class SecretAdmin(admin.ModelAdmin):
    change_list_template = "admin/tree.html"

    def changelist_view(self, request, extra_context=None):
        root_categories = SecretCategory.objects.filter(parent=None).prefetch_related("children", "secrets")
        context = dict(
            self.admin_site.each_context(request),
            title="Secrets",
            categories=root_categories,
            add_category_url=reverse("admin:wiki_secretcategory_add"),
            add_item_url=reverse("admin:wiki_secret_add"),
        )
        return render(request, "admin/tree.html", context)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "categories" in request.GET:
            form.base_fields["categories"].initial = [request.GET["categories"]]
        return form


@admin.register(SecretCategory)
class SecretCategoryAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
        return {}

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "parent" in request.GET:
            form.base_fields["parent"].initial = request.GET["parent"]
        return form
