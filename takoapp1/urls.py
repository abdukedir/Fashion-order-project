from django.urls import path
from .views import *
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # ====================== Product URLs ======================
    path("products/", ProductListAPIView.as_view(), name="product-list"),  # List all active products
    path("admin/product/create/", ProductCreateAPIView.as_view(), name="product-create"),  # Admin creates product
    path("confirm/<int:pk>/", Confirm.as_view(), name="product-confirm"),  # Retrieve/Update/Delete a single product

    # ====================== Order URLs ======================
    path("order/create/", OrderCreateAPIView.as_view(), name="order-create"),  # Customer creates an order
    path("admin/orders/", OrderListAPIView.as_view(), name="order-list"),  # Admin lists all orders
    path("admin/order/confirm/<int:pk>/", ConfirmOrderAPIView.as_view(), name="order-confirm"),  # Admin confirms order

    # ====================== Analytics / Reports ======================
    # path("admin/orders/weekly-total/", WeeklyOrdersAPIView.as_view(), name="weekly-orders"),  # Total orders in last week
    path("reports/confirmed-orders/today/", ConfirmedOrdersTodayAPIView.as_view(), name="confirmed-orders-today"),  # Confirmed orders today with optional filters ?size= & ?color=
    path("reports/confirmed-orders/week/", ConfirmedOrdersWeekAPIView.as_view(), name="confirmed-orders-week"),  # Confirmed orders in last 7 days
    path("reports/confirmed-orders/month/", ConfirmedOrdersMonthAPIView.as_view(), name="confirmed-orders-month"),  # Confirmed orders in last 30 days
    # you can use this like 
    #GET http://127.0.0.1:8000/reports/confirmed-orders/today/total/?size=M

    path("reports/confirmed-orders/week/total/", ConfirmedOrdersWeekTotalAPIView.as_view(), name="confirmed-orders-week-total"),
    path("reports/confirmed-orders/today/total/", ConfirmedOrdersTodayTotalAPIView.as_view(), name="confirmed-orders-today-total"),
    path("reports/confirmed-orders/month/total/", ConfirmedOrdersMonthTotalAPIView.as_view(), name="confirmed-orders-month-total"),

    # ====================== Sales User ======================
    path("admin/create-sales-user/", CreateSalesUserAPIView.as_view(), name="create-sales-user"),  # Create sales admin user

    # ====================== Auth Token ======================
    path("api-token-auth/", obtain_auth_token, name="api-token-auth"),  # Obtain auth token for users
]
