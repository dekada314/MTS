"""Serializers for Goods app models."""

from rest_framework import serializers
from goods.models import Categories, Products


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Categories model."""
    
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Categories
        fields = ['id', 'name', 'slug', 'product_count']
        read_only_fields = ['id']
    
    def get_product_count(self, obj):
        """Get the count of products in this category."""
        return obj.products_set.count()


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for Product list view (lightweight)."""
    
    category = serializers.StringRelatedField()
    sell_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Products
        fields = [
            'id', 'name', 'slug', 'price', 'discount', 
            'sell_price', 'quantity', 'category', 'image'
        ]
        read_only_fields = ['id', 'sell_price']
    
    def get_sell_price(self, obj):
        """Calculate selling price after discount."""
        return obj.sell_price()


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for Product detail view (full information)."""
    
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Categories.objects.all(),
        source='category',
        write_only=True
    )
    sell_price = serializers.SerializerMethodField()
    display_id = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Products
        fields = [
            'id', 'display_id', 'name', 'slug', 'description', 
            'image', 'price', 'discount', 'sell_price', 'quantity',
            'in_stock', 'category', 'category_id', 'absolute_url'
        ]
        read_only_fields = ['id', 'display_id', 'sell_price', 'absolute_url', 'in_stock']
    
    def get_sell_price(self, obj):
        """Calculate selling price after discount."""
        return obj.sell_price()
    
    def get_display_id(self, obj):
        """Get formatted display ID."""
        return obj.display_id()
    
    def get_absolute_url(self, obj):
        """Get absolute URL for the product."""
        return obj.get_absolute_url()
    
    def get_in_stock(self, obj):
        """Check if product is in stock."""
        return obj.quantity > 0


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products."""
    
    class Meta:
        model = Products
        fields = [
            'name', 'slug', 'description', 'image', 
            'price', 'discount', 'quantity', 'category'
        ]
    
    def validate_price(self, value):
        """Ensure price is positive."""
        if value < 0:
            raise serializers.ValidationError("Price must be positive.")
        return value
    
    def validate_discount(self, value):
        """Ensure discount is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Discount must be between 0 and 100.")
        return value
    
    def validate_quantity(self, value):
        """Ensure quantity is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value