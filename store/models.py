from django.db import models, transaction
from django.conf import settings # We use settings.AUTH_USER_MODEL to refer to our custom User model
from django.core.validators import MinValueValidator, MaxValueValidator  # used by Review.rating (1..5)

# --- 1. CATEGORY MODEL ---
class Category(models.Model):
    # The name of the category. CharField is used for short text.
    name = models.CharField(max_length=255)
    
    # unique=True ensures no two categories have the same URL path.
    slug = models.SlugField(unique=True, help_text="Used for clean browser URLs")

    # The Meta class provides extra information about how the model behaves.
    class Meta:
        # Django automatically pluralizes model names, but 'Categorys' looks wrong. 
        # This tells Django to use 'Categories' instead.
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

# --- 2. PRODUCT MODEL ---
# This model represents an individual item available for purchase in our store.
class Product(models.Model):
    # A ForeignKey links this product to exactly one Category. 
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    
    # The title or name of the product.
    title = models.CharField(max_length=255)
    
    # null=True, blank=True means an image is completely optional.
    image = models.FileField(upload_to='products/images', null=True, blank=True)
    
    # TextField is for longer descriptions without a strict character limit. Optional field.
    description = models.TextField(blank=True, null=True)
    
    # DecimalField is the safest way to store money because it prevents floating-point rounding errors.
    # max_digits=10 allows numbers up to 99,999,999.99
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    
    # IntegerField tracks how many items we have in our warehouse. Defaults to 0.
    stock = models.IntegerField(default=0) 
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # A ForeignKey links this product to the owner (User).
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='products')

    def __str__(self):
        # Displays the product's title in the admin panel.
        return self.title

# --- 3. CART MODEL ---
# A Cart holds the items a user intends to buy.
# Since we are enforcing that users MUST be logged in, we link it strictly to the User.
class Cart(models.Model):
    # A ForeignKey links this cart to a registered User. 
    # user cannot be null because guest checkout is disabled.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Tracks when the cart was created.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # We always have a user now, so we return the cart ID and the username.
        return f"Cart {self.id} - User: {self.user.username}"

# --- 4. CART ITEM MODEL ---
# CartItem represents a specific product inside a specific cart, along with the quantity.
class CartItem(models.Model):
    # Links this item to a specific Cart. If the Cart is deleted, the CartItem is deleted too.
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)

    # Links this item to the actual Product being purchased.
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    # ==============================================================================
    # variant (NEW FEATURE - optional, does not break existing rows)
    # ------------------------------------------------------------------------------
    # If the product has size/color options, the buyer picks one and we store it
    # here. null=True/blank=True keeps older CartItem rows valid (they have no
    # variant). related_name='+' means we don't need cartitem_set from the
    # ProductVariant side.
    # ==============================================================================
    variant = models.ForeignKey(
        'store.ProductVariant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
    )

    # PositiveIntegerField ensures they can't order a negative quantity. Defaults to 1.
    quantity = models.PositiveIntegerField(default=1)

    # ==============================================================================
    # ------------------------------------------------------------------------------
    # let you guess the cost. It shows a subtotal line that multiplies $20.00 by 3
    # to display $60.00 for that row.
    # 
    # calls `{{ item.subtotal }}`, it automatically calculates the total cost of this
    # specific item collection by multiplying the unit price by the quantity selected.
    # ==============================================================================
    @property
    def subtotal(self):
        # If this cart item has a variant with a custom price, use it.
        # Otherwise, fall back to the parent product's price.
        # This makes the cart total correct for products that have variants.
        unit_price = self.variant.get_price if self.variant_id and self.variant else self.product.price
        return unit_price * self.quantity

    def __str__(self):
        # Example: "2 x MacBook Pro" or "2 x MacBook Pro (Red / M)" if a variant was picked.
        if self.variant:
            return f"{self.quantity} x {self.product.title} ({self.variant.display_name})"
        return f"{self.quantity} x {self.product.title}"

import random # Import the random module to generate random integers for our unique order ID

# Helper function to generate a unique 7-digit order ID containing only numbers
def generate_unique_order_id():
    while True:
        # Generate a random 7-digit integer as a string (between 1000000 and 9999999 inclusive)
        new_id = str(random.randint(1000000, 9999999))
        
        # Check the database if this generated ID already exists in any Order record
        if not Order.objects.filter(order_id=new_id).exists():
            # If the ID does not exist, it is unique! We return it and exit the function
            return new_id

# --- 5. ORDER MODEL ---
# Order represents a finalized purchase.
class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    order_id = models.CharField(max_length=7, unique=True, null=True, blank=True, help_text="Unique 7-digit order identifier")
    
    # Shipping Information Fields (Required for delivery)
    full_name = models.CharField(max_length=100)
    
    # The delivery address where the items will be shipped.
    address = models.CharField(max_length=255)
    
    # The total cost of everything in the order.
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Tracks when the order was placed.
    created_at = models.DateTimeField(auto_now_add=True)
    
    # BooleanField tracks if the user has successfully paid for the order yet.
    is_paid = models.BooleanField(default=False)
    order_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending',
    )
    stock_deducted = models.BooleanField(default=False)

    # stripe_session_id CharField stores the unique Stripe Checkout Session identifier.
    # This helps us match our database Order with the actual Stripe session when verifying payment.
    stripe_session_id = models.CharField(max_length=255, null=True, blank=True, help_text="Stripe Checkout Session identifier")
    
    # payment method: 'stripe' or 'cod'
    payment_method = models.CharField(max_length=10, choices=(('stripe','Stripe'),('cod','CashOnDelivery')), default='stripe')

    def save(self, *args, **kwargs):
        # Check if the order_id has not been set yet
        if not self.order_id:
            # Call our helper generator function to assign a unique 7-digit number
            self.order_id = generate_unique_order_id()
        # Call the parent class's standard save method to store the record in the database
        super().save(*args, **kwargs)

    def mark_paid_and_update_status(self):
        if not self.is_paid:
            self.is_paid = True
        if self.order_status == 'pending':
            self.order_status = 'processing'
        self.save(update_fields=['is_paid', 'order_status'])

    def deduct_stock_once(self):
        if self.stock_deducted:
            return False

        with transaction.atomic():
            order_items = list(self.items.select_related('product', 'variant').all())
            for item in order_items:
                if item.variant_id:
                    variant = ProductVariant.objects.select_for_update().get(id=item.variant_id)
                    if variant.stock < item.quantity:
                        raise ValueError(f"Insufficient stock for {variant.display_name}")
                else:
                    product = Product.objects.select_for_update().get(id=item.product_id)
                    if product.stock < item.quantity:
                        raise ValueError(f"Insufficient stock for {product.title}")

            for item in order_items:
                if item.variant_id:
                    variant = ProductVariant.objects.select_for_update().get(id=item.variant_id)
                    variant.stock -= item.quantity
                    variant.save(update_fields=['stock'])
                else:
                    product = Product.objects.select_for_update().get(id=item.product_id)
                    product.stock -= item.quantity
                    product.save(update_fields=['stock'])

            self.stock_deducted = True
            self.save(update_fields=['stock_deducted'])

        return True

    def __str__(self):
        return f"Order {self.order_id} by {self.full_name}"

# --- 6. ORDER ITEM MODEL ---
# OrderItem is a snapshot of a CartItem the moment it was purchased.
class OrderItem(models.Model):
    # Links this item to a specific Order.
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    
    # Links to the Product. 
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    variant = models.ForeignKey(
        'store.ProductVariant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
    )
    
    # The quantity purchased.
    quantity = models.PositiveIntegerField(default=1)
    
    # CRITICAL: We save the price *at the moment of purchase*.
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # ==============================================================================
    # ------------------------------------------------------------------------------
    # Similar to how the CartItem calculates dynamic prices, when reviewing a printed
    # receipt, you want to see exactly how much you paid for that row (e.g. 2 books
    # at $15.00 each equals a subtotal of $30.00). 
    # This property performs this calculation using the locked-in historical price.
    # ==============================================================================
    @property
    def subtotal(self):
        # Multiply the frozen purchase price by the quantity ordered
        return self.price * self.quantity

    def __str__(self):
        return f"Item {self.id} for Order {self.order.id}"


# ==============================================================================
# ProductVariant (NEW FEATURE - does not change the existing Product model)
# ------------------------------------------------------------------------------
# A single Product (e.g. a T-shirt) can be sold in many options such as
# different sizes or colors. Instead of forcing the seller to create a
# separate Product row for every combo, we add a ProductVariant table that
# links back to the parent product.
# ------------------------------------------------------------------------------
class ProductVariant(models.Model):
    # Link this variant to its parent product.
    # on_delete=CASCADE means: if the product is deleted, its variants are also deleted.
    # related_name='variants' lets us call product.variants.all() from views/templates.
    product = models.ForeignKey(
        'store.Product',
        on_delete=models.CASCADE,
        related_name='variants',
    )

    # The size label shown to the shopper (S, M, L, XL, 38, 40, ...).
    # blank=True means the seller can leave it empty (e.g. for digital products).
    size = models.CharField(max_length=20, blank=True)

    # The color label shown to the shopper (Red, Blue, #FF0000, ...).
    color = models.CharField(max_length=30, blank=True)

    # Stock Keeping Unit: optional business identifier for inventory syncing.
    sku = models.CharField(max_length=50, blank=True)

    # How many units of THIS specific variant we have. Independent of product.stock.
    stock = models.PositiveIntegerField(default=0)

    # Optional price override for this variant. If empty, product.price is used.
    # null=True/blank=True are required so the field can be left empty in forms.
    price_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Auto-stamped the first time the row is saved.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A product can only have ONE row for a given (size, color) combination.
        # e.g. you cannot create two "Red / Medium" variants for the same T-shirt.
        unique_together = ('product', 'size', 'color')

    # Returns the price the buyer should pay for this variant.
    # If this variant has a custom price we use it; otherwise we fall back to
    # the parent product's price. Saves us writing this if/else everywhere.
    @property
    def get_price(self):
        return self.price_override if self.price_override is not None else self.product.price

    # Human-friendly label for this variant, e.g. "Red / Medium".
    # We drop empty parts so we never show " / " for blank size or color.
    @property
    def display_name(self):
        parts = [p for p in (self.size, self.color) if p]
        return ' / '.join(parts) if parts else 'Default'

    # Shown in the Django admin dropdown so the seller can tell variants apart.
    def __str__(self):
        return f"{self.product.title} - {self.display_name}"


# ==============================================================================
# ProductImage (NEW FEATURE - does not change the existing Product.image field)
# ------------------------------------------------------------------------------
# The existing Product model already has ONE image field. This new table lets
# a seller attach MANY extra images to a single product (front, back, side,
# zoomed-in, in-use, etc.) without modifying the original Product model.
# ==============================================================================
class ProductImage(models.Model):
    # Link this image to its parent product. CASCADE keeps the gallery clean
    # when the product is deleted.
    product = models.ForeignKey(
        'store.Product',
        on_delete=models.CASCADE,
        related_name='images',  # lets us call product.images.all()
    )

    # The actual image file. We store it under products/gallery/ to keep
    # it separate from the existing products/images/ folder.
    image = models.ImageField(upload_to='products/gallery')

    # Optional caption shown under the image (e.g. "Front view", "In box").
    # blank=True means the seller can leave it empty.
    caption = models.CharField(max_length=200, blank=True)

    # Sort order: lower numbers come first. Defaults to 0.
    # Lets the seller control which photo is the cover.
    order = models.PositiveIntegerField(default=0)

    # Auto-stamped the first time the row is saved.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Default ordering so the gallery always shows in the seller's chosen order.
        ordering = ['order', 'id']

    # Shown in the admin list. Truncates long captions to keep the table tidy.
    def __str__(self):
        return f"{self.product.title} - {self.caption or 'Image ' + str(self.id)}"


# ==============================================================================
# Review (NEW FEATURE - does not change existing Product/Order models)
# ------------------------------------------------------------------------------
# A buyer who has purchased a product can leave a star rating (1-5) and a
# short comment. The "verified_purchase" flag is set automatically: TRUE
# only if the reviewer has at least one paid OrderItem for this product.
# This stops random users from spamming fake reviews for products they
# never bought.
# ==============================================================================
class Review(models.Model):
    # Link the review to one product. CASCADE keeps reviews tidy: if a
    # product is deleted, its reviews are deleted too.
    product = models.ForeignKey(
        'store.Product',
        on_delete=models.CASCADE,
        related_name='reviews',  # lets us call product.reviews.all()
    )

    # Link the review to the user who wrote it. SET_NULL means: if a user
    # is later deleted, the review text is kept (good for shop credibility)
    # but the user pointer becomes empty.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviews',
    )

    # Star rating 1..5. PositiveSmallIntegerField is a small int (saves
    # space) and validators=[MinValueValidator(1), MaxValueValidator(5)]
    # make sure the form cannot accept 0 or 6.
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    # Short text comment. blank=True means the buyer can leave just a
    # star rating without writing words.
    comment = models.TextField(blank=True)

    # True only if this reviewer actually paid for this product. The view
    # sets this when the review is created, so the form doesn't expose it.
    verified_purchase = models.BooleanField(default=False)

    # Auto-stamped the first time the row is saved.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Newest reviews first - that is what shoppers usually want to read.
        ordering = ['-created_at']

    # Shown in the admin list - quick "user -> product (rating★)" view.
    def __str__(self):
        return f"{self.user} -> {self.product.title} ({self.rating}★)"
