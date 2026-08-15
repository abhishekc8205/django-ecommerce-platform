"""API ViewSets for products and categories."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from store.models import Category, Product, ProductVariant, ProductImage
from store.permissions import IsSeller, IsOwner
from store.serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'


class ProductViewSet(viewsets.ModelViewSet):
    """Full CRUD ViewSet for products."""
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Product.objects.select_related(
            'category', 'owner'
        ).prefetch_related(
            'variants', 'images', 'reviews'
        ).order_by('-created_at', '-id')

    def get_permissions(self):
        """Override permissions by action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsSeller()]

    def perform_create(self, serializer):
        """Automatically set owner to current user."""
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """Verify user owns the product before updating."""
        product = self.get_object()
        if product.owner_id != self.request.user.id:
            self.permission_denied(
                self.request,
                message="You do not have permission to modify this product."
            )
        serializer.save()

    def perform_destroy(self, instance):
        """Verify user owns the product before deleting."""
        if instance.owner_id != self.request.user.id:
            self.permission_denied(
                self.request,
                message="You do not have permission to delete this product."
            )
        instance.delete()

    @action(detail=True, methods=['get'])
    def variants(self, request, pk=None):
        """Get all variants for a product."""
        product = self.get_object()
        variants = product.variants.all().order_by('size', 'color')
        from store.serializers import ProductVariantSerializer
        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """Get all gallery images for a product."""
        product = self.get_object()
        images = product.images.all().order_by('order')
        from store.serializers import ProductImageSerializer
        serializer = ProductImageSerializer(images, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for a product."""
        product = self.get_object()
        reviews = product.reviews.all()
        from store.serializers import ReviewSerializer
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
