"""Template views for cart management."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from store.models import Cart, CartItem, Product, ProductVariant


@login_required
def view_cart(request):
    """Display user's shopping cart."""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all().select_related('product', 'variant')
    total_price = sum(item.subtotal for item in cart_items)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'cart.html', context)


@login_required
def add_to_cart(request, product_id):
    """Add product to cart."""
    product = get_object_or_404(Product, id=product_id)
    variant = None
    variant_id = request.GET.get('variant')

    if variant_id:
        variant = ProductVariant.objects.filter(
            id=variant_id, product=product
        ).first()

    stock_available = variant.stock if variant else product.stock
    if stock_available <= 0:
        messages.error(request, 'This item is currently out of stock.')
        return redirect('product_detail', product_id=product.id)

    cart, _ = Cart.objects.get_or_create(user=request.user)

    if variant:
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart, product=product, variant=variant
        )
    else:
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart, product=product, variant__isnull=True
        )

    if not item_created:
        if cart_item.quantity + 1 > stock_available:
            messages.error(request, 'Not enough stock available.')
            return redirect('cart')
        cart_item.quantity += 1
        cart_item.save()

    variant_label = f" ({variant.display_name})" if variant else ""
    messages.success(
        request,
        f"Added {product.title}{variant_label} to your cart!"
    )
    return redirect('index')


@login_required
def increment_cart_item(request, item_id):
    """Increase quantity of cart item."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.quantity += 1
    cart_item.save()
    messages.success(
        request,
        f"Increased quantity of {cart_item.product.title}!"
    )
    return redirect('cart')


@login_required
def decrement_cart_item(request, item_id):
    """Decrease quantity of cart item."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        messages.success(
            request,
            f"Decreased quantity of {cart_item.product.title}!"
        )
    else:
        cart_item.delete()
        messages.warning(
            request,
            f"Removed {cart_item.product.title} from your cart!"
        )

    return redirect('cart')


@login_required
def delete_cart_item(request, item_id):
    """Remove item from cart."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_title = cart_item.product.title
    cart_item.delete()
    messages.warning(request, f"Removed {product_title} from your cart!")
    return redirect('cart')
