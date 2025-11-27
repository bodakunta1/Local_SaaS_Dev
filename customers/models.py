from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.utils import timezone

# Create your models here.


class Plan(models.Model):
    """
    Master list of subscription plans (Basic / Standard / Premium).
    Lives in the public schema via the `customers` app.
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Internal code, e.g. 'basic', 'standard', 'premium'."
    )
    name = models.CharField(
        max_length=100,
        help_text="Display name shown to tenants."
    )
    description = models.TextField(blank=True)

    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional yearly price if you offer yearly billing."
    )
    currency = models.CharField(max_length=10, default="INR")

    # Feature limits (you can extend as needed)
    max_products = models.PositiveIntegerField(null=True, blank=True)
    max_orders_per_month = models.PositiveIntegerField(null=True, blank=True)
    max_staff_users = models.PositiveIntegerField(null=True, blank=True)
    max_storage_mb = models.PositiveIntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["monthly_price"]

    def __str__(self):
        return f"{self.name} ({self.currency} {self.monthly_price}/month)"



class Client(TenantMixin):
    # Tenant Info 
    tenant_name = models.CharField(max_length=100)
    server_name = models.CharField(max_length=150, help_text="VPS or server identifier")
    desired_domain = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Tenant's desired subdomain (e.g., 'store1', 'bigco')."
    )
    created_on = models.DateField(auto_now_add=True)
    email=models.EmailField(null=True,blank=True)
    company=models.CharField(max_length=200,null=True,blank=True)
    address=models.TextField(null=True,blank=True)
    logo=models.ImageField(upload_to='tenant_logos/', null=True, blank=True)

    plan = models.ForeignKey(
        Plan, 
        on_delete=models.PROTECT,
        related_name="tenants",
        null=True,
        blank=True,
        help_text="Current active subscription plan for this tenant."
    )

    #  Subscription 
    PLAN_TYPE_CHOICES=[
        ('Basic','Basic'),
        ('Standard','Standard'),
        ('Premium','Premium')
    ]
    plan_type = models.CharField(max_length=50,choices=PLAN_TYPE_CHOICES,default='Basic')
    subscription_start = models.DateField(
        auto_now_add=True
        )
    subscription_end = models.DateField(
        null=True, 
        blank=True
        )

    on_trial = models.BooleanField(default=False)

    trial_end = models.DateField(
        null=True,
        blank=True,
        help_text="If on_trial = True, Trial ends this date."
    )

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
        ("Cancelled", "cancelled"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    # Usage & Analytics 
    storage_used_mb = models.FloatField(default=0.0)
    product_count = models.IntegerField(default=0)
    order_count = models.IntegerField(default=0)
    visitor_count_7d = models.IntegerField(default=0)
    visitor_count_30d = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    last_login = models.DateTimeField(null=True, blank=True)

    # Payments
    total_orders_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    last_payment_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)

    PAYMENT_MODES = [
        ('COD', 'Cash on Delivery'),
        ('UPI', 'UPI'),
        ('CARD', 'Credit/Debit Card'),
    ]
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODES, default='COD')
    PAYMENT_STATUS_CHOICES=[
        ('Unpaid','Unpaid'),
        ('Paid','Paid')
    ]
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES,default="Unpaid")
    PAYMENT_PLAN=[
        ('Weekly','Weekly'),
        ('Monthly','Monthly')
    ]
    payment_plan=models.CharField(max_length=20,choices=PAYMENT_PLAN,default='Weekly')

    #  Django Tenants Required
    auto_create_schema = True

    def __str__(self):
        return self.tenant_name
    
    def has_active_subcription(self) -> bool:
        """ Return True if subcription_end is in future. """
        if self.subscription_end is None:
            return False
        return self.subscription_end >= timezone.now().date()
    
    def is_on_trial(self) -> bool:
        """ Return True if tenant is currently in trial period. """
        if not self.on_trial or self.trial_end is None:
            return False
        return self.trial_end >= timezone.now().date()
    
    
class Domain(DomainMixin):
    pass

class TenantRequest(models.Model):
    tenant_name = models.CharField(max_length=100)
    desired_domain = models.CharField(max_length=150)
    email = models.EmailField(null=True, blank=True)
    company = models.CharField(max_length=200,null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)
    PLAN_TYPE_CHOICES = [
        ('Basic', 'Basic'),
        ('Standard', 'Standard'),
        ('Premium', 'Premium'),
    ]
    plan_type = models.CharField(max_length=50,choices=PLAN_TYPE_CHOICES,default='Basic')
    PAYMENT_MODE_CHOICES = [
        ('COD', 'Cash On Delivery'),
        ('UPI', 'UPI'),
        ('CARD', 'Credit/Debit Card'),
    ]
    payment_mode = models.CharField(max_length=10,choices=PAYMENT_MODE_CHOICES,default='COD')
    PAYMENT_PLAN_CHOICES = [
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
            ]
    payment_plan=models.CharField(max_length=10,choices=PAYMENT_PLAN_CHOICES,default='Monthly')
    created_on = models.DateTimeField(auto_now_add=True)
    requested_on = models.DateField(default=timezone.now)
    is_approved = models.BooleanField(default=False)


    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.tenant_name} ({self.status})"

