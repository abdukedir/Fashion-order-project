from django.urls import path
from .views import (
    ProductCreateAPIView,
    ProductListAPIView,
    ProductStatusUpdateAPIView,
    OrderCreateAPIView,
    UpdateOrderStatusAPIView,
    OrderListAPIView,
    ConfirmedOrdersReportAPIView,
    DeliveredOrdersTodayAPIView,
    DeliveredOrdersWeekAPIView,
    DeliveredOrdersMonthAPIView,
    CreateSalesUserAPIView,
)

urlpatterns = [
    # =========================
    # PRODUCTS
    # =========================
    path("products/", ProductListAPIView.as_view(), name="product-list"),
    path("products/create/", ProductCreateAPIView.as_view(), name="product-create"),
    path("products/<int:pk>/status/", ProductStatusUpdateAPIView.as_view(), name="product-status-update"),

    # =========================
    # ORDERS
    # =========================
    path("orders/", OrderListAPIView.as_view(), name="order-list"),
    path("orders/create/", OrderCreateAPIView.as_view(), name="order-create"),
    path("orders/<int:pk>/update-status/", UpdateOrderStatusAPIView.as_view(), name="order-update-status"),

    # =========================
    # CONFIRMED ORDERS REPORTS
    # =========================
    path("reports/confirmed/", ConfirmedOrdersReportAPIView.as_view(), name="confirmed-orders-report"),

    # =========================
    # DELIVERED ORDERS REPORTS
    # =========================
    path("reports/delivered/today/", DeliveredOrdersTodayAPIView.as_view(), name="delivered-orders-today"),
    path("reports/delivered/week/", DeliveredOrdersWeekAPIView.as_view(), name="delivered-orders-week"),
    path("reports/delivered/month/", DeliveredOrdersMonthAPIView.as_view(), name="delivered-orders-month"),

    # =========================
    # CREATE SALES USER
    # =========================
    path("users/create-sales/", CreateSalesUserAPIView.as_view(), name="create-sales-user"),
]
