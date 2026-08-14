from django.urls import path
from store import views

urlpatterns = [
    path('', views.index_view, name='index'),
    # This path expects an integer (like 1, 2, 3) which represents the product ID.
    # When a user goes to /add-to-cart/5/, Django will grab product #5 and send it to our view.
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    # ==============================================================================
    # ------------------------------------------------------------------------------
    # In a supermarket, when you are done shopping, you look up for a signpost that
    # reads "Aisle 10: Checkout & Cart Review." 
    # 
    # This URL route acts as that dynamic signpost! When a user navigates their browser
    # to `/cart/`, this rule catches their request and guides them directly to our
    # `view_cart` clerk function to inspect their items.
    # ==============================================================================
    path('cart/', views.view_cart, name='cart'),
    # ==============================================================================
    # ------------------------------------------------------------------------------
    # In a checkout lane, you have specialized conveyor belt lanes and registers for
    # adding items, subtracting items, or scanning items straight to the trash box.
    # 
    # These three URLs serve as those electronic lane pathways! When a customer taps
    # a plus, minus, or delete button in their browser, Django guides their request
    # directly to the correct database view handler with the specific Item ID to process.
    # ==============================================================================
    path('increment-cart-item/<int:item_id>/', views.increment_cart_item, name='increment_cart_item'),
    path('decrement-cart-item/<int:item_id>/', views.decrement_cart_item, name='decrement_cart_item'),
    path('delete-cart-item/<int:item_id>/', views.delete_cart_item, name='delete_cart_item'),
    # ==============================================================================
    # ------------------------------------------------------------------------------
    # the Billing Desk (`checkout/initiate/`) where you enter your shipping details
    # to package everything up into an order invoice. Once that invoice is written,
    # the clerk hands you a slip with an order number and guides you to the dynamic
    # Review & Payment Counter (`checkout/<str:order_id>/`) to look over the details
    # and tap "Pay Now".
    # ==============================================================================
    path('checkout/initiate/', views.checkout_initiate, name='checkout_initiate'),
    path('checkout/<str:order_id>/', views.checkout_page, name='checkout_page'),
    
    # ==============================================================================
    # ------------------------------------------------------------------------------
    # payment gate conveyor belt (`checkout/payment/<str:order_id>/`). This creates 
    # the secure Stripe session and guides your browser to their armored payment page.
    # 
    # After filling in your card details, the bank vehicle drives you back to the
    # store's local Customer Service counter (`payment/status/`), which checks the 
    # transaction status and prints a big "APPROVED" or "DECLINED" stamp on your order!
    # ==============================================================================
    # 3. Create Stripe Checkout Session Route (Processes and redirects to Stripe hosted payment form)
    path('checkout/payment/<str:order_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('payment/status/', views.payment_status, name='payment_status'),
    
    # ==============================================================================
    # ------------------------------------------------------------------------------
    # In a major department store, they have a secure "Customer loyalty service desk" 
    # wing where members can ask to view their accounts dashboard or request a printed 
    # detailed copy of a past transaction receipt.
    # 
    # These routes lead directly to those two customer services:
    # 1. `/dashboard/` opens up the dynamic loyalty card statistics and order list.
    # 2. `/order/<order_id>/` opens up the full itemized details of a single receipt.
    # ==============================================================================
    # 5. Customer Loyalty Dashboard Route
    path('dashboard/', views.dashboard_view, name='dashboard'),
    # 6. Detailed Receipt View Route
    path('order/<str:order_id>/', views.order_detail_view, name='order_detail'),
    path('my-sales/', views.seller_orders_view, name='seller_orders'),
    # Seller product add
    path('product/add/', views.add_product, name='add_product'),
    path('product/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    # DRF API endpoints for products and categories
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/products/', views.api_products, name='api_products'),
    path('api/products/<int:pk>/', views.api_product_detail, name='api_product_detail'),

    # ==============================================================================
    # Product detail + variant management (NEW FEATURE)
    # ------------------------------------------------------------------------------
    # These URLs only ADD new behavior. The old add_to_cart / edit_product /
    # delete_product URLs are still here and unchanged. We just add:
    #   - product_detail: shows one product and its variants
    #   - add_variant   : seller form to create a new variant
    # ==============================================================================
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/add-variant/', views.add_variant, name='add_variant'),

    # ==============================================================================
    # Gallery image management (NEW FEATURE)
    # ------------------------------------------------------------------------------
    # - add_product_image  : upload a new gallery photo for a product
    # - delete_product_image: remove one gallery photo
    # ==============================================================================
    path('product/<int:product_id>/add-image/', views.add_product_image, name='add_product_image'),
    path('product/image/<int:image_id>/delete/', views.delete_product_image, name='delete_product_image'),

    # ==============================================================================
    # Reviews (NEW FEATURE)
    # ------------------------------------------------------------------------------
    # - add_review   : submit a star rating + comment for a product
    # - delete_review: remove your own review
    # ==============================================================================
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
]
