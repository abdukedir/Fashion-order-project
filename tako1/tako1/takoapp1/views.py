import uuid
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.timezone import now, timedelta
from django.db.models import Sum
from django.contrib.auth.hashers import make_password

from .models import Product, Cart, CartItem, Order, User
from .serializers import ProductSerializer, CartSerializer, CartItemSerializer, OrderSerializer


# ======================
# PRODUCT (ADMIN CREATES WITH IMAGE)
# ======================
class ProductCreateAPIView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    parser_classes = [MultiPartParser, FormParser]


class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer

class Confirm(generics.RetrieveUpdateDestroyAPIView):
    queryset=Product.objects.all()
    serializer_class=ProductSerializer
    lookup_field="pk"

# ======================
# CART
# ======================
class GetOrCreateCartAPIView(APIView):
    def get(self, request):
        cart = Cart.objects.create()
        return Response({
            "cart_id": cart.id,
            "session_id": str(cart.session_id)
        })


class CartItemCreateAPIView(APIView):
    def post(self, request):
        cart = Cart.objects.get(session_id=request.data["session_id"])
        product = Product.objects.get(id=request.data["product"])

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            color=request.data["color"],
            size=request.data["size"],
            defaults={"quantity": request.data.get("quantity", 1)}
        )

        if not created:
            item.quantity += int(request.data.get("quantity", 1))
            item.save()

        return Response(CartItemSerializer(item).data)


class CartAPIView(APIView):
    def get(self, request):
        cart = Cart.objects.get(session_id=request.query_params["session_id"])
        return Response(CartSerializer(cart).data)


# ======================
# ORDER
# ======================
class OrderCreateAPIView(APIView):
    def post(self, request):
        cart = Cart.objects.get(session_id=request.data["session_id"])
        order = Order.objects.create(
            customer_name=request.data["customer_name"],
            cart=cart
        )
        return Response({"order_id": order.id})


class UploadPaymentAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, order_id):
        order = Order.objects.get(id=order_id)
        order.payment_screenshot = request.FILES["image"]
        order.save()
        return Response({"status": "uploaded"})


class ConfirmOrderAPIView(APIView):
    def patch(self, request, pk):
        order = Order.objects.get(id=pk)
        order.status = "CONFIRMED"
        order.save()
        return Response(OrderSerializer(order).data)


# ======================
# ANALYTICS
# ======================
class WeeklyOrdersAPIView(APIView):
    def get(self, request):
        week_ago = now().date() - timedelta(days=7)
        total = Order.objects.filter(created_at__date__gte=week_ago).count()
        return Response({"weekly_orders": total})


# ======================
# CREATE SALES USER
# ======================
class CreateSalesUserAPIView(APIView):
    def post(self, request):
        user = User.objects.create(
            username=request.data["username"],
            password=make_password(request.data["password"]),
            is_sales_admin=True
        )
        return Response({"username": user.username})
