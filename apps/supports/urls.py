from django.urls import path

from apps.customers.views import CustomersListView
from .views import (
    ActivitiesListView,
    CustomerActivitiesView,
    SyncView,
)

urlpatterns = [
    path("sync", SyncView.as_view(), name="sync"),
    path("customers", CustomersListView.as_view(), name="customers-list"),
    path("customers/<int:id>/activities", CustomerActivitiesView.as_view(), name="customer-activities"),
    path("activities", ActivitiesListView.as_view(), name="activities-list"),
]