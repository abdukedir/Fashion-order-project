from django.urls import path
from .views import *

urlpatterns = [
    # Products
    path("products/", ProductListAPIView.as_view()),
    path("admin/product/create/", ProductCreateAPIView.as_view()),

    # Cart
    path("cart/create/", GetOrCreateCartAPIView.as_view()),
    path("cart/item/add/", CartItemCreateAPIView.as_view()),
    path("cart/", CartAPIView.as_view()),

    # Orders
    path("order/create/", OrderCreateAPIView.as_view()),
    path("order/upload-payment/<int:order_id>/", UploadPaymentAPIView.as_view()),
    path("admin/order/confirm/<int:pk>/", ConfirmOrderAPIView.as_view()),

    # Analytics
    path("admin/orders/weekly-total/", WeeklyOrdersAPIView.as_view()),

    # Sales user
    path("admin/create-sales-user/", CreateSalesUserAPIView.as_view()),
    path("confirm/<int:pk>/",Confirm.as_view()),
]
