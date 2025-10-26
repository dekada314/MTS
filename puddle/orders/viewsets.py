"""ViewSets for Orders app API."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema

from orders.models import Order, OrderItem
from orders.serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    OrderItemSerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing orders."""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return orders for current user or all for admin."""
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().prefetch_related('orderitem_set__product')
        return Order.objects.filter(user=user).prefetch_related('orderitem_set__product')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        return OrderDetailSerializer
    
    def get_permissions(self):
        """Admin only for update/delete."""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Create order with current user."""
        serializer.save()
    
    @extend_schema(
        description="Get current user's orders",
        responses={200: OrderListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Get all orders for current user."""
        orders = Order.objects.filter(user=request.user).prefetch_related('orderitem_set__product')
        serializer = OrderListSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        description="Get order statistics",
        responses={200: dict}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def statistics(self, request):
        """Get order statistics (admin only)."""
        from django.db.models import Count, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        stats = {
            'total_orders': Order.objects.count(),
            'orders_today': Order.objects.filter(created_timestamp__date=today).count(),
            'orders_this_week': Order.objects.filter(created_timestamp__date__gte=week_ago).count(),
            'orders_this_month': Order.objects.filter(created_timestamp__date__gte=month_ago).count(),
            'pending_orders': Order.objects.filter(status='В обработке').count(),
            'paid_orders': Order.objects.filter(is_paid=True).count(),
        }
        
        return Response(stats)