from rest_framework import serializers
from .models import (
    Product,
    ProductImage,
    Cart,
    CartItem,
    Order
)
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "is_read", "created_at"]

# ======================
# PRODUCT IMAGE SERIALIZER
# ======================
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = [
            "id",
            "image",
            "is_primary",
        ]


# ======================
# PRODUCT SERIALIZER (WITH MULTIPLE IMAGES)
# ======================
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "available_colors",
            "available_sizes",
            "tshirt_type",
            "is_active",
            "created_at",
            "images",
        ]


# ======================
# PRODUCT CREATE / UPDATE SERIALIZER
# (Handles multiple image uploads)
# ======================
class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "available_colors",
            "available_sizes",
            "tshirt_type",
            "is_active",
            "images",
        ]

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        product = Product.objects.create(**validated_data)

        for index, image in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(index == 0)  # first image = main image
            )

        return product

    def update(self, instance, validated_data):
        images = validated_data.pop("images", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if images is not None:
            instance.images.all().delete()
            for index, image in enumerate(images):
                ProductImage.objects.create(
                    product=instance,
                    image=image,
                    is_primary=(index == 0)
                )

        return instance


# ======================
# CART ITEM SERIALIZER
# ======================
class CartItemSerializer(serializers.ModelSerializer):
    total_price = serializers.ReadOnlyField()
    product = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = "__all__"


# ======================
# CART SERIALIZER
# ======================
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "session_id", "items"]


# ======================
# ORDER SERIALIZER
# ======================
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


# ======================
# CONFIRMED ORDER REPORT SERIALIZER
# ======================
class ConfirmedOrderStatsSerializer(serializers.Serializer):
    """
    Used for aggregated confirmed order reports
    (today / week / month)
    """

    product_name = serializers.CharField()
    size = serializers.CharField()
    color = serializers.CharField()
    total_quantity = serializers.IntegerField()
