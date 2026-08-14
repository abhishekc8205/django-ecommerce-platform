from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from store.models import Cart, CartItem, Category, Order, OrderItem, Product


class StockAndOrderStatusTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', email='buyer@example.com', password='secret123')
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            category=self.category,
            title='Phone',
            price=99.99,
            stock=1,
            owner=self.user,
        )
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_checkout_rejects_insufficient_stock(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('checkout_initiate'),
            {'full_name': 'Test Buyer', 'address': '123 Main St', 'payment_method': 'cod'},
            follow=True,
        )

        self.assertRedirects(response, reverse('cart'))
        self.assertFalse(Order.objects.exists())
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any('short on stock' in message.lower() for message in messages))

    def test_paid_order_deducts_stock_once_and_updates_status(self):
        self.client.force_login(self.user)
        self.product.stock = 3
        self.product.save(update_fields=['stock'])

        order = Order.objects.create(
            user=self.user,
            full_name='Test Buyer',
            address='123 Main St',
            total_price=199.98,
            payment_method='stripe',
            stripe_session_id='dev_test_session',
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price=99.99)

        response = self.client.get(reverse('payment_status'), {'session_id': 'dev_test_session'})

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertTrue(order.is_paid)
        self.assertEqual(order.order_status, 'processing')
        self.assertEqual(self.product.stock, 1)

        response = self.client.get(reverse('payment_status'), {'session_id': 'dev_test_session'})
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
