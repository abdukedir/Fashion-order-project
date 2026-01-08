from django.urls import path
from .views import (
    # Products
    ProductCreateAPIView,
    ProductStatusUpdateAPIView,
    ProductListAPIView,
    
    # Orders
    OrderCreateAPIView,
    UpdateOrderStatusAPIView,
    OrderListAPIView,
    
    # Reports
    ConfirmedOrdersReportAPIView,
    DeliveredOrdersTodayAPIView,
    DeliveredOrdersWeekAPIView,
    DeliveredOrdersMonthAPIView,
    
    # Notifications
    NotificationListAPIView,
    
    # Users
    CreateSalesUserAPIView,
)

urlpatterns = [
    # =======================
    # Products
    # =======================
    path("products/", ProductListAPIView.as_view(), name="product-list"),
    path("admin/product/create/", ProductCreateAPIView.as_view(), name="product-create"),
    path("admin/product/<int:pk>/status/", ProductStatusUpdateAPIView.as_view(), name="product-status-update"),

    # =======================
    # Orders
    # =======================
    path("orders/", OrderListAPIView.as_view(), name="order-list"),
    path("order/create/", OrderCreateAPIView.as_view(), name="order-create"),
    path("order/<int:pk>/update-status/", UpdateOrderStatusAPIView.as_view(), name="order-status-update"),

    # =======================
    # Reports
    # =======================
    path("reports/confirmed-orders/", ConfirmedOrdersReportAPIView.as_view(), name="confirmed-orders-report"),
    path("reports/delivered/today/", DeliveredOrdersTodayAPIView.as_view(), name="delivered-orders-today"),
    path("reports/delivered/week/", DeliveredOrdersWeekAPIView.as_view(), name="delivered-orders-week"),
    path("reports/delivered/month/", DeliveredOrdersMonthAPIView.as_view(), name="delivered-orders-month"),

    # =======================
    # Notifications
    # =======================
    path("notifications/", NotificationListAPIView.as_view(), name="notifications-list"),

    # =======================
    # Users
    # =======================
    path("admin/sales-user/create/", CreateSalesUserAPIView.as_view(), name="create-sales-user"),
]
