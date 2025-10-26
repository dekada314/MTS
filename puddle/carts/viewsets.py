"""ViewSets for Carts app API."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from carts.models import Cart
from carts.serializers import (
    CartSerializer,
    CartCreateSerializer,
    CartUpdateSerializer,
    CartSummarySerializer
)


class CartViewSet(viewsets.ModelViewSet):
    """ViewSet for managing shopping cart."""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return cart items for current user."""
        return Cart.objects.filter(user=self.request.user).select_related('product', 'product__category')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return CartCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CartUpdateSerializer
        return CartSerializer
    
    def perform_create(self, serializer):
        """Save cart item with current user."""
        serializer.save(user=self.request.user)
    
    @extend_schema(
        description="Get cart summary with total items and price",
        responses={200: CartSummarySerializer}
    )
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get cart summary."""
        cart_items = self.get_queryset()
        
        total_quantity = cart_items.total_quantity()
        total_price = cart_items.total_price()
        
        serializer = CartSummarySerializer({
            'total_items': total_quantity,
            'total_price': total_price,
            'items': cart_items
        })
        
        return Response(serializer.data)
    
    @extend_schema(
        description="Clear all items from cart",
        responses={204: None}
    )
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all cart items for current user."""
        deleted_count = self.get_queryset().delete()[0]
        return Response(
            {'message': f'{deleted_count} items removed from cart'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @extend_schema(
        description="Add item to cart or update quantity",
        request=CartCreateSerializer,
        responses={201: CartSerializer}
    )
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart (alternative to create)."""
        serializer = CartCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            cart_item = serializer.save()
            return Response(
                CartSerializer(cart_item, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)