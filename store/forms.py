from django import forms
from .models import Product, ProductVariant, ProductImage, Review


# Existing ProductForm (UNCHANGED) - we only add new code below.
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'title', 'image', 'description', 'price', 'stock']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
            }),
            'title': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'Product name',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-indigo-600 file:text-white hover:file:bg-indigo-700',
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-xl border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'rows': 5,
                'placeholder': 'Describe the product features and benefits...',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'step': '0.01',
                'min': '0',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'min': '0',
            }),
        }


# ==============================================================================
# ProductVariantForm (NEW FEATURE)
# ------------------------------------------------------------------------------
# Used by sellers on the "manage variants" page to create a new size/color
# combo for one of their products. It is a normal ModelForm bound to the
# ProductVariant model. We mark size, color, sku as NOT required because a
# seller can leave any of them empty (e.g. a fragrance that only varies by size).
# ==============================================================================
class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        # Fields the seller fills in. 'product' is set automatically by the view.
        fields = ['size', 'color', 'sku', 'stock', 'price_override']
        widgets = {
            'size': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'e.g. M, L, XL, 42',
            }),
            'color': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'e.g. Red, Blue',
            }),
            'sku': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'Optional stock keeping unit',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'min': '0',
            }),
            'price_override': forms.NumberInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Optional, leave blank to use product price',
            }),
        }


# ==============================================================================
# ProductImageForm (NEW FEATURE)
# ------------------------------------------------------------------------------
# Used on the "add gallery image" page. The seller picks a file, types an
# optional caption, and gives a sort order (0 = first, 1 = second, ...).
# The 'product' field is set automatically by the view so it never appears
# in the rendered form.
# ==============================================================================
class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'caption', 'order']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-indigo-600 file:text-white hover:file:bg-indigo-700',
            }),
            'caption': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'placeholder': 'e.g. Front view, In box',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'min': '0',
            }),
        }


# ==============================================================================
# ReviewForm (NEW FEATURE)
# ------------------------------------------------------------------------------
# Lets a logged-in buyer submit a star rating + optional comment for a
# product. The "product" and "user" fields are filled in by the view, not
# the form, so the buyer cannot fake a review for someone else.
# ==============================================================================
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            # The rating input lets the buyer pick 1..5.
            'rating': forms.NumberInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'min': '1', 'max': '5',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'block w-full rounded-xl border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200',
                'rows': 4,
                'placeholder': 'Share your experience with this product...',
            }),
        }
