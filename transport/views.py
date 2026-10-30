import base64
import io
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from .models import TransportLine, Stop, LineStop, Schedule, Ticket


def line_list(request):
    """List all transport lines."""
    type_filter = request.GET.get('type', '')
    lines = TransportLine.objects.filter(is_active=True)

    if type_filter:
        lines = lines.filter(line_type=type_filter)

    context = {
        'lines': lines,
        'type_filter': type_filter,
        'type_choices': TransportLine.TYPE_CHOICES,
    }
    return render(request, 'transport/line_list.html', context)


def line_detail(request, pk):
    """Detail view of a transport line with stops and schedule."""
    line = get_object_or_404(TransportLine, pk=pk)
    stops = line.line_stops.select_related('stop').all()
    schedules = line.schedules.filter(is_active=True)

    # Build stop data for map
    stop_data = []
    for ls in stops:
        stop_data.append({
            'name': ls.stop.name,
            'lat': float(ls.stop.latitude),
            'lng': float(ls.stop.longitude),
            'zone': ls.stop.zone,
            'order': ls.order,
            'accessible': ls.stop.is_accessible,
        })

    context = {
        'line': line,
        'stops': stops,
        'schedules': schedules,
        'stop_data': stop_data,
    }
    return render(request, 'transport/line_detail.html', context)


def book_ticket(request):
    """Ticket booking form and processing."""
    lines = TransportLine.objects.filter(is_active=True).prefetch_related('line_stops__stop')

    if request.method == 'POST':
        line_id = request.POST.get('line')
        origin_stop_id = request.POST.get('origin_stop')
        destination_stop_id = request.POST.get('destination_stop')
        ticket_type = request.POST.get('ticket_type', 'single')
        passenger_name = request.POST.get('passenger_name', '')
        passenger_email = request.POST.get('passenger_email', '')
        passenger_phone = request.POST.get('passenger_phone', '')

        line = get_object_or_404(TransportLine, pk=line_id)
        origin_stop = get_object_or_404(Stop, pk=origin_stop_id)
        destination_stop = get_object_or_404(Stop, pk=destination_stop_id)

        # Calculate price based on ticket type
        price_map = {
            'single': 2.50,
            'return': 4.50,
            'day': 7.00,
            'weekly': 25.00,
            'monthly': 80.00,
        }
        price = price_map.get(ticket_type, 2.50)

        # Calculate validity
        validity_map = {
            'single': timedelta(hours=2),
            'return': timedelta(hours=24),
            'day': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': timedelta(days=30),
        }
        valid_until = timezone.now() + validity_map.get(ticket_type, timedelta(hours=2))

        # Generate QR code
        qr_data = ''
        try:
            import qrcode
            ticket_temp = Ticket(
                passenger_name=passenger_name,
                line=line,
                origin_stop=origin_stop,
                destination_stop=destination_stop,
                ticket_type=ticket_type,
                price=price,
                valid_until=valid_until,
            )
            ticket_temp.save()

            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(f"LOGICRAFT-TICKET|{ticket_temp.ticket_id}|{line.line_number}|{origin_stop.name}|{destination_stop.name}|{valid_until.isoformat()}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_data = base64.b64encode(buffer.getvalue()).decode()

            ticket_temp.qr_code = qr_data
            ticket_temp.save()

            messages.success(request, f'Ticket booked successfully! ID: {ticket_temp.ticket_id}')
            return redirect('transport:ticket_detail', pk=ticket_temp.pk)
        except ImportError:
            # qrcode library not installed, create ticket without QR
            ticket = Ticket.objects.create(
                passenger_name=passenger_name,
                passenger_email=passenger_email,
                passenger_phone=passenger_phone,
                line=line,
                origin_stop=origin_stop,
                destination_stop=destination_stop,
                ticket_type=ticket_type,
                price=price,
                valid_until=valid_until,
                qr_code='',
            )
            messages.success(request, f'Ticket booked successfully! ID: {ticket.ticket_id}')
            return redirect('transport:ticket_detail', pk=ticket.pk)

    # Build stops per line for JavaScript
    lines_stops_data = {}
    for line in lines:
        stops = []
        for ls in line.line_stops.select_related('stop').order_by('order'):
            stops.append({
                'id': ls.stop.id,
                'name': ls.stop.name,
                'zone': ls.stop.zone,
            })
        lines_stops_data[line.id] = stops

    context = {
        'lines': lines,
        'lines_stops_data': lines_stops_data,
        'ticket_type_choices': Ticket.TYPE_CHOICES,
    }
    return render(request, 'transport/book_ticket.html', context)


def ticket_detail(request, pk):
    """Display ticket details with QR code."""
    ticket = get_object_or_404(
        Ticket.objects.select_related('line', 'origin_stop', 'destination_stop'),
        pk=pk
    )
    context = {'ticket': ticket}
    return render(request, 'transport/ticket_detail.html', context)


def ticket_list(request):
    """List all tickets."""
    tickets = Ticket.objects.select_related('line', 'origin_stop', 'destination_stop').all()[:50]
    context = {'tickets': tickets}
    return render(request, 'transport/ticket_list.html', context)
