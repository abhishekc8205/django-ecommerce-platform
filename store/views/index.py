"""Views for product listing and browsing."""
from django.shortcuts import render
from django.db.models import Q, Avg, Case, IntegerField, Value, When
from django.core.paginator import Paginator

from store.models import Product, Category


def index_view(request):
    """Display product listing with filters and search."""
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    sort = request.GET.get('sort', 'newest')
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()

    products = Product.objects.select_related('category').prefetch_related(
        'reviews'
    )

    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    products = products.annotate(
        average_rating=Avg('reviews__rating'),
        has_reviews=Case(
            When(reviews__isnull=False, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
    )

    if sort == 'price_low':
        products = products.order_by('price', '-created_at', '-id')
    elif sort == 'price_high':
        products = products.order_by('-price', '-created_at', '-id')
    elif sort == 'rating':
        products = products.order_by(
            '-has_reviews', '-average_rating', '-created_at', '-id'
        )
    else:
        products = products.order_by('-created_at', '-id')

    categories = Category.objects.all()

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'query': query,
        'category_slug': category_slug,
        'sort': sort,
        'min_price': min_price,
        'max_price': max_price,
        'categories': categories,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj
    }
    return render(request, 'index.html', context)
