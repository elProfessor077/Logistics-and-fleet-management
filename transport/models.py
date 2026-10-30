import uuid
from django.db import models


class TransportLine(models.Model):
    """A public transport line (bus, metro, tram)."""
    TYPE_CHOICES = [
        ('bus', 'Bus'),
        ('metro', 'Metro'),
        ('tram', 'Tram'),
        ('ferry', 'Ferry'),
        ('rail', 'Commuter Rail'),
    ]

    name = models.CharField(max_length=100)
    line_number = models.CharField(max_length=10, unique=True)
    line_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='bus')
    color_code = models.CharField(max_length=7, default='#0ea5e9', help_text='Hex color code')
    frequency_minutes = models.PositiveIntegerField(default=15, help_text='Average frequency in minutes')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['line_number']

    def __str__(self):
        return f"[{self.line_number}] {self.name}"


class Stop(models.Model):
    """A physical stop/station on a transport line."""
    ZONE_CHOICES = [
        ('1', 'Zone 1 — Central'),
        ('2', 'Zone 2 — Inner'),
        ('3', 'Zone 3 — Outer'),
        ('4', 'Zone 4 — Suburban'),
    ]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    zone = models.CharField(max_length=5, choices=ZONE_CHOICES, default='1')
    address = models.CharField(max_length=300, blank=True)
    is_accessible = models.BooleanField(default=True, help_text='Wheelchair accessible')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} — {self.name}"


class LineStop(models.Model):
    """Ordered stop along a transport line."""
    line = models.ForeignKey(TransportLine, on_delete=models.CASCADE, related_name='line_stops')
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='line_stops')
    order = models.PositiveIntegerField()
    travel_time_from_previous = models.PositiveIntegerField(default=0, help_text='Minutes from previous stop')

    class Meta:
        ordering = ['line', 'order']
        unique_together = ['line', 'stop']

    def __str__(self):
        return f"{self.line.line_number} — Stop #{self.order}: {self.stop.name}"


class Schedule(models.Model):
    """Schedule entry for a transport line."""
    DAYS_CHOICES = [
        ('weekday', 'Monday-Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday & Holidays'),
        ('daily', 'Daily'),
    ]

    line = models.ForeignKey(TransportLine, on_delete=models.CASCADE, related_name='schedules')
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    days_of_week = models.CharField(max_length=20, choices=DAYS_CHOICES, default='weekday')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['departure_time']

    def __str__(self):
        return f"{self.line.line_number}: {self.departure_time} → {self.arrival_time} ({self.get_days_of_week_display()})"


class Ticket(models.Model):
    """Public transport ticket."""
    TYPE_CHOICES = [
        ('single', 'Single Trip'),
        ('return', 'Return Trip'),
        ('day', 'Day Pass'),
        ('weekly', 'Weekly Pass'),
        ('monthly', 'Monthly Pass'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    ticket_id = models.CharField(max_length=20, unique=True, editable=False)
    passenger_name = models.CharField(max_length=200)
    passenger_email = models.EmailField(blank=True)
    passenger_phone = models.CharField(max_length=20, blank=True)
    line = models.ForeignKey(TransportLine, on_delete=models.CASCADE, related_name='tickets')
    origin_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='departure_tickets')
    destination_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='arrival_tickets')
    ticket_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='single')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField()
    qr_code = models.TextField(blank=True, help_text='Base64-encoded QR code image')

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return f"{self.ticket_id} — {self.passenger_name} ({self.get_ticket_type_display()})"

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            self.ticket_id = f"TK-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
