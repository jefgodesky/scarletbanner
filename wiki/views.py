from django.shortcuts import get_object_or_404, render

from wiki.models import WikiPage


def create(request):
    return render(request, "wiki/create.html")


def page(request, slug):
    page = get_object_or_404(WikiPage, slug=slug)
    return render(request, "wiki/page.html", {"page": page})
