from django.urls import path, include
from rest_framework.routers import DefaultRouter

from store.views.products import ProductViewSet, CategoryViewSet
from store.views.index import index_view
from store.views.cart import (
    view_cart, add_to_cart, increment_cart_item,
    decrement_cart_item, delete_cart_item
)
from store.views.orders import (
    checkout_initiate, checkout_page, create_checkout_session,
    payment_status, dashboard_view, order_detail_view, seller_orders_view
)
from store.views.reviews import product_detail, add_review, delete_review
from store.views.products_manage import (
    add_product, edit_product, delete_product,
    add_variant, add_product_image, delete_product_image
)

router = DefaultRouter()
router.register(r'api/categories', CategoryViewSet, basename='category')
router.register(r'api/products', ProductViewSet, basename='product')

urlpatterns = [
    path('', index_view, name='index'),
    *router.urls,

    path('product/<int:product_id>/', product_detail, name='product_detail'),

    path('cart/', view_cart, name='cart'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('increment-cart-item/<int:item_id>/', increment_cart_item, name='increment_cart_item'),
    path('decrement-cart-item/<int:item_id>/', decrement_cart_item, name='decrement_cart_item'),
    path('delete-cart-item/<int:item_id>/', delete_cart_item, name='delete_cart_item'),

    path('checkout/initiate/', checkout_initiate, name='checkout_initiate'),
    path('checkout/<str:order_id>/', checkout_page, name='checkout_page'),
    path('checkout/payment/<str:order_id>/', create_checkout_session, name='create_checkout_session'),
    path('payment/status/', payment_status, name='payment_status'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('order/<str:order_id>/', order_detail_view, name='order_detail'),

    path('my-sales/', seller_orders_view, name='seller_orders'),
    path('product/add/', add_product, name='add_product'),
    path('product/<int:product_id>/edit/', edit_product, name='edit_product'),
    path('product/<int:product_id>/delete/', delete_product, name='delete_product'),
    path('product/<int:product_id>/add-variant/', add_variant, name='add_variant'),
    path('product/<int:product_id>/add-image/', add_product_image, name='add_product_image'),
    path('product/image/<int:image_id>/delete/', delete_product_image, name='delete_product_image'),

    path('product/<int:product_id>/review/', add_review, name='add_review'),
    path('review/<int:review_id>/delete/', delete_review, name='delete_review'),
]
