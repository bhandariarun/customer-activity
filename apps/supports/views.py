from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import NotFound

from apps.supports.models import Activity
from apps.customers.models import Customer
from apps.base.pagination import StandardResultsSetPagination
from .serializers import ActivitySerializer
from services.exceptions import ExternalServiceError
from services.sync_services import SyncService
from .filters import ActivityFilter
from .choices import ActivityType, ActivitySource

class SyncView(APIView):
    """
    POST /sync
    Fetches external data, normalizes, stores locally.
    Idempotent due to update_or_create + unique constraint.
    """

    def post(self, request):
        service = SyncService()
        try:
            result = service.sync()
        except ExternalServiceError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            # Catch-all to avoid leaking stack traces; in real systems log the exception.
            return Response(
                {"detail": "Unexpected error during sync."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "customers_upserted": result.customers_upserted,
                "activities_upserted": result.activities_upserted,
                "activities_orphaned": result.activities_orphaned,
                "customer_errors": result.customer_errors,
                "activity_errors": result.activity_errors,
                "warnings": result.warnings,
            },
            status=status.HTTP_200_OK,
        )

@extend_schema_view(
    get=extend_schema(
        summary="List activities (with filters)",
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
class CustomerActivitiesView(ListAPIView):
    """
    GET /customers/{id}/activities
    """
    serializer_class = ActivitySerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        customer_id = self.kwargs.get("id")
        try:
            customer_id = int(customer_id)
        except (TypeError, ValueError):
            raise NotFound("Invalid customer id")

        if not Customer.objects.filter(id=customer_id).exists():
            raise NotFound("Customer not found")

        return Activity.objects.filter(customer_id=customer_id).order_by("-created_at", "-id")


@extend_schema_view(
    get=extend_schema(
        summary="List activities (with filters)",
        parameters=[
            OpenApiParameter(
                name="type",
                type=OpenApiTypes.STR,
                required=False,
                description=f"Filter by activity type. Allowed: {[c[0] for c in ActivityType.choices]}",
            ),
            OpenApiParameter(
                name="source",
                type=OpenApiTypes.STR,
                required=False,
                description=f"Filter by activity source. Allowed: {[c[0] for c in ActivitySource.choices]}",
            ),
            OpenApiParameter(
                name="customer_id",
                type=OpenApiTypes.INT,
                required=False,
                description="Filter activities by customer id.",
            ),
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
class ActivitiesListView(ListAPIView):
    """
    GET /activities?source=support&type=ticket&customer_id=1
    """
    queryset = Activity.objects.all().order_by("-created_at", "-id")
    serializer_class = ActivitySerializer
    pagination_class = StandardResultsSetPagination

    filter_backends = [DjangoFilterBackend]
    filterset_class = ActivityFilter