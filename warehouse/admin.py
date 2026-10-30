from django.contrib import admin
from .models import Warehouse, InventoryItem, StockMovement


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'city', 'capacity', 'current_utilization', 'utilization_percent', 'is_active']
    list_filter = ['city', 'is_active']
    search_fields = ['name', 'code', 'city']


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'warehouse', 'quantity', 'unit', 'is_low_stock']
    list_filter = ['category', 'warehouse']
    search_fields = ['sku', 'name']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['item', 'movement_type', 'quantity', 'from_warehouse', 'to_warehouse', 'timestamp']
    list_filter = ['movement_type', 'timestamp']
