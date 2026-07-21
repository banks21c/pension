from django.urls import path

from . import views

urlpatterns = [
    path("products/", views.pension_products, name="pension-products"),
    path("irp/", views.irp_products, name="irp-products"),
]
