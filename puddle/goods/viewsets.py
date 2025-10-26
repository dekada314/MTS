"""ViewSets for Goods app API."""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from goods.models import Categories, Products
from goods.serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing categories."""
    
    queryset = Categories.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'id']
    ordering = ['id']
    
    def get_permissions(self):
        """Admin only for create/update/delete."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return super().get_permissions()
    
    @extend_schema(
        description="Get all products in this category",
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get all products in a specific category."""
        category = self.get_object()
        products = Products.objects.filter(category=category)
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for managing products."""
    
    queryset = Products.objects.select_related('category').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'category__slug']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'created', 'discount']
    ordering = ['id']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def get_permissions(self):
        """Admin only for create/update/delete."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return super().get_permissions()
    
    @extend_schema(
        description="Get products with active discounts",
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def discounted(self, request):
        """Get all products with discounts."""
        products = self.queryset.filter(discount__gt=0, quantity__gt=0)
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        description="Get products that are in stock",
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def in_stock(self, request):
        """Get all products that are in stock."""
        products = self.queryset.filter(quantity__gt=0)
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        description="Search products by name or description",
        parameters=[
            OpenApiParameter(name='q', description='Search query', required=True, type=str)
        ],
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search products by query."""
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        products = self.queryset.filter(name__icontains=query) | \
                   self.queryset.filter(description__icontains=query)
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)