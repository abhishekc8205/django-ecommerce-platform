"""
URL configuration for authify_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# path: used to define exact web address routes.
# include: used to reference other local app urls.py files, keeping routing modular.
from django.urls import path, include
from django.contrib import admin

try:
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
except ImportError:
    TokenObtainPairView = None
    TokenRefreshView = None

urlpatterns = [
    # Routes any requests starting with 'admin/' directly to the Django Admin backend.
    path('admin/', admin.site.urls),
    # Include store app urls for the storefront and catalog
    path('', include('store.urls')),
    # We include our accounts app urls.py. By passing an empty string '' as the prefix,
    # we allow routes defined in accounts/urls.py (like 'register/') to be accessed
    # directly at the root level (e.g., 'http://127.0.0.1:8000/register/').
    path('', include('accounts.urls')),
]

if TokenObtainPairView and TokenRefreshView:
    urlpatterns += [
        path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
