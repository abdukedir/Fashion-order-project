from rest_framework import serializers
from .models import Product, Cart, CartItem, Order


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class CartItemSerializer(serializers.ModelSerializer):
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = "__all__"


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "session_id", "items"]


# class OrderSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Order
#         fields = "__all__"
# below this i am doing the details of the order and the lists of the order
class OrderSerializer(serializers.ModelSerializer):
    cart = CartSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_name",
            "status",
            "cart",
            "payment_screenshot",
            "created_at",
        ]
        
class ConfirmedOrderStatsSerializer(serializers.Serializer):
    """
    Serializer to generate order statistics for confirmed orders.
    Aggregates total quantities per product, size, and color.
    This is not tied directly to a model because we are using aggregation.
    """

    product_name = serializers.CharField()
    size = serializers.CharField()
    color = serializers.CharField()
    total_quantity = serializers.IntegerField()
