import json
from datetime import timedelta

from django.utils.timezone import now
from django.db.models import Sum
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404

from rest_framework import generics, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Product, Cart, CartItem, Order, User, Notification
from .serializers import (
    ProductSerializer,
    OrderSerializer,
    ConfirmedOrderStatsSerializer
)

# =====================================================
# PAGINATION
# =====================================================
class DefaultPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


# =====================================================
# NOTIFICATION SERIALIZER
# =====================================================
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


# =====================================================
# NOTIFICATIONS API
# =====================================================
class NotificationListAPIView(generics.ListAPIView):
    queryset = Notification.objects.filter(is_read=False).order_by("-created_at")
    serializer_class = NotificationSerializer
    pagination_class = DefaultPagination
    permission_classes = [IsAuthenticated]


# =====================================================
# PERMISSIONS
# =====================================================
class IsAdminOrSuperAdmin:
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )


class IsSalesOrAdmin:
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in [User.ROLE_ADMIN, User.ROLE_SALES]
        )


class IsAdminOnlyForReports:
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == User.ROLE_ADMIN
        )


# =====================================================
# PRODUCTS
# =====================================================
class ProductCreateAPIView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]


class ProductStatusUpdateAPIView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    http_method_names = ["patch"]

    def patch(self, request, *args, **kwargs):
        product = self.get_object()
        is_active = request.data.get("is_active")

        if is_active is None:
            return Response(
                {"error": "is_active field is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        product.is_active = bool(is_active)
        product.save(update_fields=["is_active"])

        return Response({
            "product_id": product.id,
            "is_active": product.is_active,
            "message": "Product status updated successfully"
        })


class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer


# =====================================================
# ORDER CREATE (CHECKOUT + REALTIME)
# =====================================================
class OrderCreateAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        items = json.loads(request.data.get("items", "[]"))

        if not items:
            return Response({"error": "Cart is empty"}, status=400)

        cart = Cart.objects.create()

        for item in items:
            product = get_object_or_404(Product, id=item["id"])
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=item.get("quantity", 1),
                size=item.get("size", "M"),
                color=item.get("color", "Default"),
            )

        order = Order.objects.create(
            customer_name=request.data.get("username"),
            cart=cart,
            payment_screenshot=request.FILES.get("payment_screenshot"),
            status="PENDING",
        )

        notification = Notification.objects.create(
            message=f"🛒 New order from {order.customer_name}"
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "admin_notifications",
            {
                "type": "send_notification",
                "message": notification.message,
                "order_id": order.id,
                "created_at": str(notification.created_at),
            }
        )

        return Response(
            {"order_id": order.id, "message": "Order placed successfully"},
            status=status.HTTP_201_CREATED
        )


# =====================================================
# UPDATE ORDER STATUS
# =====================================================
class UpdateOrderStatusAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def patch(self, request, pk):
        status_value = request.data.get("status")

        if status_value not in ["CONFIRMED", "DELIVERED", "REJECTED"]:
            return Response({"error": "Invalid status"}, status=400)

        order = get_object_or_404(Order, id=pk)
        order.status = status_value
        order.save(update_fields=["status"])

        notification = Notification.objects.create(
            message=f"Order #{order.id} updated to {status_value}"
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "admin_notifications",
            {
                "type": "send_notification",
                "message": notification.message,
                "order_id": order.id,
                "created_at": str(notification.created_at),
            }
        )

        return Response(OrderSerializer(order).data)


# =====================================================
# LIST ORDERS WITH PAGINATION
# =====================================================
class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    pagination_class = DefaultPagination
    permission_classes = [IsSalesOrAdmin]

    def get_queryset(self):
        status_filter = self.request.query_params.get("status")
        qs = Order.objects.all().order_by("-created_at")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


# =====================================================
# CONFIRMED REPORTS
# =====================================================
class ConfirmedOrdersReportAPIView(generics.ListAPIView):
    serializer_class = ConfirmedOrderStatsSerializer
    permission_classes = [IsAuthenticated, IsAdminOnlyForReports]
    pagination_class = DefaultPagination

    def get_queryset(self):
        period = self.request.query_params.get("period", "day")
        days = 1 if period == "day" else 7 if period == "week" else 30
        start_date = now() - timedelta(days=days)

        qs = CartItem.objects.filter(
            cart__order__status="CONFIRMED",
            cart__order__created_at__gte=start_date
        ).values(
            "product__name", "size", "color"
        ).annotate(
            total_quantity=Sum("quantity")
        ).order_by("product__name")

        for row in qs:
            row["product_name"] = row.pop("product__name")

        return qs


# =====================================================
# DELIVERED REPORTS
# =====================================================
class DeliveredOrdersReportBase(generics.ListAPIView):
    serializer_class = ConfirmedOrderStatsSerializer
    permission_classes = [IsAuthenticated, IsAdminOnlyForReports]
    pagination_class = DefaultPagination
    days = 1

    def get_queryset(self):
        start_date = now() - timedelta(days=self.days)

        qs = CartItem.objects.filter(
            cart__order__status="DELIVERED",
            cart__order__created_at__gte=start_date
        ).values(
            "product__name", "size", "color"
        ).annotate(
            total_quantity=Sum("quantity")
        )

        for row in qs:
            row["product_name"] = row.pop("product__name")

        return qs


class DeliveredOrdersTodayAPIView(DeliveredOrdersReportBase):
    days = 1


class DeliveredOrdersWeekAPIView(DeliveredOrdersReportBase):
    days = 7


class DeliveredOrdersMonthAPIView(DeliveredOrdersReportBase):
    days = 30


# =====================================================
# CREATE SALES USER
# =====================================================
class CreateSalesUserAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def post(self, request):
        User.objects.create(
            username=request.data["username"],
            password=make_password(request.data["password"]),
            role=User.ROLE_SALES
        )
        return Response({"message": "Sales user created successfully"})
