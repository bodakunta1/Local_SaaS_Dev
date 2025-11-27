from django.db import models
from django.utils import timezone

from customers.models import Client, Plan

# Create your models here.

class SubscriptionOrder(models.Model):
    """
    Represents a subscription 'order' for a tenant:
    - upgrade, downgrade or renewal of a plan
    - one row per billing cycle / trnasaction intent
    """

    BILLING_PERIOD_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    tenant = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="subscription_orders",
        help_text="Which tenant (client) this order belongs to."
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscription_orders",
        help_text="Plan that the tenant is purchasing or renewing."
    )

    billing_period = models.CharField(
        max_length=20,
        choices=BILLING_PERIOD_CHOICES,
        default="monthly",

    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount to be charged for this subscription period. "
    )

    currency = models.CharField(max_length=10, default="INR")

    created_at = models.DateTimeField(auto_now_add=True)

    #Lifecycle tracking
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    #When payment is confirmed(set from a webhook or callback)
    paid_at = models.DateTimeField(null=True, blank=True)

    #Optional: store how long this order extends the subscription
    period_start = models.DateField(
        null=True,
        blank=True,
        help_text="Subcription period start after payment."
    )

    period_end = models.DateField(
        null=True,
        blank=True,
        help_text="Subscription period end after payment."
    )

    def __str__(self):
        return f"{self.tenant} - {self.plan.name} ({self.billing_period})"
    

class Payment(models.Model):
    """
    One payment attempt/record for a SubscriptionOrder.
    Useful if a user retries payment multiple times.
    """

    PROVIDER_CHOICES =[
        ("razorpay", "Razorpay"),
        ("manual", "Manual"),
    ]

    order = models.ForeignKey(
        SubscriptionOrder,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        help_text="which payment gateway processed this payment. "
    )

    provider_payment_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="Payment ID/reference returned by Razorpay."
    )

    provider_order_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="Order/Session ID returned by gateway."
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")

    STATUS_CHOICES = [
        ("created", "Created"),
        ("processing", "Processing"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #Optionally store raw gateway response for debugging
    raw_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Optional raw payload from gateway for debugging/audit."
    )

    def __str__(self):
        return f"{self.order} - {self.provider} - {self.status}"

