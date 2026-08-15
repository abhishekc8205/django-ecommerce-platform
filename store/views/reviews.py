"""Template views for reviews and product details."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import render, redirect, get_object_or_404

from store.models import Product, Review, OrderItem
from store.forms import ReviewForm


def product_detail(request, product_id):
    """Display product details with variants, images, and reviews."""
    product = get_object_or_404(Product, id=product_id)
    variants = product.variants.all().order_by('size', 'color')

    reviews = product.reviews.all()
    review_count = reviews.count()
    average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    can_manage = (
        request.user.is_authenticated and
        request.user.is_seller and
        product.owner_id == request.user.id
    )

    return render(request, 'product_detail.html', {
        'product': product,
        'variants': variants,
        'can_manage_product': can_manage,
        'gallery_images': product.images.all(),
        'reviews': reviews,
        'review_count': review_count,
        'average_rating': average_rating,
        'user_review': user_review,
    })


@login_required
def add_review(request, product_id):
    """Add product review."""
    product = get_object_or_404(Product, id=product_id)

    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, 'You already reviewed this product.')
        return redirect('product_detail', product_id=product.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.verified_purchase = OrderItem.objects.filter(
                order__user=request.user,
                order__is_paid=True,
                product=product,
            ).exists()
            review.save()
            messages.success(request, 'Review posted!')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ReviewForm()

    return render(request, 'add_review.html', {
        'form': form,
        'product': product,
    })


@login_required
def delete_review(request, review_id):
    """Delete review."""
    review = get_object_or_404(Review, id=review_id)
    product_id = review.product_id

    if request.user != review.user and not request.user.is_superuser:
        messages.error(request, 'You can only delete your own review.')
        return redirect('product_detail', product_id=product_id)

    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review removed.')

    return redirect('product_detail', product_id=product_id)
