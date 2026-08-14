from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class ProductSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=True,
    )

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
            'created_at',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'category']
