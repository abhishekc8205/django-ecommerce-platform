from django.urls import path
from . import views

urlpatterns = [
    # We map the URL path 'register/' directly to our register_user view function.
    # We give it a unique name 'register' so we can refer to this path easily in HTML templates
    # or redirect statements using {% url 'register' %} or redirect('register').
    path('register/', views.register_user, name='register'),
    # We map the URL path 'login/' directly to our login_user view function.
    # We give it a unique name 'login' so we can refer to this path easily in templates
    # and redirect statements (like our register_user view redirecting to 'login'!).
    path('login/', views.login_user, name='login'),
    # Note: The dashboard URL has been removed from accounts and registered under the store app.

    # We map the URL path 'logout/' directly to our logout_user view function.
    # We give it a unique name 'logout' so templates can safely trigger a sign-out sequence.
    # Analogy: This is the official "Exit Door" signpost pointing to the exit desk.
    path('logout/', views.logout_user, name='logout'),
    # Allow a logged-in user to become a seller
    path('become-seller/', views.become_seller, name='become_seller'),
]
