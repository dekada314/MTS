"""Serializers for Carts app models."""

from rest_framework import serializers
from carts.models import Cart
from goods.serializers import ProductListSerializer


class CartSerializer(serializers.ModelSerializer):
    """Serializer for Cart model."""
    
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Cart.objects.all(),
        source='product',
        write_only=True
    )
    products_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'product', 'product_id', 
            'quantity', 'products_price', 'created_timestamp'
        ]
        read_only_fields = ['id', 'user', 'created_timestamp', 'products_price']
    
    def get_products_price(self, obj):
        """Calculate total price for this cart item."""
        return obj.products_price()
    
    def validate_quantity(self, value):
        """Ensure quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value


class CartCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating cart items."""
    
    class Meta:
        model = Cart
        fields = ['product', 'quantity']
    
    def validate_quantity(self, value):
        """Ensure quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value
    
    def validate(self, attrs):
        """Check product availability."""
        product = attrs['product']
        quantity = attrs['quantity']
        
        if product.quantity < quantity:
            raise serializers.ValidationError({
                'quantity': f'Only {product.quantity} items available in stock.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create or update cart item for the user."""
        user = self.context['request'].user
        product = validated_data['product']
        quantity = validated_data['quantity']
        
        # Check if item already exists in cart
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            cart_item.quantity += quantity
            cart_item.save()
        
        return cart_item


class CartUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating cart quantity."""
    
    class Meta:
        model = Cart
        fields = ['quantity']
    
    def validate_quantity(self, value):
        """Ensure quantity is positive and available."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        
        # Check stock availability
        cart_item = self.instance
        if cart_item.product.quantity < value:
            raise serializers.ValidationError(
                f'Only {cart_item.product.quantity} items available in stock.'
            )
        
        return value


class CartSummarySerializer(serializers.Serializer):
    """Serializer for cart summary."""
    
    total_items = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    items = CartSerializer(many=True)