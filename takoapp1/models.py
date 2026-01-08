import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


# ======================
# ABSTRACT BASE USER WITH ROLE
# ======================
class AbstractBaseUserWithRole(AbstractUser):
    """
    Abstract base user with role support.
    This model does NOT create a database table.
    """

    ROLE_ADMIN = "ADMIN"
    ROLE_SALES = "SALES"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_SALES, "Sales"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_ADMIN,
        db_index=True
    )

    class Meta:
        abstract = True


# ======================
# CONCRETE USER MODEL
# ======================
class User(AbstractBaseUserWithRole):
    """
    Actual user model used by Django
    """

    def is_sales(self):
        return self.role == self.ROLE_SALES

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def __str__(self):
        return f"{self.username} ({self.role})"


# ======================
# PRODUCT MODEL
# ======================
class Product(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    available_colors = models.JSONField(default=list, blank=True)
    available_sizes = models.JSONField(default=list, blank=True)

    tshirt_type = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ======================
# PRODUCT IMAGE (MULTIPLE IMAGES)
# ======================
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="images",
        on_delete=models.CASCADE,
        db_index=True
    )

    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)  # ⭐ main image
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "id"]

    def __str__(self):
        return f"Image for {self.product.name}"


# ======================
# CART
# ======================
class Cart(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.session_id)


# ======================
# CART ITEM
# ======================
class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        related_name="items",
        on_delete=models.CASCADE,
        db_index=True
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_index=True
    )
    color = models.CharField(max_length=50, db_index=True)
    size = models.CharField(max_length=10, db_index=True)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"


# ======================
# ORDER
# ======================
class Order(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_REJECTED = "REJECTED"
    STATUS_DELIVERED = "DELIVERED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_DELIVERED, "Delivered"),
    ]

    customer_name = models.CharField(max_length=255, db_index=True)

    cart = models.OneToOneField(
        Cart,
        on_delete=models.CASCADE,
        related_name="order"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )

    payment_screenshot = models.ImageField(
        upload_to="payments/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.customer_name} - {self.status}"


# ======================
# NOTIFICATION
# ======================
class Notification(models.Model):
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message
