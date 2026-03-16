from django.urls import path
from .views import (
    CustomersListView,

)

urlpatterns = [
    path("customers", CustomersListView.as_view(), name="customers-list"),
]