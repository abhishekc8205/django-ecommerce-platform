# store/context_processors.py

from store.models import CartItem

def cart_item_count(request):
    # Therefore, we return a default count of 0 items.
    if not request.user.is_authenticated:
        return {'cart_count': 0}
        
    try:
        # 2. Query the database to find all CartItem objects belonging to this user's cart.
        # We look up items where the cart's owner matches the currently logged-in user.
        items = CartItem.objects.filter(cart__user=request.user)
        
        # 3. Sum up the quantity field of each item in the cart.
        # For example, if they have 2 laptops and 3 shirts, we sum (2 + 3) to get 5 total items in the cart.
        # If the cart is empty or there are no items, sum() automatically returns 0.
        total_count = sum(item.quantity for item in items)
        
        # 4. Return the key-value dictionary. This key `cart_count` becomes globally
        # accessible as a variable across all our HTML templates!
        return {'cart_count': total_count}
        
    except Exception:
        return {'cart_count': 0}
