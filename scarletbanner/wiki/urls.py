from django.urls import path

from scarletbanner.wiki import views

app_name = "wiki"

urlpatterns = [
    path("create/", views.create, name="create"),
    path("<slug:slug>/", views.page, name="page"),
]
