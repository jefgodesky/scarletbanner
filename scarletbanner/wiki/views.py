from django.shortcuts import get_object_or_404, redirect, render

from scarletbanner.wiki.forms import PageForm
from scarletbanner.wiki.models import Page


def create(request):
    if request.method == "POST":
        form = PageForm(request.POST, request.FILES)
        if form.is_valid():
            page = form.save()
            return redirect("page", slug=page.slug)
    else:
        form = PageForm()

    return render(request, "page_form.html", {"form": form})


def page(request, slug):
    page = get_object_or_404(Page, slug=slug)
    return render(request, "page.html", {"page": page})
