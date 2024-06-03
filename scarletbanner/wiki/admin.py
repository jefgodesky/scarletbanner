from django.contrib import admin
from django.shortcuts import render
from django.urls import reverse

from scarletbanner.wiki.models import Character, File, Image, OwnedPage, Page, Secret, SecretCategory, Template


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("title", "body")}),
        (
            "Organization",
            {
                "fields": ("parent", "slug"),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("read", "write"),
            },
        ),
    )


@admin.register(OwnedPage)
class OwnedPageAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("title", "body")}),
        (
            "Ownership",
            {
                "fields": ("owner",),
            },
        ),
        (
            "Organization",
            {
                "fields": ("parent", "slug"),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("read", "write"),
            },
        ),
    )


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("title", "body")}),
        (
            "Ownership",
            {
                "fields": ("owner",),
            },
        ),
        (
            "Organization",
            {
                "fields": ("parent", "slug"),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("read", "write"),
            },
        ),
    )


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("title", "body")}),
        (
            "Organization",
            {
                "fields": ("parent", "slug"),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("read", "write"),
            },
        ),
    )


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("title", "attachment", "body")}),
        (
            "Organization",
            {
                "fields": ("parent", "slug"),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("read", "write"),
            },
        ),
    )


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("title", "attachment", "body")}),
        (
            "Organization",
            {
                "fields": ("parent", "slug"),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("read", "write"),
            },
        ),
    )


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
