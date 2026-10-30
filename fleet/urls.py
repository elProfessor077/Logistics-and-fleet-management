from django.urls import path
from . import views

app_name = 'fleet'

urlpatterns = [
    path('', views.fleet_list, name='fleet_list'),
    path('map/', views.fleet_map, name='fleet_map'),
    path('drivers/', views.driver_list, name='driver_list'),
    path('vehicle/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('api/locations/', views.api_vehicle_locations, name='api_vehicle_locations'),
    path('api/vehicle/<int:pk>/location/', views.api_record_location, name='api_record_location'),
]

