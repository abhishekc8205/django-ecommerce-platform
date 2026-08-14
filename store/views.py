import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.crypto import get_random_string

import stripe
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from store.models import Cart, CartItem, Order, OrderItem, Product, ProductVariant, ProductImage, Review, Category
from .forms import ProductForm, ProductVariantForm, ProductImageForm, ReviewForm
from .serializers import CategorySerializer, ProductSerializer
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
from django.db.models import Avg, Case, IntegerField, Sum, Value, When

logger = logging.getLogger(__name__)


def user_can_manage_product(user, product):
    return user.is_authenticated and user.is_seller and product.owner_id == user.id


def require_seller(request):
    if request.user.is_seller:
        return True
    messages.error(request, "Become a seller before managing products.")
    return False


def get_owned_product_or_redirect(request, product_id, error_message):
    product = get_object_or_404(Product, id=product_id)
    if not user_can_manage_product(request.user, product):
        messages.error(request, error_message)
        logger.warning(
            "Unauthorized product management attempt: user=%s product=%s owner=%s",
            request.user.pk,
            product.id,
            product.owner_id,
        )
        return None
    return product

def index_view(request):
    # Get query parameters
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    sort = request.GET.get('sort', 'newest')
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    
    # Start with all products
    # Use a stable ordering so paginated results do not move between pages.
    products = Product.objects.select_related('category')
    
    # Filter by search query
    if query:
        products = products.filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(category__name__icontains=query)
        )
    
    # Filter by category slug
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
        products = products.order_by('-has_reviews', '-average_rating', '-created_at', '-id')
    else:
        products = products.order_by('-created_at', '-id')
    
    # Get all categories for dropdown
    categories = Category.objects.all()
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 items per page
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'products': page_obj,  # This is a Page object
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

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def api_categories(request):
    from .models import Category
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def api_products(request):
    if request.method == 'GET':
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    if not request.user.is_authenticated or not request.user.is_seller:
        return Response({'detail': 'Only authenticated seller users may add products.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = ProductSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        product = serializer.save(owner=request.user)
        return Response(ProductSerializer(product, context={'request': request}).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def api_product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'GET':
        serializer = ProductSerializer(product, context={'request': request})
        return Response(serializer.data)

    if not request.user.is_authenticated:
        return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

    if not user_can_manage_product(request.user, product):
        return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ['PUT', 'PATCH']:
        serializer = ProductSerializer(product, data=request.data, partial=(request.method == 'PATCH'), context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@login_required
def add_to_cart(request, product_id):
    # 1. Grab the product from the shelf. If the product ID doesn't exist, throw a 404 Not Found error.
    product = get_object_or_404(Product, id=product_id)

    # ==============================================================================
    # Variant support (NEW FEATURE - does not break old behavior)
    # ------------------------------------------------------------------------------
    # Old URL: /add-to-cart/5/  -> adds the parent product (no variant).
    # New URL: /add-to-cart/5/?variant=12 -> adds the chosen ProductVariant.
    # If the product has no variants OR no variant is passed, we fall back to
    # the parent product exactly like before.
    # ==============================================================================
    variant = None  # default = no variant
    variant_id = request.GET.get('variant')  # ?variant=<id> from product_detail.html
    if variant_id:
        # Try to fetch the variant. We use filter().first() instead of
        # get_object_or_404 so a bad/wrong variant id silently falls back
        # to the parent product (safer than crashing for the buyer).
        from .models import ProductVariant
        variant = ProductVariant.objects.filter(id=variant_id, product=product).first()

    stock_available = variant.stock if variant else product.stock
    if stock_available <= 0:
        messages.error(request, 'This item is currently out of stock.')
        return redirect('product_detail', product_id=product.id)

    # 2. Get the user's shopping cart bucket. If they don't have one yet, build them a new one!
    # get_or_create returns a tuple: (the_object, created_boolean). We just want the object.
    cart, created = Cart.objects.get_or_create(user=request.user)

    # 3. Check if this specific product is already sitting inside the cart bucket.
    # We also match on variant so a "Red / M" and a "Blue / L" become 2 separate lines.
    if variant:
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart, product=product, variant=variant
        )
    else:
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart, product=product, variant__isnull=True
        )

    # 4. If the item was already in the cart, we just add 1 to the quantity.
    if not item_created:
        if cart_item.quantity + 1 > stock_available:
            messages.error(request, 'Not enough stock available for this item.')
            return redirect('cart')
        cart_item.quantity += 1
        cart_item.save()
        # Like saying "I already had one pair of these socks in the cart, let's make it two!"

    # Send a cheerful success message to the customer using Django's message framework
    # If a variant was selected, mention it in the message so the buyer knows what they got.
    if variant:
        messages.success(request, f"Added {product.title} ({variant.display_name}) to your cart!")
    else:
        messages.success(request, f"Added {product.title} to your cart!")

    # 5. Send the customer right back to the storefront so they can keep shopping!
    return redirect('index')

@login_required
def add_product(request):
    if not require_seller(request):
        return redirect('index')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save(commit=False)
            p.owner = request.user
            p.save()
            messages.success(request, 'Product added.')
            return redirect('index')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})


@login_required
def edit_product(request, product_id):
    product = get_owned_product_or_redirect(
        request,
        product_id,
        'You can only edit products that you own.',
    )
    if product is None:
        return redirect('index')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated.')
            return redirect('index')
    else:
        form = ProductForm(instance=product)
    return render(request, 'add_product.html', {'form': form, 'editing': True, 'product': product})


@login_required
def delete_product(request, product_id):
    product = get_owned_product_or_redirect(
        request,
        product_id,
        'You can only delete products that you own.',
    )
    if product is None:
        return redirect('index')
    # For safety, require POST to delete
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('index')
    # Render a simple confirmation page
    return render(request, 'confirm_delete.html', {'object': product})

@login_required
# Protect this cart review view so that only authenticated members can inspect a shopping session
def view_cart(request):
    # 1. Fetch or initialize the user's active shopping cart bucket.
    # we initialize a clean, empty cart for them instead of throwing a database or lookup error.
    # The method returns a tuple: (cart_instance, was_created_boolean), so we unpack the first item.
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # 2. Gather all the individual items linked to this user's cart.
    cart_items = cart.items.all().select_related('product')
    
    # 3. Calculate the sum total cost of all the products sitting inside the shopping cart.
    # We start our counter at exactly 0.00 dollars.
    total_price = 0
    
    # 4. Iterate through every single item in the cart collection to calculate the cumulative price.
    for item in cart_items:
        # The subtotal helper on CartItem already handles variant pricing for us.
        # We just call it here so the cart total stays correct whether the buyer
        # picked a variant or the plain product.
        total_price += item.subtotal
        
    # 5. Pack our calculated data into a neat dictionary box (context) to ship to the frontend template.
    context = {
        'cart': cart,
        # The primary Cart object representing this user's shopping session
        'cart_items': cart_items,
        # The collection of items currently inside the shopping cart
        'total_price': total_price,
        # The calculated total cost of the customer's shopping basket
    }
    
    # 6. Render the dedicated `cart.html` review page, passing along our context data box!
    return render(request, 'cart.html', context)

@login_required
def increment_cart_item(request, item_id):
    # 1. Find the specific CartItem that the user clicked. If the item doesn't exist, throw a 404 error.
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    # 2. Add 1 to the quantity field
    cart_item.quantity += 1
    
    # 3. Save the updated quantity back to the database
    cart_item.save()
    
    # 4. Send a sweet message to let the user know their cart has been updated
    messages.success(request, f"Increased quantity of {cart_item.product.title}!")
    
    # 5. Send them right back to the cart review page to see the new total
    return redirect('cart')

@login_required
def decrement_cart_item(request, item_id):
    # 1. Find the specific CartItem that the user clicked, ensuring it belongs to them
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    # 2. Check if they have more than 1 of this item in their cart
    if cart_item.quantity > 1:
        # Subtract 1 from the quantity
        cart_item.quantity -= 1
        cart_item.save()
        messages.success(request, f"Decreased quantity of {cart_item.product.title}!")
    else:
        # 3. If quantity is exactly 1 and they decrement, delete the item entirely
        cart_item.delete()
        messages.warning(request, f"Removed {cart_item.product.title} from your cart!")
        
    # 4. Redirect them back to their cart review page
    return redirect('cart')

@login_required
def delete_cart_item(request, item_id):
    # 1. Grab the specific CartItem ensuring it belongs to this logged-in user
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    # 2. Completely remove the cart item from the database
    cart_item.delete()
    
    # 3. Send a warning/danger message confirming the removal of the item
    messages.warning(request, f"Removed {cart_item.product.title} from your cart!")
    
    # 4. Redirect the user back to their active cart page
    return redirect('cart')

@login_required
def checkout_initiate(request):
    # We restrict this view to POST requests only, as it handles form submission data
    if request.method == 'POST':
        # 1. Fetch the user's active shopping cart bucket. If they don't have one, redirect back to cart.
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # 2. Gather all the items sitting inside the user's cart.
        cart_items = list(cart.items.select_related('product', 'variant').all())
        
        if not cart_items:
            messages.warning(request, "Your shopping cart is empty! Add some items before checking out.")
            return redirect('cart')
            
        # 4. Retrieve the customer's shipping information from the POST request form fields.
        # strip() is used to remove any accidental trailing spaces the user might have typed.
        full_name = request.POST.get('full_name', '').strip()
        address = request.POST.get('address', '').strip()
        
        # 5. Check if the shipping information is completely filled out.
        if not full_name or not address:
            messages.error(request, "Please fill out all required shipping fields to proceed.")
            return redirect('cart')
            
        stock_shortages = []
        for item in cart_items:
            available_stock = item.variant.stock if item.variant_id and item.variant else item.product.stock
            if item.quantity > available_stock:
                label = f"{item.product.title} ({item.variant.display_name})" if item.variant else item.product.title
                stock_shortages.append(label)

        if stock_shortages:
            messages.error(request, "We couldn't create your order because the following item(s) are short on stock: " + ", ".join(stock_shortages))
            return redirect('cart')

        # 6. Initialize our price counter to 0.00 to calculate the grand total.
        total_price = 0
        
        # 7. First, loop through all cart items to pre-calculate the total price.
        for item in cart_items:
            # Reuse CartItem.subtotal so variant prices are included correctly.
            total_price += item.subtotal
            
        # 8. Read payment method and create the parent Order record.
        payment_method = request.POST.get('payment_method', 'stripe')
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            address=address,
            total_price=total_price,
            is_paid=False,
            payment_method=payment_method,
        )
        
        # 9. Now, loop through the cart items again to create static historical OrderItem snapshots.
        for item in cart_items:
            # Use the variant's price when present so the locked-in receipt
            # price matches what the buyer actually saw in the cart.
            locked_price = item.variant.get_price if item.variant_id and item.variant else item.product.price
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                price=locked_price
            )
            
        # 10. Once the order details are safely compiled, clear all items from the active cart bucket.
        # This empties their cart for future shopping sessions.
        cart.items.all().delete()
        
        # 11. If COD chosen, mark the order paid, update status, and deduct stock once.
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
            messages.success(request, "Order placed with Cash on Delivery. Check your order details.")
            return redirect('order_detail', order_id=order.order_id)

        messages.success(request, "Order initiated successfully! Please review and complete your payment.")
        return redirect('checkout_page', order_id=order.order_id)
        
    # If a user attempts to access this URL directly via a GET request, send them back to the cart page
    return redirect('cart')

@login_required
def checkout_page(request, order_id):
    # 1. Fetch the single, unpaid order matching the unique 7-digit order_id.
    order = get_object_or_404(Order, order_id=order_id, user=request.user, is_paid=False)
    
    # 2. Gather all the individual OrderItems associated with this parent Order.
    # We prefetch the associated product information to keep database queries optimized.
    order_items = order.items.all().select_related('product')
    
    # 3. Pack the order and its items into our template context block.
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    # 4. Render the modern, clean `checkout.html` page, passing along the invoice context!
    return render(request, 'checkout.html', context)

@login_required
def create_checkout_session(request, order_id):
    # 1. We fetch the specific unpaid order belonging to the current logged-in user
    order = get_object_or_404(Order, order_id=order_id, user=request.user, is_paid=False)
    
    # 2. Configure Stripe key. If a real secret key isn't configured (placeholder),
    #    use a local-development fallback that creates a fake session id and redirects
    #    to the payment status view. This lets frontend/manual testing work without
    #    real Stripe credentials.
    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_configured = bool(settings.STRIPE_SECRET_KEY) and 'placeholder' not in settings.STRIPE_SECRET_KEY
    
    # 3. We initialize an empty list to compile all the products of this order for Stripe
    line_items = []
    
    # 4. We loop through each individual OrderItem snapshot linked to our parent Order
    for item in order.items.all():
        # We append each item formatted specifically as a dictionary matching Stripe's API rules
        line_items.append({
            'price_data': {
                'currency': 'usd', # We define the checkout currency as US Dollars
                'product_data': {
                    'name': item.product.title, # We pass the catalog title of the product
                },
                # Stripe expects prices in "cents" (integers), so we multiply by 100
                'unit_amount': int(item.price * 100),
            },
            'quantity': item.quantity, # We pass the exact quantity purchased
        })
        
    try:
        if not stripe_configured:
            # Create a fake session id for local testing and redirect to payment_status
            fake_session_id = f"dev_{get_random_string(12)}"
            order.stripe_session_id = fake_session_id
            order.save()
            return redirect(f"{reverse('payment_status')}?session_id={fake_session_id}")

        session = stripe.checkout.Session.create(
            payment_method_types=['card'], # We allow standard credit card payments
            line_items=line_items, # We hand over our compiled items shopping list
            mode='payment', # We state that this is a one-time product payment transaction
            # Once payment is complete, Stripe redirects the user back to our local status view.
            # We append Stripe's dynamic template tag '{CHECKOUT_SESSION_ID}' to the URL.
            # Stripe will automatically swap this placeholder with the actual session token upon redirect!
            success_url=request.build_absolute_uri(reverse('payment_status')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('checkout_page', args=[order.order_id])),
            customer_email=request.user.email, # Pre-fill the customer's email on Stripe's page
            metadata={
                'order_id': order.order_id # We attach our internal database order ID for audit logs
            }
        )

        # 6. We record the generated Stripe Session ID on our database Order record
        order.stripe_session_id = session.id
        order.save() # Save the database record to lock in the session mapping!

        # 7. Redirect the user's browser directly to Stripe's gorgeous, secure hosted payment page!
        return redirect(session.url, code=303)

    except Exception as e:
        # If any API or connection exception occurs, we catch it and display a friendly alert
        messages.error(request, f"Stripe integration failed: {str(e)}")
        # Redirect the user right back to the checkout details page to review and retry
        return redirect('checkout_page', order_id=order.order_id)

@login_required
def payment_status(request):
    # 1. We extract the session_id query parameter returned from the Stripe checkout page redirect
    session_id = request.GET.get('session_id')
    
    # 2. If no session_id exists in the URL, the user accessed this page incorrectly. Redirect to home!
    if not session_id:
        messages.warning(request, "No transaction session identifier was found.")
        return redirect('index')
        
    # 3. We look up the order in our database that maps to this specific Stripe session
    order = get_object_or_404(Order, stripe_session_id=session_id, user=request.user)

    # 4. If this is a local-development fake session, treat it as successful to allow testing
    if session_id.startswith('dev_'):
        order.mark_paid_and_update_status()
        try:
            order.deduct_stock_once()
        except ValueError as exc:
            messages.error(request, str(exc))
        context = {'order': order, 'status': 'success'}
        return render(request, 'payment_status.html', context)

    # 5. Otherwise, verify with the Stripe API
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
def seller_orders_view(request):
    if not require_seller(request):
        return redirect('index')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('order_status', '').strip()
        order = get_object_or_404(Order, order_id=order_id)
        has_owned_items = OrderItem.objects.filter(order=order, product__owner=request.user).exists()
        if not has_owned_items:
            logger.warning(
                'Unauthorized seller order status update: user=%s order=%s',
                request.user.pk,
                order.id,
            )
            messages.error(request, 'You can only update orders that contain your products.')
            return redirect('seller_orders')

        valid_statuses = [choice[0] for choice in Order._meta.get_field('order_status').choices]
        if new_status not in valid_statuses:
            messages.error(request, 'Invalid order status selected.')
            return redirect('seller_orders')

        order.order_status = new_status
        order.save(update_fields=['order_status'])
        messages.success(request, f'Order status updated to {new_status.title()}.')
        return redirect('seller_orders')

    seller_orders = Order.objects.filter(items__product__owner=request.user).distinct().order_by('-created_at')
    seller_rows = []
    for order in seller_orders:
        seller_items = list(
            OrderItem.objects.filter(order=order, product__owner=request.user)
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
        'order_status_choices': Order._meta.get_field('order_status').choices,
    })


@login_required
def dashboard_view(request):
    # 1. Retrieve all orders initiated by the current authenticated user, sorted by date (newest first)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # 2. Count the total number of orders in the database for this customer
    total_orders = orders.count()
    
    total_spent = Order.objects.filter(user=request.user, is_paid=True).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # 4. Count the number of pending orders that are still unpaid (is_paid=False)
    pending_orders = Order.objects.filter(user=request.user, is_paid=False).count()
    
    seller_products = Product.objects.filter(owner=request.user).order_by('-created_at', '-id')
    seller_order_items = (
        OrderItem.objects
        .filter(product__owner=request.user)
        .select_related('order', 'product')
        .order_by('-order__created_at', '-id')
    )
    paid_seller_items = [item for item in seller_order_items if item.order.is_paid]
    seller_revenue = sum(item.subtotal for item in paid_seller_items)
    seller_units_sold = sum(item.quantity for item in paid_seller_items)
    seller_pending_sales = sum(1 for item in seller_order_items if not item.order.is_paid)

    # 5. Pack the statistics and the orders collection into our page context data box
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
    
    # 6. Render the upgraded customer dashboard template, passing along the context data
    return render(request, 'dashboard.html', context)

@login_required
def order_detail_view(request, order_id):
    # This prevents users from sneaking into the database to inspect other people's receipts!
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # 2. Gather all individual itemized snapshots associated with this parent order
    order_items = order.items.all().select_related('product')
    
    # 3. Package the order metadata and line items into our template context data block
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    # 4. Render the clean order detail page passing along our receipt inspection context!
    return render(request, 'order_detail.html', context)


# ==============================================================================
# Product detail + variant picker (NEW FEATURE)
# ------------------------------------------------------------------------------
# Shows one Product on its own page along with all of its ProductVariants
# (size/color options). The user picks a variant and hits "Add to cart".
# We do NOT change the existing add_to_cart URL; we only call it with the
# chosen variant id through a query string (?variant=<id>).
# ==============================================================================
@login_required
def product_detail(request, product_id):
    # Look up the product or throw a 404 if it does not exist.
    product = get_object_or_404(Product, id=product_id)

    # Get all variants for this product. If there are none, the template
    # simply shows the "default" product with its own stock/price.
    variants = product.variants.all().order_by('size', 'color')

    # ==============================================================================
    # Reviews (NEW FEATURE)
    # ------------------------------------------------------------------------------
    # Pull all reviews for this product so the template can render them.
    # We also compute the average rating and total review count, used to
    # show a "4.3 / 5 (12 reviews)" summary.
    # ==============================================================================
    from django.db.models import Avg
    reviews = product.reviews.all()
    review_count = reviews.count()
    # aggregate() returns {'rating__avg': <value or None>}; we default to 0
    # when there are no reviews so the math in the template stays simple.
    average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    # Check if the logged-in user already has a review for this product.
    # We use it to decide between "Edit your review" and "Leave a review".
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    return render(request, 'product_detail.html', {
        'product': product,
        'variants': variants,
        'can_manage_product': user_can_manage_product(request.user, product),
        # gallery_images is NEW (multi-image gallery feature). The template
        # uses it to show extra photos below the main product image.
        'gallery_images': product.images.all(),
        # New review context:
        'reviews': reviews,
        'review_count': review_count,
        'average_rating': average_rating,
        'user_review': user_review,
    })


# ==============================================================================
# Add a new review (NEW FEATURE - any logged-in user)
# ------------------------------------------------------------------------------
# Lets a logged-in user submit a star rating + comment for a product.
# We automatically mark the review as a "verified purchase" if the user
# has at least one PAID OrderItem for this product. This stops random
# people from leaving fake reviews for products they never bought.
# ==============================================================================
@login_required
def add_review(request, product_id):
    # 1. Find the product. 404 if missing.
    product = get_object_or_404(Product, id=product_id)

    # 2. Block duplicate reviews: one review per (user, product).
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, 'You already reviewed this product.')
        return redirect('product_detail', product_id=product.id)

    # 3. POST: save the new review. GET: show an empty form.
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # save(commit=False) lets us fill in product/user/verified before
            # the row hits the database.
            review = form.save(commit=False)
            review.product = product
            review.user = request.user

            # "Verified purchase" = user has a PAID order containing this product.
            review.verified_purchase = OrderItem.objects.filter(
                order__user=request.user,
                order__is_paid=True,
                product=product,
            ).exists()

            review.save()
            messages.success(request, 'Thanks! Your review has been posted.')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ReviewForm()

    return render(request, 'add_review.html', {
        'form': form,
        'product': product,
    })


# ==============================================================================
# Delete a review (NEW FEATURE - author or superuser only)
# ------------------------------------------------------------------------------
# Lets a user remove their own review. POST only for safety.
# ==============================================================================
@login_required
def delete_review(request, review_id):
    # 1. Fetch the review. 404 if missing.
    review = get_object_or_404(Review, id=review_id)
    product_id = review.product_id  # remember the parent product to redirect

    # 2. Permission check: only the author or a superuser can delete.
    if request.user != review.user and not request.user.is_superuser:
        messages.error(request, 'You can only delete your own review.')
        return redirect('product_detail', product_id=product_id)

    # 3. POST only: a GET should not destroy data.
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review removed.')

    return redirect('product_detail', product_id=product_id)


# ==============================================================================
# Add a new variant for a product (NEW FEATURE - seller only)
# ------------------------------------------------------------------------------
# Sellers land on a small form where they can type size/color/sku/stock/
# price_override. We attach the new variant to the right product and the
# right owner (the logged-in user must be the product's owner or a superuser).
# ==============================================================================
@login_required
def add_variant(request, product_id):
    product = get_owned_product_or_redirect(
        request,
        product_id,
        'You can only add variants to products that you own.',
    )
    if product is None:
        return redirect('index')

    # 3. On POST we read the form. On GET we show an empty form.
    if request.method == 'POST':
        form = ProductVariantForm(request.POST)
        if form.is_valid():
            # save(commit=False) builds the object in memory but does not
            # write it to the database yet, so we can attach the parent
            # product first.
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            messages.success(request, f'Variant "{variant.display_name}" added.')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductVariantForm()

    # 4. Render the form. We reuse add_product.html styling by extending base.html.
    return render(request, 'add_variant.html', {
        'form': form,
        'product': product,
    })


# ==============================================================================
# Add a gallery image for a product (NEW FEATURE - seller only)
# ------------------------------------------------------------------------------
# Sellers land on a small form to upload one more photo for a product.
# We attach the new image to the right product and the right owner
# (logged-in user must be the product owner or a superuser).
# ==============================================================================
@login_required
def add_product_image(request, product_id):
    product = get_owned_product_or_redirect(
        request,
        product_id,
        'You can only add images to products that you own.',
    )
    if product is None:
        return redirect('index')

    # 3. On POST we read the form (request.FILES is required for image uploads).
    # On GET we show an empty form.
    if request.method == 'POST':
        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            # save(commit=False) lets us attach the parent product before
            # the row is actually written to the database.
            image = form.save(commit=False)
            image.product = product
            image.save()
            messages.success(request, 'Gallery image added.')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductImageForm()

    # 4. Render the form, reusing the same look-and-feel as add_product.
    return render(request, 'add_product_image.html', {
        'form': form,
        'product': product,
    })


# ==============================================================================
# Delete a gallery image (NEW FEATURE - seller only)
# ------------------------------------------------------------------------------
# Tiny endpoint that removes a ProductImage row. POST is required so the
# action cannot be triggered by a simple link/GET (basic CSRF / safety).
# ==============================================================================
@login_required
def delete_product_image(request, image_id):
    # 1. Fetch the gallery image. 404 if it does not exist.
    image = get_object_or_404(ProductImage, id=image_id)
    product = image.product  # remember the parent product to redirect back

    # 2. Permission check: only the owner of the parent product.
    if not user_can_manage_product(request.user, product):
        messages.error(request, 'You can only delete images from products that you own.')
        return redirect('index')

    # 3. Only allow POST. A GET should not destroy data.
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Gallery image removed.')

    # 4. Send the user back to the product page.
    return redirect('product_detail', product_id=product.id)

