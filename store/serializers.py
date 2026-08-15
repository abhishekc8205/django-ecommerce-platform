from rest_framework import serializers
from django.db.models import Avg
from .models import Category, Product, Review, ProductVariant, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'color', 'sku', 'stock', 'price_override', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'caption', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'rating', 'comment', 'verified_purchase', 'created_at']
        read_only_fields = ['id', 'user', 'verified_purchase', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=True,
    )
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'category',
            'category_id',
            'title',
            'description',
            'price',
            'stock',
            'image',
            'owner',
            'average_rating',
            'review_count',
            'variants',
            'images',
            'created_at',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'category', 'average_rating', 'review_count', 'variants', 'images']

    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else None

    def get_review_count(self, obj):
        return obj.reviews.count()
