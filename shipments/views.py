from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Shipment, ShipmentEvent, Route


def shipment_list(request):
    """List all shipments with filtering."""
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    search = request.GET.get('search', '')

    shipments = Shipment.objects.select_related('vehicle', 'route').all()

    if status_filter:
        shipments = shipments.filter(status=status_filter)
    if priority_filter:
        shipments = shipments.filter(priority=priority_filter)
    if search:
        shipments = shipments.filter(
            models.Q(tracking_number__icontains=search) |
            models.Q(sender_name__icontains=search) |
            models.Q(receiver_name__icontains=search) |
            models.Q(origin__icontains=search) |
            models.Q(destination__icontains=search)
        )

    context = {
        'shipments': shipments,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search': search,
        'status_choices': Shipment.STATUS_CHOICES,
        'priority_choices': Shipment.PRIORITY_CHOICES,
    }
    return render(request, 'shipments/shipment_list.html', context)


def shipment_detail(request, pk):
    """Detailed view of a shipment with events timeline."""
    shipment = get_object_or_404(
        Shipment.objects.select_related('vehicle', 'route'),
        pk=pk
    )
    events = shipment.events.all()

    context = {
        'shipment': shipment,
        'events': events,
    }
    return render(request, 'shipments/shipment_detail.html', context)


def track_shipment(request):
    """Public shipment tracking page."""
    tracking_number = request.GET.get('tracking', '').strip()
    shipment = None
    events = []

    if tracking_number:
        try:
            shipment = Shipment.objects.get(tracking_number__iexact=tracking_number)
            events = shipment.events.all()
        except Shipment.DoesNotExist:
            messages.error(request, f'No shipment found with tracking number: {tracking_number}')

    context = {
        'tracking_number': tracking_number,
        'shipment': shipment,
        'events': events,
    }
    return render(request, 'shipments/track_shipment.html', context)


def create_shipment(request):
    """Create a new shipment."""
    if request.method == 'POST':
        shipment = Shipment.objects.create(
            origin=request.POST.get('origin', ''),
            destination=request.POST.get('destination', ''),
            sender_name=request.POST.get('sender_name', ''),
            sender_phone=request.POST.get('sender_phone', ''),
            sender_email=request.POST.get('sender_email', ''),
            receiver_name=request.POST.get('receiver_name', ''),
            receiver_phone=request.POST.get('receiver_phone', ''),
            receiver_email=request.POST.get('receiver_email', ''),
            weight_kg=request.POST.get('weight_kg', 0) or 0,
            dimensions=request.POST.get('dimensions', ''),
            description=request.POST.get('description', ''),
            priority=request.POST.get('priority', 'normal'),
        )

        # Create initial event
        ShipmentEvent.objects.create(
            shipment=shipment,
            status='pending',
            location=shipment.origin,
            notes='Shipment created and awaiting pickup.',
        )

        messages.success(request, f'Shipment created! Tracking number: {shipment.tracking_number}')
        return redirect('shipments:shipment_detail', pk=shipment.pk)

    routes = Route.objects.filter(is_active=True)
    context = {
        'routes': routes,
        'priority_choices': Shipment.PRIORITY_CHOICES,
    }
    return render(request, 'shipments/create_shipment.html', context)


from django.db import models
