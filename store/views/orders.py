"""Template views for orders and checkout."""
import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.crypto import get_random_string

import stripe

from store.models import Cart, Order, OrderItem, Product

logger = logging.getLogger(__name__)


def _user_can_manage_product(user, product):
    """Check if user can manage a product."""
    return (
        user.is_authenticated and
        user.is_seller and
        product.owner_id == user.id
    )


@login_required
def checkout_initiate(request):
    """Initialize order from cart."""
    if request.method != 'POST':
        return redirect('cart')

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = list(cart.items.select_related('product', 'variant').all())

    if not cart_items:
        messages.warning(request, "Your cart is empty!")
        return redirect('cart')

    full_name = request.POST.get('full_name', '').strip()
    address = request.POST.get('address', '').strip()

    if not full_name or not address:
        messages.error(request, "Please fill out all shipping fields.")
        return redirect('cart')

    stock_shortages = []
    for item in cart_items:
        available_stock = (
            item.variant.stock if item.variant_id and item.variant
            else item.product.stock
        )
        if item.quantity > available_stock:
            label = (
                f"{item.product.title} ({item.variant.display_name})"
                if item.variant
                else item.product.title
            )
            stock_shortages.append(label)

    if stock_shortages:
        messages.error(
            request,
            f"We couldn't create your order because the following item(s) are short on stock: {', '.join(stock_shortages)}"
        )
        return redirect('cart')

    total_price = sum(item.subtotal for item in cart_items)
    payment_method = request.POST.get('payment_method', 'stripe')

    order = Order.objects.create(
        user=request.user,
        full_name=full_name,
        address=address,
        total_price=total_price,
        payment_method=payment_method,
    )

    for item in cart_items:
        locked_price = (
            item.variant.get_price if item.variant_id and item.variant
            else item.product.price
        )
        OrderItem.objects.create(
            order=order,
            product=item.product,
            variant=item.variant,
            quantity=item.quantity,
            price=locked_price
        )

    cart.items.all().delete()

    if payment_method == 'cod':
        try:
            order.is_paid = True
            order.order_status = 'processing'
            order.save(update_fields=['is_paid', 'order_status'])
            order.deduct_stock_once()
        except ValueError as exc:
            order.delete()
            messages.error(request, str(exc))
            return redirect('cart')

        messages.success(request, "Order placed with Cash on Delivery!")
        return redirect('order_detail', order_id=order.order_id)

    messages.success(request, "Order initiated. Complete your payment.")
    return redirect('checkout_page', order_id=order.order_id)


@login_required
def checkout_page(request, order_id):
    """Display checkout/payment page."""
    order = get_object_or_404(
        Order, order_id=order_id, user=request.user, is_paid=False
    )
    order_items = order.items.all().select_related('product')

    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'checkout.html', context)


@login_required
def create_checkout_session(request, order_id):
    """Create Stripe checkout session."""
    order = get_object_or_404(
        Order, order_id=order_id, user=request.user, is_paid=False
    )

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_configured = (
        bool(settings.STRIPE_SECRET_KEY) and
        'placeholder' not in settings.STRIPE_SECRET_KEY
    )

    line_items = []
    for item in order.items.all():
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': item.product.title},
                'unit_amount': int(item.price * 100),
            },
            'quantity': item.quantity,
        })

    try:
        if not stripe_configured:
            fake_session_id = f"dev_{get_random_string(12)}"
            order.stripe_session_id = fake_session_id
            order.save()
            return redirect(
                f"{reverse('payment_status')}?session_id={fake_session_id}"
            )

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=(
                request.build_absolute_uri(reverse('payment_status')) +
                '?session_id={CHECKOUT_SESSION_ID}'
            ),
            cancel_url=request.build_absolute_uri(
                reverse('checkout_page', args=[order.order_id])
            ),
            customer_email=request.user.email,
            metadata={'order_id': order.order_id}
        )

        order.stripe_session_id = session.id
        order.save()
        return redirect(session.url, code=303)

    except Exception as e:
        messages.error(request, f"Stripe failed: {str(e)}")
        return redirect('checkout_page', order_id=order.order_id)


@login_required
def payment_status(request):
    """Check payment status."""
    session_id = request.GET.get('session_id')

    if not session_id:
        messages.warning(request, "No transaction found.")
        return redirect('index')

    order = get_object_or_404(Order, stripe_session_id=session_id, user=request.user)

    if session_id.startswith('dev_'):
        order.mark_paid_and_update_status()
        try:
            order.deduct_stock_once()
        except ValueError as exc:
            messages.error(request, str(exc))
        context = {'order': order, 'status': 'success'}
        return render(request, 'payment_status.html', context)

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid' or session.status == 'complete':
            order.mark_paid_and_update_status()
            try:
                order.deduct_stock_once()
            except ValueError as exc:
                messages.error(request, str(exc))
            context = {'order': order, 'status': 'success'}
        else:
            context = {'order': order, 'status': 'failed'}

    except Exception as e:
        context = {'order': order, 'status': 'failed', 'error': str(e)}

    return render(request, 'payment_status.html', context)


@login_required
def dashboard_view(request):
    """Buyer and seller dashboard."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    total_orders = orders.count()
    total_spent = (
        Order.objects.filter(user=request.user, is_paid=True)
        .aggregate(total=Sum('total_price'))['total'] or 0
    )
    pending_orders = Order.objects.filter(
        user=request.user, is_paid=False
    ).count()

    seller_products = Product.objects.filter(
        owner=request.user
    ).order_by('-created_at', '-id')

    seller_order_items = (
        OrderItem.objects
        .filter(product__owner=request.user)
        .select_related('order', 'product')
        .order_by('-order__created_at', '-id')
    )
    paid_seller_items = [item for item in seller_order_items if item.order.is_paid]
    seller_revenue = sum(item.subtotal for item in paid_seller_items)
    seller_units_sold = sum(item.quantity for item in paid_seller_items)
    seller_pending_sales = sum(
        1 for item in seller_order_items if not item.order.is_paid
    )

    context = {
        'orders': orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'pending_orders': pending_orders,
        'seller_products': seller_products,
        'seller_product_count': seller_products.count(),
        'seller_recent_sales': seller_order_items[:10],
        'seller_revenue': seller_revenue,
        'seller_units_sold': seller_units_sold,
        'seller_pending_sales': seller_pending_sales,
    }
    return render(request, 'dashboard.html', context)


@login_required
def order_detail_view(request, order_id):
    """Display order details."""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    order_items = order.items.all().select_related('product')

    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'order_detail.html', context)


@login_required
def seller_orders_view(request):
    """Seller order management."""
    if not request.user.is_seller:
        messages.error(request, "Become a seller first.")
        return redirect('index')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('order_status', '').strip()
        order = get_object_or_404(Order, order_id=order_id)

        has_owned_items = OrderItem.objects.filter(
            order=order, product__owner=request.user
        ).exists()

        if not has_owned_items:
            logger.warning(
                'Unauthorized update: user=%s order=%s',
                request.user.pk, order.id
            )
            messages.error(request, 'Unauthorized.')
            return redirect('seller_orders')

        valid_statuses = [
            choice[0]
            for choice in Order._meta.get_field('order_status').choices
        ]
        if new_status not in valid_statuses:
            messages.error(request, 'Invalid status.')
            return redirect('seller_orders')

        order.order_status = new_status
        order.save(update_fields=['order_status'])
        messages.success(request, f'Status updated to {new_status}.')
        return redirect('seller_orders')

    seller_orders = Order.objects.filter(
        items__product__owner=request.user
    ).distinct().order_by('-created_at')

    seller_rows = []
    for order in seller_orders:
        seller_items = list(
            OrderItem.objects
            .filter(order=order, product__owner=request.user)
            .select_related('product', 'order')
            .order_by('id')
        )
        seller_rows.append({
            'order': order,
            'items': seller_items,
            'total': sum(item.subtotal for item in seller_items),
        })

    return render(request, 'seller_orders.html', {
        'seller_orders': seller_rows,
        'order_status_choices': (
            Order._meta.get_field('order_status').choices
        ),
    })
