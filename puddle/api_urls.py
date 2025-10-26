"""API URL Configuration."""

from rest_framework.routers import DefaultRouter
from django.urls import path, include

from goods.viewsets import CategoryViewSet, ProductViewSet
from users.viewsets import UserViewSet
from carts.viewsets import CartViewSet
from orders.viewsets import OrderViewSet

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'users', UserViewSet, basename='user')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),  # Login/logout for browsable API
]