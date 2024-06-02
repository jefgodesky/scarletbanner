from django.shortcuts import get_object_or_404, render

from scarletbanner.wiki.models import Page


def create(request):
    return render(request, "wiki/create.html")


def page(request, slug):
    page = get_object_or_404(Page, slug=slug)
    return render(request, "wiki/page.html", {"page": page})
