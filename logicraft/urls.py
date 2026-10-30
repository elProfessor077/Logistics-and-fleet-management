"""LogiCraft URL Configuration."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from fleet import views as fleet_views
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('fleet/', include('fleet.urls')),
    path('warehouse/', include('warehouse.urls')),
    path('shipments/', include('shipments.urls')),
    path('transport/', include('transport.urls')),
    path('api/fleet/locations/', fleet_views.api_vehicle_locations, name='api_fleet_locations_global'),
    path('accounts/register/', core_views.register_view, name='register'),
    path('accounts/logout/', core_views.custom_logout_view, name='logout'),
    path('accounts/profile/', core_views.profile_view, name='profile'),
    path('accounts/', include('django.contrib.auth.urls')),
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
