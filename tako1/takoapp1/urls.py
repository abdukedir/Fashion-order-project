from django.urls import path
from .views import *
from rest_framework.authtoken.views import obtain_auth_token
urlpatterns = [
    # Products to display the products inserted to the dataase by the admin
    path("products/", ProductListAPIView.as_view()),
    #to create the product tis is actiolly the admins role
    path("admin/product/create/", ProductCreateAPIView.as_view()),

    # Cart to create cart api just customer users create carts and add items to the cart
    #path("cart/create/", GetOrCreateCartAPIView.as_view()),

    #path("cart/item/add/", CartItemCreateAPIView.as_view()),
    #this is to look what items are inserted to the cart
    #path("cart/", CartAPIView.as_view()),

    # Orders this api is for ordering the items in the cart
    path("order/create/", OrderCreateAPIView.as_view()),
    #this is the api to upload screensheet of the payment when they order
    #path("order/upload-payment/<int:order_id>/", UploadPaymentAPIView.as_view()),
    path("admin/orders/", OrderListAPIView.as_view()),

    path("admin/order/confirm/<int:pk>/", ConfirmOrderAPIView.as_view()),

    # Analytics
    path("admin/orders/weekly-total/", WeeklyOrdersAPIView.as_view()),
    path("auth/forgot-password/", ForgotPasswordAPIView.as_view()),
    path("auth/reset-password/", ResetPasswordAPIView.as_view()),

    # Sales user
    path("admin/create-sales-user/", CreateSalesUserAPIView.as_view()),
    path("confirm/<int:pk>/",Confirm.as_view()),
    path("api-token-auth/", obtain_auth_token),

    #path to look the ordered items
    
]
