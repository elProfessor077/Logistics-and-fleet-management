from django.contrib import admin
from .models import Route, Shipment, ShipmentEvent


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'origin', 'destination', 'distance_km', 'estimated_hours']
    search_fields = ['name', 'origin', 'destination']


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'origin', 'destination', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['tracking_number', 'sender_name', 'receiver_name']
    readonly_fields = ['tracking_number']


@admin.register(ShipmentEvent)
class ShipmentEventAdmin(admin.ModelAdmin):
    list_display = ['shipment', 'status', 'location', 'timestamp']
    list_filter = ['status']
