from rest_framework.generics import ListAPIView
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema, extend_schema_view
from apps.base.pagination import StandardResultsSetPagination
from apps.customers.models import Customer
from .serializers import CustomerSerializer

@extend_schema_view(
    get=extend_schema(
        summary="List customers",
        parameters=[
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                required=False,
                description="Results per page",
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                required=False,
                description="Page number",
            ),
        ],
    )
)
class CustomersListView(ListAPIView):
    """
    GET /customers
    """
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer
    pagination_class = StandardResultsSetPagination
