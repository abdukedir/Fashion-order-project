import json
from django.utils.timezone import now, timedelta
from django.contrib.auth.hashers import make_password
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Product, Cart, CartItem, Order, User
from .serializers import ProductSerializer, OrderSerializer


# ======================
# PRODUCT VIEWS
# ======================
from rest_framework.generics import ListAPIView


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
                return Response(
                    {"error": "Your shopping bag is empty"},
                    status=status.HTTP_400_BAD_REQUEST
                )

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

                # Create one CartItem per selected color
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
                    # fallback if no colors selected
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
# ADMIN / ANALYTICS
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


class WeeklyOrdersAPIView(APIView):
    """Analytics for total orders in the last 7 days."""
    def get(self, request):
        week_ago = now().date() - timedelta(days=7)
        total = Order.objects.filter(created_at__date__gte=week_ago).count()
        return Response({"weekly_orders": total})


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


class OrderListAPIView(generics.ListAPIView):
    """List all orders (for admin dashboard)."""
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import logging
from rest_framework.permissions import AllowAny

from .models import PasswordResetOTP
from .utils import generate_otp

logger = logging.getLogger(__name__)
User = get_user_model()


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email required"}, status=status.HTTP_400_BAD_REQUEST)

        # Avoid MultipleObjectsReturned by picking a single user (prefer active)
        user = User.objects.filter(email__iexact=email, is_active=True).order_by("id").first()
        if not user:
            user = User.objects.filter(email__iexact=email).order_by("id").first()
        if not user:
            # Keep response generic for security
            return Response({"message": "If an account with that email exists, a reset code has been sent."}, status=status.HTTP_200_OK)

        try:
            otp = generate_otp()
            PasswordResetOTP.objects.create(user=user, otp=otp)
        except Exception as e:
            logger.exception("Failed creating OTP object")
            return Response({"error": "Server error creating OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@localhost")

        try:
            send_mail(
                subject="Password Reset OTP",
                message=f"Your OTP is {otp}. It expires in 10 minutes.",
                from_email=from_email,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.exception("Failed sending password reset email")
            # Clean up OTP if email failed
            try:
                PasswordResetOTP.objects.filter(user=user, otp=otp).delete()
            except Exception:
                pass
            return Response({"error": "Failed to send email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # DEBUG convenience: return otp in response only when DEBUG True
        if getattr(settings, "DEBUG", False):
            return Response({"message": "OTP sent to email (console)."}, status=status.HTTP_200_OK)

        return Response({"message": "If an account with that email exists, a reset code has been sent."}, status=status.HTTP_200_OK)


class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        if not all([email, otp, new_password]):
            return Response({"error": "All fields required"}, status=status.HTTP_400_BAD_REQUEST)

        # Select a user safely (prefer active)
        user = User.objects.filter(email__iexact=email, is_active=True).order_by("-id").first()
        if not user:
            user = User.objects.filter(email__iexact=email).order_by("-id").first()
        if not user:
            return Response({"error": "Invalid OTP or user"}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp).order_by("-created_at").first()
        if not otp_obj:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_expired():
            otp_obj.delete()
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user.password = make_password(new_password)
            user.save()
            otp_obj.delete()
        except Exception as e:
            logger.exception("Failed to reset password")
            return Response({"error": "Server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
        