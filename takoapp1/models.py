import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


# ======================
# Custom User
# ======================
class User(AbstractUser):
    is_sales_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# ======================
# Product Model (ONE IMAGE)
# ======================
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    available_colors = models.JSONField(default=list, blank=True)
    available_sizes = models.JSONField(default=list, blank=True)

    tshirt_type = models.CharField(max_length=100)

    # ✅ SINGLE IMAGE
    image = models.ImageField(upload_to="products/")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ======================
# Cart
# ======================
class Cart(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.session_id)


# ======================
# Cart Item
# ======================
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.quantity * self.product.price


# ======================
# Order
# ======================
class Order(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_REJECTED = "REJECTED"   # ✅ ADD THIS
    STATUS_DELIVERED = "DELIVERED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_REJECTED, "Rejected"),  # ✅ ADD THIS
        (STATUS_DELIVERED, "Delivered"),
    ]

    customer_name = models.CharField(max_length=255)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name="order")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    payment_screenshot = models.ImageField(upload_to="payments/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.status}"

class Notification(models.Model):
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message
