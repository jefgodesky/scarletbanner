from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from scarletbanner.wiki.models import Character, OwnedPage, Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": ("title", "body")
        }),
        ("Organization", {
            "fields": ("parent", "slug"),
        }),
        ("Permissions", {
            "fields": ("read", "write"),
        }),
    )


@admin.register(OwnedPage)
class OwnedPageAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": ("title", "body")
        }),
        ("Ownership", {
            "fields": ("owner",),
        }),
        ("Organization", {
            "fields": ("parent", "slug"),
        }),
        ("Permissions", {
            "fields": ("read", "write"),
        }),
    )


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": ("title", "body")
        }),
        ("Ownership", {
            "fields": ("owner",),
        }),
        ("Organization", {
            "fields": ("parent", "slug"),
        }),
        ("Permissions", {
            "fields": ("read", "write"),
        }),
    )
