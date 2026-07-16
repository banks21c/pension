from django.urls import include, path

from pension_api.views import consult_submit

urlpatterns = [
    path("api/pension/", include("pension_api.urls")),
    path("api/consult/", consult_submit, name="consult"),
]
