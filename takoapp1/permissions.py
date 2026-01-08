# permissions.py
from rest_framework.permissions import BasePermission

class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )

class IsNotSales(BasePermission):
    def has_permission(self, request, view):
        return not getattr(request.user, "is_sales_admin", False)
