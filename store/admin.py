from django.contrib import admin
from store.models import Category, Product, Cart, CartItem, Order, OrderItem, ProductVariant, ProductImage, Review


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'order_status', 'is_paid', 'payment_method', 'total_price', 'created_at')
    list_filter = ('order_status', 'is_paid', 'payment_method')
    search_fields = ('order_id', 'full_name', 'address')


# Register your models here.
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)

# ProductVariant is a NEW feature. Registering it here makes variants
# manageable from the Django admin (list, search, edit, delete).
# list_display controls which columns are shown in the variant list page.
admin.site.register(ProductVariant)

# ProductImage (NEW FEATURE) - shows gallery images in the admin list with
# their parent product, order, and caption columns.
admin.site.register(ProductImage)

# Review (NEW FEATURE) - lets the admin see all reviews in one place.
admin.site.register(Review)
