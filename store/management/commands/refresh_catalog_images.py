"""Replace catalog images with product-specific images from Wikimedia Commons."""

from pathlib import Path
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from store.models import Product


# Curated direct photo URLs.  The values are intentionally grouped by the
# physical product type, never by a product's position in the catalog.
UNSPLASH = "https://images.unsplash.com/"
IMAGE_URLS = {
    "CloudFlex Running Shoe": UNSPLASH + "photo-1496579538151-212636d0b01c?auto=format&fit=crop&w=1200&q=85",
    "Summit Trail Runner": UNSPLASH + "photo-1551698618-1dfe5d97d256?auto=format&fit=crop&w=1200&q=85",
    "Harbor Leather Loafer": UNSPLASH + "photo-1614252369475-531eba835eb1?auto=format&fit=crop&w=1200&q=85",
    "North Ridge Boot": UNSPLASH + "photo-1542840410-3092f99611a3?auto=format&fit=crop&w=1200&q=85",
    "Coastline Slide": UNSPLASH + "photo-1603487742131-4160ec999306?auto=format&fit=crop&w=1200&q=85",
    "Harbor Cotton Tee": UNSPLASH + "photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=1200&q=85",
    "Northwind Hoodie": UNSPLASH + "photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=1200&q=85",
    "Metro Denim Jacket": UNSPLASH + "photo-1542272604-787c3835535d?auto=format&fit=crop&w=1200&q=85",
    "Rivet Utility Shirt": UNSPLASH + "photo-1503342394128-c104d54dba01?auto=format&fit=crop&w=1200&q=85",
    "Coastline Chino": UNSPLASH + "photo-1473966968600-fa801b869a1a?auto=format&fit=crop&w=1200&q=85",
    "Orbit Travel Tote": UNSPLASH + "photo-1591561954557-26941169b49e?auto=format&fit=crop&w=1200&q=85",
    "Signal Leather Wallet": UNSPLASH + "photo-1627123424574-724758594e93?auto=format&fit=crop&w=1200&q=85",
    "Glow Travel Belt": UNSPLASH + "photo-1624222247344-550fb60583dc?auto=format&fit=crop&w=1200&q=85",
    "Drift Polarized Shades": UNSPLASH + "photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=1200&q=85",
    "Voyager Backpack": UNSPLASH + "photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=85",
    "Echo Wireless Earbuds": UNSPLASH + "photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=1200&q=85",
    "Pulse Bluetooth Speaker": UNSPLASH + "photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=1200&q=85",
    "Flux Mechanical Keyboard": UNSPLASH + "photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=1200&q=85",
    "Vanta USB-C Hub": UNSPLASH + "photo-1760376789478-c1023d2dc007?auto=format&fit=crop&w=1200&q=85",
    "Nova Wireless Mouse": UNSPLASH + "photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=1200&q=85",
    "Apex X10 Phone": UNSPLASH + "photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=1200&q=85",
    "Mira Z Pro": UNSPLASH + "photo-1510557880182-3d4d3cba35a5?auto=format&fit=crop&w=1200&q=85",
    "Pixel Mini Wireless": UNSPLASH + "photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=1200&q=85",
    "Nexa Edge Duo": UNSPLASH + "photo-1580910051074-3eb694886505?auto=format&fit=crop&w=1200&q=85",
    "Apex X10 Max": UNSPLASH + "photo-1565849904461-04a58ad377e0?auto=format&fit=crop&w=1200&q=85",
    "AtlasBook Air 14": UNSPLASH + "photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=1200&q=85",
    "ForgeDesk Mini PC": UNSPLASH + "photo-1547082299-de196ea013d6?auto=format&fit=crop&w=1200&q=85",
    "Crest UltraBook 15": UNSPLASH + "photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1200&q=85",
    "Terra Workstation": UNSPLASH + "photo-1549921296-bc643ead1e65?auto=format&fit=crop&w=1200&q=85",
    "Summit Pro 13": UNSPLASH + "photo-1484788984921-03950022c9ef?auto=format&fit=crop&w=1200&q=85",
}


def fetch(url):
    request = Request(url, headers={"User-Agent": "EcommerceCatalogImageUpdater/1.0"})
    with urlopen(request, timeout=30) as response:
        return response.read(), response.headers.get_content_type()


class Command(BaseCommand):
    help = "Remove old catalog files and download curated product-specific images."

    def handle(self, *args, **options):
        products = list(Product.objects.order_by("id"))
        missing = [product.title for product in products if product.title not in IMAGE_URLS]
        if missing:
            raise CommandError("Missing image searches for: " + ", ".join(missing))

        # Download everything before deleting current files.  A network failure
        # therefore can never leave the catalog only half-populated.
        downloaded_images = []
        for product in products:
            image_url = IMAGE_URLS[product.title]
            try:
                image_bytes, content_type = fetch(image_url)
            except Exception as error:
                raise CommandError(f"Could not download image for {product.title}: {error}") from error
            if not content_type.startswith("image/"):
                raise CommandError(f"Image download failed for {product.title}")
            downloaded_images.append((product, image_url, image_bytes, content_type))

        image_dir = Path("store/media/products/images")
        for path in image_dir.iterdir():
            if path.is_file():
                path.unlink()
        Product.objects.exclude(image="").update(image="")

        for product, image_url, image_bytes, content_type in downloaded_images:
            extension = "png" if content_type == "image/png" else "jpg"
            filename = f"{product.title.lower().replace(' ', '-')}.{extension}"
            product.image.save(filename, ContentFile(image_bytes), save=False)
            product.save(update_fields=["image"])
            self.stdout.write(self.style.SUCCESS(f"Updated {product.title}: {image_url}"))

        self.stdout.write(self.style.SUCCESS(f"Refreshed {len(products)} product images."))
