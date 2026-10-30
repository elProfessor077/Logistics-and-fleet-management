from django.contrib import admin
from .models import Driver, Vehicle, VehicleLocation, MaintenanceLog


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'license_number', 'phone', 'status']
    list_filter = ['status']
    search_fields = ['user__first_name', 'user__last_name', 'license_number']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate_number', 'make', 'model', 'vehicle_type', 'status', 'assigned_driver']
    list_filter = ['status', 'vehicle_type', 'fuel_type']
    search_fields = ['plate_number', 'make', 'model']


@admin.register(VehicleLocation)
class VehicleLocationAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'latitude', 'longitude', 'speed', 'timestamp']
    list_filter = ['vehicle']


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'maintenance_type', 'date', 'cost', 'next_due']
    list_filter = ['maintenance_type', 'date']
