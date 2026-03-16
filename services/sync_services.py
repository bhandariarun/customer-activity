from dataclasses import dataclass
from typing import List, Optional, Tuple

from django.db import transaction

from apps.customers.models import Customer
from apps.supports.models import Activity
from services.external_clients import CRMClient, SupportClient
from services.normalizers import (
    NormalizedActivity,
    NormalizedCustomer,
    normalize_activity_from_support_post,
    normalize_customer_from_crm,
)


@dataclass
class SyncResult:
    customers_upserted: int
    activities_upserted: int
    activities_orphaned: int
    customer_errors: int
    activity_errors: int
    warnings: List[str]


class SyncService:
    def __init__(
        self,
        crm_client: Optional[CRMClient] = None,
        support_client: Optional[SupportClient] = None,
    ):
        self.crm_client = crm_client or CRMClient()
        self.support_client = support_client or SupportClient()

    def sync(self) -> SyncResult:
        warnings: List[str] = []

        crm_raw = self.crm_client.fetch_customers()
        support_raw = self.support_client.fetch_tickets()

        normalized_customers: List[NormalizedCustomer] = []
        customer_errors = 0
        for item in crm_raw:
            if not isinstance(item, dict):
                customer_errors += 1
                continue
            c = normalize_customer_from_crm(item)
            if c is None:
                customer_errors += 1
                continue
            normalized_customers.append(c)

        normalized_activities: List[NormalizedActivity] = []
        activity_errors = 0
        for item in support_raw:
            if not isinstance(item, dict):
                activity_errors += 1
                continue
            a = normalize_activity_from_support_post(item)
            if a is None:
                activity_errors += 1
                continue
            normalized_activities.append(a)

        with transaction.atomic():
            customers_upserted = self._upsert_customers(normalized_customers)
            activities_upserted, activities_orphaned = self._upsert_activities(
                normalized_activities
            )

        if customer_errors:
            warnings.append(
                f"{customer_errors} CRM customer records were skipped due to invalid fields."
            )
        if activity_errors:
            warnings.append(
                f"{activity_errors} support activity records were skipped due to invalid fields."
            )
        if activities_orphaned:
            warnings.append(
                f"{activities_orphaned} activities reference missing customers; stored with customer=null."
            )

        return SyncResult(
            customers_upserted=customers_upserted,
            activities_upserted=activities_upserted,
            activities_orphaned=activities_orphaned,
            customer_errors=customer_errors,
            activity_errors=activity_errors,
            warnings=warnings,
        )

    def _upsert_customers(self, customers: List[NormalizedCustomer]) -> int:
        upserted = 0
        for c in customers:
            _, created = Customer.objects.update_or_create(
                id=c.id,
                defaults={"name": c.name, "email": c.email},
            )
            # update_or_create counts as upsert; count both creates and updates
            upserted += 1
        return upserted

    def _upsert_activities(
        self, activities: List[NormalizedActivity]
    ) -> Tuple[int, int]:
        upserted = 0
        orphaned = 0

        # Map known customers for faster lookup
        # (for small data sets this is fine; for large scale use bulk patterns)
        customer_ids = {a.customer_id for a in activities if a.customer_id is not None}
        existing_customers = {
            c.id: c for c in Customer.objects.filter(id__in=customer_ids)
        }

        for a in activities:
            customer = (
                existing_customers.get(a.customer_id)
                if a.customer_id is not None
                else None
            )
            if a.customer_id is not None and customer is None:
                orphaned += 1

            Activity.objects.update_or_create(
                source=a.source,
                external_id=a.external_id,
                defaults={
                    "customer": customer,
                    "type": a.type,
                    "title": a.title,
                    "content": a.content,
                },
            )
            upserted += 1

        return upserted, orphaned
