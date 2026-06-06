"""
URL configuration for main_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('main_users.urls')),
    path('', include('main_home.urls')),
    path('data_management/', include('main_data_management.urls', namespace='data_management')),
    # Feature apps (app_*) are mounted here as they are migrated in from tango_bsm:
    #   path("property_management/", include("app_hospitality_core.urls")),
    #   path('brand-standards/', include('app_brand_standard.urls')),
    #   path('procurement/', include('app_procurement.urls', namespace='procurement')),
    #   path('hotel_audit/', include('app_hotel_audit.urls', namespace='hotel_audit')),
    #   path('inventory/', include('app_inventory.urls', namespace='inventory')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
