import json
from django.utils.timezone import now, timedelta
from django.contrib.auth.hashers import make_password
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Sum

from .models import Product, Cart, CartItem, Order, User
from .serializers import (
    ProductSerializer,
    OrderSerializer,
    ConfirmedOrderStatsSerializer
)

# ======================
# PRODUCT VIEWS
# ======================
class ProductCreateAPIView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    parser_classes = [MultiPartParser, FormParser]


class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer


class Confirm(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = "pk"


# ======================
# ORDER & CART LOGIC
# ======================
class OrderCreateAPIView(APIView):
    """
    Checkout endpoint:
    - Creates a Cart
    - Creates CartItems (supports multiple colors)
    - Creates Order linked to Cart
    - Sends WebSocket notification
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        data = request.data
        try:
            # 1️⃣ Create Cart
            cart = Cart.objects.create()

            # 2️⃣ Parse items JSON
            items_json = data.get("items", "[]")
            items_list = json.loads(items_json)

            if not items_list:
                return Response({"error": "Your shopping bag is empty"},
                                status=status.HTTP_400_BAD_REQUEST)

            # 3️⃣ Create Order
            order = Order.objects.create(
                customer_name=data.get("username"),
                cart=cart,
                payment_screenshot=request.FILES.get("payment_screenshot"),
                status="PENDING"
            )

            # 4️⃣ Create CartItems (handle multiple colors)
            for item_data in items_list:
                product_id = item_data.get("id")
                quantity = item_data.get("quantity", 1)
                size = item_data.get("size", "M")
                colors = item_data.get("colors", [])

                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    continue

                if isinstance(colors, list) and colors:
                    for color in colors:
                        CartItem.objects.create(
                            cart=cart,
                            product=product,
                            quantity=quantity,
                            size=size,
                            color=color
                        )
                else:
                    CartItem.objects.create(
                        cart=cart,
                        product=product,
                        quantity=quantity,
                        size=size,
                        color="Default"
                    )

            # 5️⃣ Send WebSocket notification
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "admin_notifications",
                    {
                        "type": "send_notification",
                        "message": f"🛒 New order from {order.customer_name}",
                        "order_id": order.id,
                        "created_at": str(order.created_at),
                    }
                )
            except Exception as ws_error:
                print(f"WebSocket error: {ws_error}")

            return Response(
                {
                    "order_id": order.id,
                    "message": "Order placed successfully! Pending verification.",
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            print(f"Checkout Error: {str(e)}")
            return Response(
                {"error": "Failed to process order. Ensure all fields are valid."},
                status=status.HTTP_400_BAD_REQUEST
            )


# ======================
# CONFIRM ORDER
# ======================
class ConfirmOrderAPIView(APIView):
    """Updates Order status to CONFIRMED."""
    def patch(self, request, pk):
        try:
            order = Order.objects.get(id=pk)
            order.status = "CONFIRMED"
            order.save()
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)


# ======================
# CREATE SALES USER
# ======================
class CreateSalesUserAPIView(APIView):
    """Create a user with Sales Admin permissions."""
    def post(self, request):
        try:
            user = User.objects.create(
                username=request.data["username"],
                password=make_password(request.data["password"]),
                is_sales_admin=True
            )
            return Response({"username": user.username, "status": "Sales admin created"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ======================
# LIST ALL ORDERS
# ======================
class OrderListAPIView(generics.ListAPIView):
    """List all orders (for admin dashboard)."""
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer


# ======================
# BASE REPORT VIEW
# ======================
class BaseConfirmedOrdersReportAPIView(generics.ListAPIView):
    """
    Base class for confirmed orders report.
    Subclasses set period_days for today/week/month.
    Supports optional filters: size and color.
    """
    serializer_class = ConfirmedOrderStatsSerializer
    period_days = 0  # override in subclass

    def get_queryset(self):
        today = now().date()
        start_date = today - timedelta(days=self.period_days)

        # 1️⃣ Filter confirmed orders by period
        orders = Order.objects.filter(status='CONFIRMED', created_at__date__gte=start_date)

        # 2️⃣ Get related CartItems
        cart_items = CartItem.objects.filter(cart__order__in=orders)

        # 3️⃣ Apply optional query filters
        size_filter = self.request.query_params.get('size')
        color_filter = self.request.query_params.get('color')
        if size_filter:
            cart_items = cart_items.filter(size=size_filter)
        if color_filter:
            cart_items = cart_items.filter(color=color_filter)

        # 4️⃣ Aggregate by product, size, color
        queryset = cart_items.values('product__name', 'size', 'color') \
            .annotate(total_quantity=Sum('quantity')) \
            .order_by('product__name', 'size', 'color')

        # 5️⃣ Rename product__name to product_name
        for item in queryset:
            item['product_name'] = item.pop('product__name')

        return queryset


# ======================
# TODAY / WEEK / MONTH REPORTS
# ======================
class ConfirmedOrdersTodayAPIView(BaseConfirmedOrdersReportAPIView):
    period_days = 0


class ConfirmedOrdersWeekAPIView(BaseConfirmedOrdersReportAPIView):
    period_days = 7


class ConfirmedOrdersMonthAPIView(BaseConfirmedOrdersReportAPIView):
    period_days = 30
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import now, timedelta
from django.db.models import Sum
from .models import CartItem, Order

# =============================
# TOTAL CONFIRMED ORDERS TODAY
# =============================
class ConfirmedOrdersTodayTotalAPIView(APIView):
    """
    Returns total quantity of confirmed orders today.
    Optional filters: size and color
    """
    def get(self, request):
        today = now().date()
        cart_items = CartItem.objects.filter(
            cart__order__status='CONFIRMED',
            cart__order__created_at__date=today
        )

        # Optional filters
        size_filter = request.query_params.get('size')
        color_filter = request.query_params.get('color')
        if size_filter:
            cart_items = cart_items.filter(size=size_filter)
        if color_filter:
            cart_items = cart_items.filter(color=color_filter)

        # Sum all quantities
        total_quantity = cart_items.aggregate(total=Sum('quantity'))['total'] or 0

        return Response({
            "date": str(today),
            "size": size_filter or "All",
            "color": color_filter or "All",
            "total_quantity": total_quantity
        })


# =============================
# TOTAL CONFIRMED ORDERS THIS WEEK
# =============================
class ConfirmedOrdersWeekTotalAPIView(APIView):
    """
    Returns total quantity of confirmed orders in the last 7 days.
    Optional filters: size and color
    """
    def get(self, request):
        today = now().date()
        week_ago = today - timedelta(days=7)
        cart_items = CartItem.objects.filter(
            cart__order__status='CONFIRMED',
            cart__order__created_at__date__gte=week_ago
        )

        size_filter = request.query_params.get('size')
        color_filter = request.query_params.get('color')
        if size_filter:
            cart_items = cart_items.filter(size=size_filter)
        if color_filter:
            cart_items = cart_items.filter(color=color_filter)

        total_quantity = cart_items.aggregate(total=Sum('quantity'))['total'] or 0

        return Response({
            "start_date": str(week_ago),
            "end_date": str(today),
            "size": size_filter or "All",
            "color": color_filter or "All",
            "total_quantity": total_quantity
        })


# =============================
# TOTAL CONFIRMED ORDERS THIS MONTH
# =============================
class ConfirmedOrdersMonthTotalAPIView(APIView):
    """
    Returns total quantity of confirmed orders in the last 30 days.
    Optional filters: size and color
    """
    def get(self, request):
        today = now().date()
        month_ago = today - timedelta(days=30)
        cart_items = CartItem.objects.filter(
            cart__order__status='CONFIRMED',
            cart__order__created_at__date__gte=month_ago
        )

        size_filter = request.query_params.get('size')
        color_filter = request.query_params.get('color')
        if size_filter:
            cart_items = cart_items.filter(size=size_filter)
        if color_filter:
            cart_items = cart_items.filter(color=color_filter)

        total_quantity = cart_items.aggregate(total=Sum('quantity'))['total'] or 0

        return Response({
            "start_date": str(month_ago),
            "end_date": str(today),
            "size": size_filter or "All",
            "color": color_filter or "All",
            "total_quantity": total_quantity
        })
