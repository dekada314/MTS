"""Serializers for Orders app models."""

from rest_framework import serializers
from orders.models import Order, OrderItem
from goods.serializers import ProductListSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model."""
    
    product = ProductListSerializer(read_only=True)
    products_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'name', 
            'price', 'quantity', 'products_price', 'created_timestamp'
        ]
        read_only_fields = ['id', 'order', 'created_timestamp', 'products_price']
    
    def get_products_price(self, obj):
        """Calculate total price for this order item."""
        return obj.products_price()


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for Order list view."""
    
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'created_timestamp', 'phone_number', 
            'requires_delivery', 'is_paid', 'status',
            'total_items', 'total_price'
        ]
        read_only_fields = ['id', 'created_timestamp']
    
    def get_total_items(self, obj):
        """Get total number of items in order."""
        return obj.orderitem_set.total_quantity()
    
    def get_total_price(self, obj):
        """Get total price of order."""
        return obj.orderitem_set.total_price()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for Order detail view."""
    
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_info', 'created_timestamp', 
            'phone_number', 'requires_delivery', 'delivery_address',
            'payment_on_get', 'is_paid', 'status',
            'items', 'total_items', 'total_price'
        ]
        read_only_fields = ['id', 'user', 'created_timestamp']
    
    def get_total_items(self, obj):
        """Get total number of items in order."""
        return obj.orderitem_set.total_quantity()
    
    def get_total_price(self, obj):
        """Get total price of order."""
        return obj.orderitem_set.total_price()
    
    def get_user_info(self, obj):
        """Get basic user information."""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email,
                'full_name': f"{obj.user.first_name} {obj.user.last_name}".strip()
            }
        return None


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders."""
    
    class Meta:
        model = Order
        fields = [
            'phone_number', 'requires_delivery', 
            'delivery_address', 'payment_on_get'
        ]
    
    def validate(self, attrs):
        """Validate delivery address if delivery is required."""
        if attrs.get('requires_delivery') and not attrs.get('delivery_address'):
            raise serializers.ValidationError({
                'delivery_address': 'Delivery address is required when delivery is requested.'
            })
        return attrs
    
    def create(self, validated_data):
        """Create order from user's cart."""
        from carts.models import Cart
        from django.db import transaction
        
        user = self.context['request'].user
        
        # Check if user can place order (email verified)
        if not user.can_place_order():
            raise serializers.ValidationError({
                'error': 'Email verification required to place orders.'
            })
        
        # Get user's cart items
        cart_items = Cart.objects.filter(user=user).select_related('product')
        
        if not cart_items.exists():
            raise serializers.ValidationError({'error': 'Cart is empty.'})
        
        # Create order with transaction
        with transaction.atomic():
            # Create order
            order = Order.objects.create(
                user=user,
                **validated_data
            )
            
            # Create order items from cart
            for cart_item in cart_items:
                product = cart_item.product
                
                # Check stock availability
                if product.quantity < cart_item.quantity:
                    raise serializers.ValidationError({
                        'error': f'Insufficient stock for {product.name}. Available: {product.quantity}'
                    })
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    name=product.name,
                    price=product.sell_price(),
                    quantity=cart_item.quantity
                )
                
                # Reduce product quantity
                product.quantity -= cart_item.quantity
                product.save()
            
            # Clear cart
            cart_items.delete()
        
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status (admin only)."""
    
    class Meta:
        model = Order
        fields = ['status', 'is_paid']