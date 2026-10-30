from django.db import models
from django.contrib.auth.models import User


class Warehouse(models.Model):
    """Physical warehouse / distribution center."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    capacity = models.PositiveIntegerField(help_text='Total capacity in units')
    current_utilization = models.PositiveIntegerField(default=0, help_text='Current used capacity in units')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_warehouses')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def utilization_percent(self):
        if self.capacity == 0:
            return 0
        return round((self.current_utilization / self.capacity) * 100, 1)

    @property
    def available_capacity(self):
        return max(0, self.capacity - self.current_utilization)


class InventoryItem(models.Model):
    """Item stored in a warehouse."""
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('machinery', 'Machinery'),
        ('raw_materials', 'Raw Materials'),
        ('finished_goods', 'Finished Goods'),
        ('packaging', 'Packaging'),
        ('spare_parts', 'Spare Parts'),
        ('hazardous', 'Hazardous Materials'),
        ('perishable', 'Perishable Goods'),
        ('other', 'Other'),
    ]
    UNIT_CHOICES = [
        ('pcs', 'Pieces'),
        ('kg', 'Kilograms'),
        ('liters', 'Liters'),
        ('boxes', 'Boxes'),
        ('pallets', 'Pallets'),
        ('tons', 'Tons'),
    ]

    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory_items')
    quantity = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='pcs')
    min_stock = models.PositiveIntegerField(default=10, help_text='Minimum stock alert threshold')
    max_stock = models.PositiveIntegerField(default=1000)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.sku} — {self.name}"

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock

    @property
    def stock_value(self):
        return self.quantity * self.unit_price


class StockMovement(models.Model):
    """Record of stock entering, leaving, or transferring between warehouses."""
    MOVEMENT_CHOICES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    quantity = models.IntegerField()
    from_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_movements'
    )
    to_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_movements'
    )
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_movement_type_display()}: {self.quantity} x {self.item.name}"
