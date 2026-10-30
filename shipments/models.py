import uuid
from django.db import models
from fleet.models import Vehicle


class Route(models.Model):
    """Predefined delivery route."""
    name = models.CharField(max_length=200)
    origin = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    distance_km = models.DecimalField(max_digits=8, decimal_places=2)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2)
    waypoints = models.JSONField(default=list, blank=True, help_text='List of lat/lng waypoints')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name}: {self.origin} → {self.destination}"


class Shipment(models.Model):
    """Individual shipment with full lifecycle tracking."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    tracking_number = models.CharField(max_length=30, unique=True, editable=False)
    origin = models.CharField(max_length=300)
    destination = models.CharField(max_length=300)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    dimensions = models.CharField(max_length=50, blank=True, help_text='LxWxH in cm')
    description = models.TextField(blank=True)

    sender_name = models.CharField(max_length=200)
    sender_phone = models.CharField(max_length=20)
    sender_email = models.EmailField(blank=True)
    receiver_name = models.CharField(max_length=200)
    receiver_phone = models.CharField(max_length=20)
    receiver_email = models.EmailField(blank=True)

    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tracking_number} — {self.origin} → {self.destination}"

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = f"LC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class ShipmentEvent(models.Model):
    """Timeline event for a shipment."""
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    location = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shipment.tracking_number} — {self.get_status_display()} at {self.timestamp}"
