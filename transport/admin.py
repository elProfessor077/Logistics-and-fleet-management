from django.contrib import admin
from .models import TransportLine, Stop, LineStop, Schedule, Ticket


@admin.register(TransportLine)
class TransportLineAdmin(admin.ModelAdmin):
    list_display = ['line_number', 'name', 'line_type', 'frequency_minutes', 'is_active']
    list_filter = ['line_type', 'is_active']


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'zone', 'is_accessible']
    list_filter = ['zone']
    search_fields = ['name', 'code']


@admin.register(LineStop)
class LineStopAdmin(admin.ModelAdmin):
    list_display = ['line', 'stop', 'order', 'travel_time_from_previous']
    list_filter = ['line']


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['line', 'departure_time', 'arrival_time', 'days_of_week', 'is_active']
    list_filter = ['line', 'days_of_week']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'passenger_name', 'line', 'ticket_type', 'status', 'price', 'purchase_date']
    list_filter = ['ticket_type', 'status']
    readonly_fields = ['ticket_id']
