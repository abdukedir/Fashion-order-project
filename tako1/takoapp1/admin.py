# admin.py
from django.contrib import admin
from .models import *

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "status", "created_at", "display_items")

    def display_items(self, obj):
        # Access items via obj.cart.items
        if obj.cart:
            return ", ".join([
                f"{item.product.name} ({item.color}, {item.size}, qty: {item.quantity})"
                for item in obj.cart.items.all()
            ])
        return "-"
    
    display_items.short_description = "Items"
admin.site.register(Product)
admin.site.register(User)
admin.site.register(PasswordResetOTP)