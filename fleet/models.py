from django.db import models
from django.contrib.auth.models import User


class Driver(models.Model):
    """Driver profile linked to a Django user account."""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('on_duty', 'On Duty'),
        ('off_duty', 'Off Duty'),
        ('on_leave', 'On Leave'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    license_number = models.CharField(max_length=50, unique=True)
    license_expiry = models.DateField()
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    photo_url = models.URLField(blank=True, null=True)
    date_hired = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.license_number})"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username


class Vehicle(models.Model):
    """Fleet vehicle with assignment and status tracking."""
    TYPE_CHOICES = [
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('pickup', 'Pickup'),
        ('trailer', 'Trailer'),
        ('bus', 'Bus'),
        ('sedan', 'Sedan'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('idle', 'Idle'),
        ('maintenance', 'In Maintenance'),
        ('retired', 'Retired'),
    ]
    FUEL_CHOICES = [
        ('diesel', 'Diesel'),
        ('petrol', 'Petrol'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('cng', 'CNG'),
    ]

    plate_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='truck')
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='diesel')
    mileage = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    capacity_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_service_date = models.DateField(null=True, blank=True)
    next_service_date = models.DateField(null=True, blank=True)
    assigned_driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plate_number} — {self.make} {self.model}"


class VehicleLocation(models.Model):
    """GPS location snapshot for a vehicle."""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    speed = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    heading = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'

    def __str__(self):
        return f"{self.vehicle.plate_number} @ ({self.latitude}, {self.longitude})"


class MaintenanceLog(models.Model):
    """Maintenance record for a vehicle."""
    TYPE_CHOICES = [
        ('routine', 'Routine Service'),
        ('repair', 'Repair'),
        ('inspection', 'Inspection'),
        ('tire', 'Tire Change'),
        ('oil', 'Oil Change'),
        ('brake', 'Brake Service'),
        ('other', 'Other'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_logs')
    maintenance_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='routine')
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date = models.DateField()
    next_due = models.DateField(null=True, blank=True)
    mechanic = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.vehicle.plate_number} — {self.get_maintenance_type_display()} on {self.date}"
