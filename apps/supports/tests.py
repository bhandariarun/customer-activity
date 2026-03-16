from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.supports.models import Activity
from apps.supports.choices import ActivitySource, ActivityType


class SyncApiTests(APITestCase):
    @patch("apps.supports.views.SyncService")
    def test_post_sync_success_returns_counts(self, SyncServiceMock):
        # Arrange
        service_instance = SyncServiceMock.return_value
        service_instance.sync.return_value = type(
            "Result",
            (),
            {
                "customers_upserted": 10,
                "activities_upserted": 100,
                "activities_orphaned": 0,
                "customer_errors": 0,
                "activity_errors": 0,
                "warnings": [],
            },
        )()

        # Act
        resp = self.client.post("/api/sync", data={}, format="json")

        # Assert
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["customers_upserted"], 10)
        self.assertEqual(resp.data["activities_upserted"], 100)
        self.assertIn("warnings", resp.data)

    @patch("apps.supports.views.SyncService")
    def test_post_sync_external_service_error_returns_502(self, SyncServiceMock):
        from services.exceptions import ExternalServiceError

        # Arrange
        service_instance = SyncServiceMock.return_value
        service_instance.sync.side_effect = ExternalServiceError("Upstream failed")

        # Act
        resp = self.client.post("/api/sync", data={}, format="json")

        # Assert
        self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(resp.data["detail"], "Upstream failed")

    @patch("apps.supports.views.SyncService")
    def test_post_sync_unexpected_error_returns_500(self, SyncServiceMock):
        # Arrange
        service_instance = SyncServiceMock.return_value
        service_instance.sync.side_effect = Exception("boom")

        # Act
        resp = self.client.post("/api/sync", data={}, format="json")

        # Assert
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(resp.data["detail"], "Unexpected error during sync.")


class ActivitiesApiTests(APITestCase):
    def setUp(self):
        self.c1 = Customer.objects.create(id=1, name="A", email="a@example.com")
        self.c2 = Customer.objects.create(id=2, name="B", email="b@example.com")

        # activities for customer 1
        Activity.objects.create(
            external_id=1,
            source=ActivitySource.SUPPORT,
            customer=self.c1,
            type=ActivityType.TICKET,
            title="Invoice API failing for EU customers",
            content="Invoice generation fails for EU customers",
            ai_summary="Summary 1",
            ai_category="technical",
            ai_priority="high",
        )
        Activity.objects.create(
            external_id=2,
            source=ActivitySource.SUPPORT,
            customer=self.c1,
            type=ActivityType.TICKET,
            title="Billing question",
            content="Need invoice copy",
            ai_summary="Summary 2",
            ai_category="billing",
            ai_priority="low",
        )

        # activity for customer 2
        Activity.objects.create(
            external_id=3,
            source=ActivitySource.SUPPORT,
            customer=self.c2,
            type=ActivityType.TICKET,
            title="Integration issue",
            content="Webhook not firing",
            ai_summary="Summary 3",
            ai_category="integration",
            ai_priority="medium",
        )

        # orphan activity
        Activity.objects.create(
            external_id=4,
            source=ActivitySource.SUPPORT,
            customer=None,
            type=ActivityType.TICKET,
            title="Orphan",
            content="Unknown customer",
        )

    def test_get_activities_returns_paginated_results(self):
        resp = self.client.get("/api/activities")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("count", resp.data)
        self.assertIn("results", resp.data)
        self.assertGreaterEqual(resp.data["count"], 4)

        # Ensure AI fields are present in serializer output
        first = resp.data["results"][0]
        self.assertIn("ai_summary", first)
        self.assertIn("ai_category", first)
        self.assertIn("ai_priority", first)

    def test_get_activities_filter_by_customer_id(self):
        resp = self.client.get("/api/activities", {"customer_id": 1})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data["results"]:
            self.assertEqual(item["customer_id"], 1)

    def test_get_activities_filter_by_source(self):
        resp = self.client.get("/api/activities", {"source": "support"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data["results"]:
            self.assertEqual(item["source"], "support")

    def test_get_activities_filter_by_type(self):
        resp = self.client.get("/api/activities", {"type": "ticket"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data["results"]:
            self.assertEqual(item["type"], "ticket")

    def test_get_customer_activities_success(self):
        resp = self.client.get("/api/customers/1/activities")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data["results"]:
            self.assertEqual(item["customer_id"], 1)

    def test_get_customer_activities_invalid_id_returns_404(self):
        # URL is <int:id>, so non-int won't match route; use non-existing int instead
        resp = self.client.get("/api/customers/999/activities")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_customer_activities_customer_not_found_returns_404(self):
        Customer.objects.filter(id=1).delete()
        resp = self.client.get("/api/customers/1/activities")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data["detail"], "Customer not found")