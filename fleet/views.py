from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Vehicle, Driver, VehicleLocation, MaintenanceLog


def fleet_list(request):
    """List all vehicles with filtering."""
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')

    vehicles = Vehicle.objects.select_related('assigned_driver__user').all()

    if status_filter:
        vehicles = vehicles.filter(status=status_filter)
    if type_filter:
        vehicles = vehicles.filter(vehicle_type=type_filter)

    context = {
        'vehicles': vehicles,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'status_choices': Vehicle.STATUS_CHOICES,
        'type_choices': Vehicle.TYPE_CHOICES,
    }
    return render(request, 'fleet/fleet_list.html', context)


def fleet_map(request):
    """Map view of all vehicles with latest GPS positions."""
    vehicles = Vehicle.objects.filter(status__in=['active', 'idle']).select_related('assigned_driver__user')

    # Get latest location for each vehicle
    vehicle_data = []
    for vehicle in vehicles:
        latest_location = vehicle.locations.first()
        if latest_location:
            vehicle_data.append({
                'id': vehicle.id,
                'plate': vehicle.plate_number,
                'type': vehicle.vehicle_type,
                'status': vehicle.status,
                'make': vehicle.make,
                'model': vehicle.model,
                'driver': vehicle.assigned_driver.full_name if vehicle.assigned_driver else 'Unassigned',
                'lat': float(latest_location.latitude),
                'lng': float(latest_location.longitude),
                'speed': float(latest_location.speed),
                'heading': float(latest_location.heading),
                'timestamp': latest_location.timestamp.isoformat(),
            })

    context = {
        'vehicles': vehicles,
        'vehicle_data_json': vehicle_data,
    }
    return render(request, 'fleet/fleet_map.html', context)


def vehicle_detail(request, pk):
    """Detailed view of a single vehicle."""
    vehicle = get_object_or_404(
        Vehicle.objects.select_related('assigned_driver__user'),
        pk=pk
    )
    maintenance_logs = vehicle.maintenance_logs.all()[:10]
    recent_locations = vehicle.locations.all()[:20]
    drivers = Driver.objects.filter(status='available')

    context = {
        'vehicle': vehicle,
        'maintenance_logs': maintenance_logs,
        'recent_locations': recent_locations,
        'drivers': drivers,
    }
    return render(request, 'fleet/vehicle_detail.html', context)


def driver_list(request):
    """List all drivers."""
    drivers = Driver.objects.select_related('user').all()
    context = {'drivers': drivers}
    return render(request, 'fleet/driver_list.html', context)


def api_vehicle_locations(request):
    """API endpoint returning live vehicle GPS telematics data with optional filtering."""
    vehicle_id = request.GET.get('vehicle_id')
    status_filter = request.GET.get('status')
    
    vehicles = Vehicle.objects.select_related('assigned_driver__user')
    if vehicle_id:
        vehicles = vehicles.filter(pk=vehicle_id)
    elif status_filter:
        vehicles = vehicles.filter(status=status_filter)
    else:
        vehicles = vehicles.filter(status__in=['active', 'idle', 'maintenance'])

    data = []
    for vehicle in vehicles:
        loc = vehicle.locations.first()
        if loc:
            data.append({
                'id': vehicle.id,
                'plate': vehicle.plate_number,
                'make': vehicle.make,
                'model': vehicle.model,
                'type': vehicle.vehicle_type,
                'type_display': vehicle.get_vehicle_type_display(),
                'status': vehicle.status,
                'status_display': vehicle.get_status_display(),
                'driver': vehicle.assigned_driver.full_name if vehicle.assigned_driver else 'Unassigned',
                'driver_phone': vehicle.assigned_driver.phone if vehicle.assigned_driver else '',
                'lat': float(loc.latitude),
                'lng': float(loc.longitude),
                'speed': float(loc.speed),
                'heading': float(loc.heading),
                'timestamp': loc.timestamp.isoformat(),
            })
    return JsonResponse({'count': len(data), 'vehicles': data})


def api_record_location(request, pk):
    """API endpoint for IoT tracking devices or telematics to post new coordinates."""
    if request.method == 'POST':
        import json
        vehicle = get_object_or_404(Vehicle, pk=pk)
        try:
            body = json.loads(request.body)
            lat = body.get('lat') or body.get('latitude')
            lng = body.get('lng') or body.get('longitude')
            speed = body.get('speed', 0.0)
            heading = body.get('heading', 0.0)
            
            if lat is not None and lng is not None:
                new_loc = VehicleLocation.objects.create(
                    vehicle=vehicle,
                    latitude=lat,
                    longitude=lng,
                    speed=speed,
                    heading=heading
                )
                return JsonResponse({'status': 'success', 'location_id': new_loc.id})
            return JsonResponse({'status': 'error', 'message': 'Missing lat/lng'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=405)

