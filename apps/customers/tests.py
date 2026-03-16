from rest_framework import status
from rest_framework.test import APITestCase

from apps.customers.models import Customer


class CustomersApiTests(APITestCase):
    def setUp(self):
        Customer.objects.create(id=1, name="Alice", email="alice@example.com")
        Customer.objects.create(id=2, name="Bob", email="bob@example.com")

    def test_get_customers_returns_paginated_results(self):
        resp = self.client.get("/api/customers")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("count", resp.data)
        self.assertIn("results", resp.data)
        self.assertGreaterEqual(resp.data["count"], 2)

        first = resp.data["results"][0]
        self.assertIn("id", first)
        self.assertIn("name", first)
        self.assertIn("email", first)