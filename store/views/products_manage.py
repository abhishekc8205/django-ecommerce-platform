"""Views for seller product management."""
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from store.models import Product, ProductVariant, ProductImage
from store.forms import ProductForm, ProductVariantForm, ProductImageForm

logger = logging.getLogger(__name__)


def _user_can_manage_product(user, product):
    """Check if user can manage a product."""
    return (
        user.is_authenticated and
        user.is_seller and
        product.owner_id == user.id
    )


def _get_owned_product_or_redirect(request, product_id, error_msg):
    """Get product or redirect with error message."""
    product = get_object_or_404(Product, id=product_id)
    if not _user_can_manage_product(request.user, product):
        messages.error(request, error_msg)
        logger.warning(
            'Unauthorized product access: user=%s product=%s',
            request.user.pk, product.id
        )
        return None
    return product


@login_required
def add_product(request):
    """Add new product."""
    if not request.user.is_seller:
        messages.error(request, 'Become a seller first.')
        return redirect('index')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.save()
            messages.success(request, 'Product added.')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductForm()

    return render(request, 'add_product.html', {'form': form})


@login_required
def edit_product(request, product_id):
    """Edit existing product."""
    product = _get_owned_product_or_redirect(
        request,
        product_id,
        'You can only edit your own products.'
    )
    if product is None:
        return redirect('index')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated.')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductForm(instance=product)

    return render(
        request, 'add_product.html',
        {'form': form, 'editing': True, 'product': product}
    )


@login_required
def delete_product(request, product_id):
    """Delete product."""
    product = _get_owned_product_or_redirect(
        request,
        product_id,
        'You can only delete your own products.'
    )
    if product is None:
        return redirect('index')

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('index')

    return render(request, 'confirm_delete.html', {'object': product})


@login_required
def add_variant(request, product_id):
    """Add product variant."""
    product = _get_owned_product_or_redirect(
        request,
        product_id,
        'You can only add variants to your products.'
    )
    if product is None:
        return redirect('index')

    if request.method == 'POST':
        form = ProductVariantForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            messages.success(
                request,
                f'Variant "{variant.display_name}" added.'
            )
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductVariantForm()

    return render(request, 'add_variant.html', {
        'form': form,
        'product': product,
    })


@login_required
def add_product_image(request, product_id):
    """Add product gallery image."""
    product = _get_owned_product_or_redirect(
        request,
        product_id,
        'You can only add images to your products.'
    )
    if product is None:
        return redirect('index')

    if request.method == 'POST':
        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.product = product
            image.save()
            messages.success(request, 'Gallery image added.')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductImageForm()

    return render(request, 'add_product_image.html', {
        'form': form,
        'product': product,
    })


@login_required
def delete_product_image(request, image_id):
    """Delete product gallery image."""
    image = get_object_or_404(ProductImage, id=image_id)
    product = image.product

    if not _user_can_manage_product(request.user, product):
        messages.error(request, 'You can only delete your own images.')
        return redirect('index')

    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image removed.')

    return redirect('product_detail', product_id=product.id)
