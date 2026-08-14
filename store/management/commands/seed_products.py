from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from store.models import Category, Product
from pathlib import Path

class Command(BaseCommand):
    help = 'Seed sample products using media files in store/media/products/images'

    def handle(self, *args, **options):
        media_dir = Path(settings.MEDIA_ROOT) / 'products' / 'images'
        if not media_dir.exists():
            self.stdout.write(self.style.ERROR(f'Media directory not found: {media_dir}'))
            return

        categories = {
            'Laptops': 'laptops',
            'Accessories': 'accessories',
            'Audio': 'audio',
            'Displays': 'displays',
        }

        for name, slug in categories.items():
            Category.objects.get_or_create(name=name, slug=slug)

        sample_products = [
            {
                'title': 'MacBook Pro 16-inch M4',
                'description': 'Powerful laptop with M4 chip, pro-grade performance for creatives and developers.',
                'price': 2499.00,
                'stock': 8,
                'category': 'Laptops',
                'image_name': 'MacBook_Pro_16-inch_M4_Pro_or_Max_chip_Space_Black_PDP_Image_Position_2_eWGIyVM.webp',
            },
            {
                'title': 'Lenovo ThinkPad X1 Carbon',
                'description': 'Lightweight business laptop with premium keyboard and long battery life.',
                'price': 1799.00,
                'stock': 10,
                'category': 'Laptops',
                'image_name': 'lenovo-tp-x1-carbon-g9-i7-1185g7-1683280184.jpg',
            },
            {
                'title': 'Apple AirPods Pro',
                'description': 'True wireless earbuds with active noise cancellation and spatial audio.',
                'price': 249.00,
                'stock': 25,
                'category': 'Audio',
                'image_name': 'pngtree-apple-airpods-pro-png-image_10477533.png',
            },
            {
                'title': 'Apple Studio Display',
                'description': '27-inch Retina 5K display with reference modes and studio-quality camera.',
                'price': 1599.00,
                'stock': 4,
                'category': 'Displays',
                'image_name': 'studio-display-og-202603.jpg',
            },
            {
                'title': 'USB Numeric Keypad',
                'description': 'Compact numeric keypad with Touch ID support and sleek black finish.',
                'price': 59.99,
                'stock': 50,
                'category': 'Accessories',
                'image_name': 'keyboard-touchid-numeric-keypad-black-2.png',
            },
        ]

        created = 0
        updated = 0

        for product_data in sample_products:
            category = Category.objects.get(name=product_data['category'])
            product, was_created = Product.objects.get_or_create(
                title=product_data['title'],
                defaults={
                    'description': product_data['description'],
                    'price': product_data['price'],
                    'stock': product_data['stock'],
                    'category': category,
                }
            )
            image_path = media_dir / product_data['image_name']
            if image_path.exists():
                with image_path.open('rb') as image_file:
                    product.image.save(image_path.name, File(image_file), save=False)
            else:
                self.stdout.write(self.style.WARNING(f'Missing image: {image_path}'))

            if was_created:
                product.save()
                created += 1
            else:
                product.description = product_data['description']
                product.price = product_data['price']
                product.stock = product_data['stock']
                product.category = category
                product.save()
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Products seeded: {created} created, {updated} updated.'))
