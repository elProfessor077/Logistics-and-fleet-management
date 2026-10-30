from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone

from fleet.models import Vehicle, Driver, VehicleLocation
from warehouse.models import Warehouse, InventoryItem
from shipments.models import Shipment
from transport.models import Ticket, TransportLine
from .forms import RegisterForm


def dashboard(request):
    """Main dashboard with KPIs across all modules."""
    # Fleet KPIs
    total_vehicles = Vehicle.objects.count()
    active_vehicles = Vehicle.objects.filter(status='active').count()
    idle_vehicles = Vehicle.objects.filter(status='idle').count()
    maintenance_vehicles = Vehicle.objects.filter(status='maintenance').count()
    total_drivers = Driver.objects.count()

    # Warehouse KPIs
    total_warehouses = Warehouse.objects.filter(is_active=True).count()
    total_inventory_items = InventoryItem.objects.count()
    low_stock_items = InventoryItem.objects.filter(quantity__lte=models.F('min_stock')).count() if total_inventory_items > 0 else 0
    warehouses = Warehouse.objects.filter(is_active=True)[:6]

    # Shipment KPIs
    total_shipments = Shipment.objects.count()
    pending_shipments = Shipment.objects.filter(status='pending').count()
    in_transit_shipments = Shipment.objects.filter(status='in_transit').count()
    delivered_shipments = Shipment.objects.filter(status='delivered').count()
    recent_shipments = Shipment.objects.all()[:8]

    # Transport KPIs
    total_lines = TransportLine.objects.filter(is_active=True).count()
    total_tickets = Ticket.objects.count()
    active_tickets = Ticket.objects.filter(status='active').count()

    # Fleet status data for chart
    fleet_status_data = {
        'active': active_vehicles,
        'idle': idle_vehicles,
        'maintenance': maintenance_vehicles,
        'retired': Vehicle.objects.filter(status='retired').count(),
    }

    # Shipment status data for chart
    shipment_status_data = {
        'pending': pending_shipments,
        'picked_up': Shipment.objects.filter(status='picked_up').count(),
        'in_transit': in_transit_shipments,
        'delivered': delivered_shipments,
        'failed': Shipment.objects.filter(status='failed').count(),
    }

    context = {
        'total_vehicles': total_vehicles,
        'active_vehicles': active_vehicles,
        'idle_vehicles': idle_vehicles,
        'maintenance_vehicles': maintenance_vehicles,
        'total_drivers': total_drivers,
        'total_warehouses': total_warehouses,
        'total_inventory_items': total_inventory_items,
        'low_stock_items': low_stock_items,
        'warehouses': warehouses,
        'total_shipments': total_shipments,
        'pending_shipments': pending_shipments,
        'in_transit_shipments': in_transit_shipments,
        'delivered_shipments': delivered_shipments,
        'recent_shipments': recent_shipments,
        'total_lines': total_lines,
        'total_tickets': total_tickets,
        'active_tickets': active_tickets,
        'fleet_status_data': fleet_status_data,
        'shipment_status_data': shipment_status_data,
    }
    return render(request, 'core/dashboard.html', context)


# Need this import for the F expression used above
from django.db import models


def robots_txt(request):
    """Serve robots.txt for search engines."""
    base_url = f"{request.scheme}://{request.get_host()}"
    return render(request, 'robots.txt', {'base_url': base_url}, content_type='text/plain')


def sitemap_xml(request):
    """Serve sitemap.xml dynamically with key routes and entity links."""
    base_url = f"{request.scheme}://{request.get_host()}"
    transport_lines = TransportLine.objects.filter(is_active=True)[:100]
    warehouses = Warehouse.objects.filter(is_active=True)[:100]
    vehicles = Vehicle.objects.filter(status__in=['active', 'idle'])[:100]
    context = {
        'base_url': base_url,
        'transport_lines': transport_lines,
        'warehouses': warehouses,
        'vehicles': vehicles,
    }
    return render(request, 'sitemap.xml', context, content_type='application/xml')


def register_view(request):
    """User self-registration view with instant login."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to LogiCraft, {user.first_name or user.username}! Your account has been registered.")
            return redirect('core:dashboard')
        else:
            messages.error(request, "Please resolve the errors below to register your account.")
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


def custom_logout_view(request):
    """Seamless logout supporting both GET and POST requests."""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f"You have been signed out successfully. Goodbye, {username}!")
    return redirect('login')


@login_required
def profile_view(request):
    """Authenticated user profile & permissions summary."""
    return render(request, 'registration/profile.html', {
        'user': request.user,
        'title': 'User Profile'
    })
