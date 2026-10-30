"""
Management command to seed comprehensive, realistic operational data for LogiCraft:
- Fleet (Vehicles, Drivers, GPS locations, Maintenance)
- Warehouses (Hubs, Inventory items, Low stock alerts, Movements)
- Shipments (Routes, Shipments, Multi-stage Event logs)
- Transport (Metro, Bus, Tram lines, Stops, Schedules, Tickets with QR codes)
- Admin Superuser
"""
import base64
import io
import random
from datetime import timedelta
import qrcode
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from fleet.models import Driver, Vehicle, VehicleLocation, MaintenanceLog
from warehouse.models import Warehouse, InventoryItem, StockMovement
from shipments.models import Route, Shipment, ShipmentEvent
from transport.models import TransportLine, Stop, LineStop, Schedule, Ticket


class Command(BaseCommand):
    help = 'Seeds realistic sample data for all LogiCraft operational modules'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting LogiCraft database seeding...'))

        # 1. Admin Superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@logicraft.io',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created superuser: admin / admin123'))
        else:
            self.stdout.write('Superuser admin verified.')

        # 2. Drivers
        driver_configs = [
            ('vikram.singh', 'Vikram', 'Singh', 'DL-MH-2018-9941', '+91 98201 11223'),
            ('rajesh.kumar', 'Rajesh', 'Kumar', 'DL-KA-2019-3382', '+91 98450 44556'),
            ('amit.sharma', 'Amit', 'Sharma', 'DL-DL-2020-7714', '+91 98110 77889'),
            ('priya.patel', 'Priya', 'Patel', 'DL-GJ-2021-1250', '+91 98250 12345'),
            ('sunil.verma', 'Sunil', 'Verma', 'DL-TN-2017-8890', '+91 94440 66778'),
        ]

        drivers = []
        for uname, fname, lname, lic, phone in driver_configs:
            u, _ = User.objects.get_or_create(
                username=uname,
                defaults={'first_name': fname, 'last_name': lname, 'email': f'{uname}@logicraft.io'}
            )
            d, _ = Driver.objects.get_or_create(
                license_number=lic,
                defaults={
                    'user': u,
                    'phone': phone,
                    'status': 'available',
                    'license_expiry': timezone.now().date() + timedelta(days=730),
                }
            )
            drivers.append(d)

        self.stdout.write(self.style.SUCCESS(f'Verified {len(drivers)} drivers.'))

        # 3. Fleet Vehicles
        vehicle_configs = [
            ('MH-04-AZ-8921', 'truck', 'Volvo', 'FH16 750', 2022, 'diesel', 24000.0, 114200.0, 'active', drivers[0]),
            ('MH-12-BQ-4310', 'truck', 'Tata Motors', 'Prima 2830.K', 2021, 'diesel', 16000.0, 84300.0, 'active', drivers[1]),
            ('DL-01-CX-7789', 'van', 'Mercedes-Benz', 'Sprinter 319 CDI', 2023, 'electric', 3500.0, 31200.0, 'active', drivers[2]),
            ('KA-05-EM-6022', 'trailer', 'Ashok Leyland', 'Captain 40i', 2020, 'diesel', 28000.0, 172900.0, 'idle', drivers[3]),
            ('TN-09-RT-1194', 'truck', 'Scania', 'R500 Highline Reefer', 2022, 'diesel', 22000.0, 96500.0, 'active', drivers[4]),
            ('GJ-06-KL-5531', 'truck', 'BharatBenz', '3528C Heavy Tanker', 2019, 'cng', 30000.0, 210400.0, 'maintenance', None),
        ]

        vehicles = []
        for plate, vtype, make, model, year, fuel, cap, mil, status, driver in vehicle_configs:
            v, _ = Vehicle.objects.get_or_create(
                plate_number=plate,
                defaults={
                    'vehicle_type': vtype,
                    'make': make,
                    'model': model,
                    'year': year,
                    'fuel_type': fuel,
                    'capacity_kg': cap,
                    'mileage': mil,
                    'status': status,
                    'assigned_driver': driver,
                    'last_service_date': timezone.now().date() - timedelta(days=random.randint(15, 90)),
                    'next_service_date': timezone.now().date() + timedelta(days=random.randint(30, 120)),
                }
            )
            vehicles.append(v)

        # Vehicle GPS Locations
        gps_seeds = [
            (vehicles[0], 19.0760, 72.8777, 62.5, 45.0),    # Mumbai
            (vehicles[1], 18.5204, 73.8567, 54.0, 120.0),   # Pune
            (vehicles[2], 28.6139, 77.2090, 38.0, 90.0),    # Delhi
            (vehicles[3], 12.9716, 77.5946, 0.0, 0.0),      # Bangalore
            (vehicles[4], 13.0827, 80.2707, 71.2, 185.0),   # Chennai
            (vehicles[5], 22.3072, 73.1812, 0.0, 0.0),      # Vadodara
        ]

        for v, lat, lng, spd, head in gps_seeds:
            VehicleLocation.objects.create(
                vehicle=v,
                latitude=lat,
                longitude=lng,
                speed=spd,
                heading=head,
                timestamp=timezone.now()
            )

        # Maintenance logs
        for v in vehicles[:4]:
            if not v.maintenance_logs.exists():
                MaintenanceLog.objects.create(
                    vehicle=v,
                    maintenance_type='routine',
                    description='20,000 km Periodic Inspection, engine oil flush, synthetic filter replacement, suspension check.',
                    cost=18500.00,
                    date=timezone.now().date() - timedelta(days=40),
                    next_due=timezone.now().date() + timedelta(days=80),
                    mechanic='Authorized Service Center'
                )

        self.stdout.write(self.style.SUCCESS(f'Verified {len(vehicles)} fleet vehicles and GPS records.'))

        # 4. Warehouses
        warehouse_configs = [
            ('Mumbai Central Gateway Hub', 'WH-BOM-01', 'Plot 44, Nhava Sheva Logistics Park', 'Mumbai', 'Maharashtra', 50000, 34200, 19.0760, 72.8777),
            ('Delhi NCR Mega Depot', 'WH-DEL-02', 'Sector 88 Industrial Corridor', 'Gurugram', 'Haryana', 75000, 58100, 28.6139, 77.2090),
            ('Bangalore Tech Logistics Hub', 'WH-BLR-03', 'Electronic City Phase II, Hosur Rd', 'Bengaluru', 'Karnataka', 40000, 29800, 12.9716, 77.5946),
            ('Chennai Port Coastal Terminal', 'WH-MAA-04', 'Ennore Port Free Trade Zone', 'Chennai', 'Tamil Nadu', 60000, 41500, 13.0827, 80.2707),
            ('Pune Industrial Consolidation Center', 'WH-PNQ-05', 'Chakan MIDC Industrial Area Phase 3', 'Pune', 'Maharashtra', 35000, 18400, 18.5204, 73.8567),
        ]

        warehouses = []
        for name, code, addr, city, state, cap, util, lat, lng in warehouse_configs:
            w, _ = Warehouse.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'address': addr,
                    'city': city,
                    'state': state,
                    'capacity': cap,
                    'current_utilization': util,
                    'manager': admin_user,
                    'is_active': True,
                    'latitude': lat,
                    'longitude': lng,
                }
            )
            warehouses.append(w)

        # Inventory Items & Movements
        inventory_specs = [
            ('SKU-ELE-001', 'Microcontroller Control Units', 'electronics', 1450, 'pcs', 200, 3000, 120.00, warehouses[0]),
            ('SKU-AUT-002', 'Commercial Brake Disc Rotors', 'spare_parts', 480, 'boxes', 150, 1000, 85.00, warehouses[0]),
            ('SKU-PER-003', 'Organic Fresh Produce Cartons', 'perishable', 35, 'boxes', 100, 1200, 45.00, warehouses[0]), # LOW STOCK
            ('SKU-PHR-004', 'Insulin Cold-Chain Vials', 'perishable', 8200, 'boxes', 1500, 15000, 24.50, warehouses[1]),
            ('SKU-BLK-005', 'High-Density Industrial Pellets', 'raw_materials', 22000, 'kg', 5000, 40000, 3.20, warehouses[1]),
            ('SKU-ELE-006', 'High-Efficiency Solar Inverters', 'electronics', 290, 'boxes', 80, 600, 480.00, warehouses[2]),
            ('SKU-AUT-007', 'Heavy-Duty Lithium Fleet Batteries', 'spare_parts', 12, 'boxes', 25, 200, 1250.00, warehouses[2]), # LOW STOCK
            ('SKU-FMC-008', 'Consumer Fast-Moving Goods Pallets', 'finished_goods', 1420, 'pallets', 300, 3500, 210.00, warehouses[3]),
        ]

        for sku, name, cat, qty, unit, min_s, max_s, price, wh in inventory_specs:
            item, _ = InventoryItem.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'category': cat,
                    'quantity': qty,
                    'unit': unit,
                    'min_stock': min_s,
                    'max_stock': max_s,
                    'unit_price': price,
                    'warehouse': wh,
                }
            )
            if not item.movements.exists():
                StockMovement.objects.create(
                    item=item,
                    movement_type='in',
                    quantity=qty,
                    to_warehouse=wh,
                    reference=f'IN-PO-{random.randint(1000, 9999)}',
                    notes='Initial intake verification scan.',
                    performed_by=admin_user
                )

        self.stdout.write(self.style.SUCCESS(f'Verified {len(warehouses)} warehouses with inventory & low stock items.'))

        # 5. Routes & Shipments
        r1, _ = Route.objects.get_or_create(
            name='Western Freight Corridor: Mumbai → Pune',
            defaults={
                'origin': 'Mumbai Central Gateway Hub',
                'destination': 'Pune Industrial Consolidation Center',
                'distance_km': 148.5,
                'estimated_hours': 3.5,
                'is_active': True,
            }
        )
        r2, _ = Route.objects.get_or_create(
            name='Golden Quadrilateral Express: Delhi → Mumbai',
            defaults={
                'origin': 'Delhi NCR Mega Depot',
                'destination': 'Mumbai Central Gateway Hub',
                'distance_km': 1412.0,
                'estimated_hours': 26.0,
                'is_active': True,
            }
        )

        shipment_samples = [
            (
                'TRK-2024-8841', 'Mumbai Central Gateway Hub', 'Pune Industrial MIDC Hub',
                'Tesla Gigafactory Supply', '+91 98200 44551', 'inbound@tesla-supplier.com',
                'Bajaj Auto Assembly Plant', '+91 98220 99882', 'procurement@bajaj.com',
                1420.5, '120x80x160 cm', 'Critical automotive power electronics',
                'urgent', 'in_transit', vehicles[0], r1
            ),
            (
                'TRK-2024-9102', 'Delhi NCR Mega Depot', 'Mumbai Central Gateway Hub',
                'Biocon Life Sciences', '+91 11 2678 1234', 'logistics@biocon.com',
                'Lilavati Hospital & Research', '+91 22 2675 0000', 'pharma@lilavati.org',
                380.0, '60x60x80 cm', 'Temperature-controlled cold-chain vaccines',
                'urgent', 'out_for_delivery', vehicles[4], r2
            ),
            (
                'TRK-2024-6420', 'Bangalore Tech Logistics Hub', 'Chennai Port Coastal Terminal',
                'Infosys Hardware Lab', '+91 80 2852 0261', 'dispatch@infosys.com',
                'Global Freight Shipping Line', '+91 44 2536 1122', 'cargo@maersk.com',
                5200.0, '20ft Sea Container', 'Server rack enterprise infrastructure for export',
                'high', 'delivered', vehicles[3], None
            ),
            (
                'TRK-2024-3315', 'Pune MIDC Logistics', 'Delhi NCR Mega Depot',
                'Tata Motors Component Div', '+91 20 6613 0000', 'components@tatamotors.com',
                'Northern Dealership Network', '+91 11 4151 7788', 'fleetparts@delhidealers.com',
                840.0, '100x100x120 cm', 'Replacement chassis hydraulic assemblies',
                'normal', 'picked_up', vehicles[1], None
            ),
        ]

        for trk, orig, dest, sname, sphone, semail, rname, rphone, remail, wt, dim, desc, prio, stat, veh, rte in shipment_samples:
            shp, created = Shipment.objects.get_or_create(
                tracking_number=trk,
                defaults={
                    'origin': orig,
                    'destination': dest,
                    'sender_name': sname,
                    'sender_phone': sphone,
                    'sender_email': semail,
                    'receiver_name': rname,
                    'receiver_phone': rphone,
                    'receiver_email': remail,
                    'weight_kg': wt,
                    'dimensions': dim,
                    'description': desc,
                    'priority': prio,
                    'status': stat,
                    'vehicle': veh,
                    'route': rte,
                    'estimated_delivery': timezone.now() + timedelta(days=2),
                    'actual_delivery': timezone.now() - timedelta(hours=4) if stat == 'delivered' else None,
                }
            )
            if created or not shp.events.exists():
                ShipmentEvent.objects.create(
                    shipment=shp,
                    status='pending',
                    location=orig,
                    notes='Consignment booked and waybill registered in system.',
                    timestamp=timezone.now() - timedelta(days=1, hours=8)
                )
                ShipmentEvent.objects.create(
                    shipment=shp,
                    status='picked_up',
                    location=orig,
                    notes='Cargo loaded and security sealed onto line-haul vehicle.',
                    timestamp=timezone.now() - timedelta(hours=20)
                )
                if stat in ['in_transit', 'out_for_delivery', 'delivered']:
                    ShipmentEvent.objects.create(
                        shipment=shp,
                        status='in_transit',
                        location='National Highway Toll Plaza Mile 84',
                        notes='Vehicle cleared express electronic toll weighbridge.',
                        timestamp=timezone.now() - timedelta(hours=8)
                    )
                if stat in ['out_for_delivery', 'delivered']:
                    ShipmentEvent.objects.create(
                        shipment=shp,
                        status='out_for_delivery',
                        location=dest,
                        notes='Out with designated courier team for final drop-off verification.',
                        timestamp=timezone.now() - timedelta(hours=2)
                    )
                if stat == 'delivered':
                    ShipmentEvent.objects.create(
                        shipment=shp,
                        status='delivered',
                        location=dest,
                        notes='Received in full condition. Digital e-signature captured.',
                        timestamp=timezone.now() - timedelta(hours=1)
                    )

        self.stdout.write(self.style.SUCCESS('Verified sample shipments with milestone event timelines.'))

        # 6. Public Transport (Metro, Bus, Tram)
        lines_data = [
            ('Metro Line 1 (Blue Rapid)', 'M1', 'metro', '#0284c7', 6, 'Elevated rapid transit connecting financial downtown to northern terminals.'),
            ('Metro Line 2 (Red Corridor)', 'M2', 'metro', '#ef4444', 8, 'East-West underground transit linking international airport to tech corridor.'),
            ('City Express Bus 104', 'EX-104', 'bus', '#10b981', 12, 'High-capacity electric articulated bus along arterial coastal highway.'),
            ('Heritage Coastal Tramway', 'T-01', 'tram', '#f59e0b', 15, 'Scenic street-level tramway traversing historic seaside promenade and arts district.'),
        ]

        t_lines = []
        for name, lnum, ltype, color, freq, desc in lines_data:
            line, _ = TransportLine.objects.get_or_create(
                line_number=lnum,
                defaults={
                    'name': name,
                    'line_type': ltype,
                    'color_code': color,
                    'frequency_minutes': freq,
                    'description': desc,
                    'is_active': True,
                }
            )
            t_lines.append(line)

        # Stops
        stops_data = [
            ('Central Railway Terminal', 'CRT-01', 18.9696, 72.8193, '1', True),
            ('Victoria Financial Square', 'VFS-02', 18.9322, 72.8317, '1', True),
            ('University South Campus', 'USC-03', 18.9750, 72.8250, '1', True),
            ('Harbor Gateway Pier', 'HGP-04', 18.9220, 72.8347, '1', True),
            ('Bandra West Tech Park', 'BWP-05', 19.0596, 72.8295, '2', True),
            ('Kurla Transit Interchange', 'KTI-06', 19.0657, 72.8794, '2', True),
            ('Andheri East Metro Hub', 'AEM-07', 19.1197, 72.8464, '2', True),
            ('International Airport T2', 'AIR-08', 19.0896, 72.8656, '3', True),
            ('Borivali National Station', 'BNS-09', 19.2288, 72.8541, '4', True),
        ]

        stops_map = {}
        for sname, scode, slat, slng, szone, sacc in stops_data:
            st, _ = Stop.objects.get_or_create(
                code=scode,
                defaults={
                    'name': sname,
                    'latitude': slat,
                    'longitude': slng,
                    'zone': szone,
                    'is_accessible': sacc,
                    'address': f'{sname}, Metropolitan Transit Zone {szone}'
                }
            )
            stops_map[scode] = st

        # Assign stops to Metro Line 1
        m1_stop_codes = ['CRT-01', 'VFS-02', 'USC-03', 'BWP-05', 'AEM-07', 'BNS-09']
        for idx, code in enumerate(m1_stop_codes, start=1):
            LineStop.objects.get_or_create(
                line=t_lines[0],
                stop=stops_map[code],
                defaults={'order': idx, 'travel_time_from_previous': 5 if idx > 1 else 0}
            )

        # Assign stops to Metro Line 2
        m2_stop_codes = ['AIR-08', 'AEM-07', 'KTI-06', 'BWP-05']
        for idx, code in enumerate(m2_stop_codes, start=1):
            LineStop.objects.get_or_create(
                line=t_lines[1],
                stop=stops_map[code],
                defaults={'order': idx, 'travel_time_from_previous': 7 if idx > 1 else 0}
            )

        # Assign stops to Tram
        tram_stop_codes = ['HGP-04', 'VFS-02', 'CRT-01', 'USC-03']
        for idx, code in enumerate(tram_stop_codes, start=1):
            LineStop.objects.get_or_create(
                line=t_lines[3],
                stop=stops_map[code],
                defaults={'order': idx, 'travel_time_from_previous': 4 if idx > 1 else 0}
            )

        # Schedules
        if not t_lines[0].schedules.exists():
            Schedule.objects.create(
                line=t_lines[0],
                departure_time='06:00:00',
                arrival_time='23:30:00',
                days_of_week='weekday',
                is_active=True
            )
            Schedule.objects.create(
                line=t_lines[0],
                departure_time='07:00:00',
                arrival_time='23:00:00',
                days_of_week='saturday',
                is_active=True
            )

        # Sample Tickets with QR codes
        if not Ticket.objects.exists():
            ticket_seeds = [
                ('Rahul Verma', 'rahul.v@example.com', t_lines[0], stops_map['CRT-01'], stops_map['AEM-07'], 'single', 2.50),
                ('Sneha Kapoor', 'sneha.k@example.com', t_lines[0], stops_map['VFS-02'], stops_map['BNS-09'], 'day', 7.00),
                ('David Miller', 'david.m@example.com', t_lines[1], stops_map['AIR-08'], stops_map['BWP-05'], 'return', 4.50),
            ]

            for pname, pemail, pline, ostop, dstop, ttype, price in ticket_seeds:
                tk = Ticket(
                    passenger_name=pname,
                    passenger_email=pemail,
                    line=pline,
                    origin_stop=ostop,
                    destination_stop=dstop,
                    ticket_type=ttype,
                    price=price,
                    valid_until=timezone.now() + timedelta(days=1),
                    status='active'
                )
                tk.save()

                # Generate QR code
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(f"LOGICRAFT-PASS|{tk.ticket_id}|{pline.line_number}|{ostop.name}|{dstop.name}|VALID")
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                tk.qr_code = base64.b64encode(buffer.getvalue()).decode()
                tk.save()

        self.stdout.write(self.style.SUCCESS('Verified transit lines, stations, schedules, and active tickets.'))
        self.stdout.write(self.style.SUCCESS('LogiCraft database seeding completed successfully!'))
