from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Warehouse, InventoryItem, StockMovement


def warehouse_list(request):
    """List all warehouses with utilization info."""
    city_filter = request.GET.get('city', '')
    warehouses = Warehouse.objects.filter(is_active=True)

    if city_filter:
        warehouses = warehouses.filter(city__icontains=city_filter)

    cities = Warehouse.objects.filter(is_active=True).values_list('city', flat=True).distinct().order_by('city')

    context = {
        'warehouses': warehouses,
        'cities': cities,
        'city_filter': city_filter,
    }
    return render(request, 'warehouse/warehouse_list.html', context)


def warehouse_detail(request, pk):
    """Detail view of a warehouse with inventory and movements."""
    warehouse = get_object_or_404(Warehouse, pk=pk)
    category_filter = request.GET.get('category', '')

    items = warehouse.inventory_items.all()
    if category_filter:
        items = items.filter(category=category_filter)

    movements = StockMovement.objects.filter(
        models.Q(from_warehouse=warehouse) | models.Q(to_warehouse=warehouse)
    ).select_related('item')[:20]

    low_stock_items = warehouse.inventory_items.filter(
        quantity__lte=models.F('min_stock')
    )

    context = {
        'warehouse': warehouse,
        'items': items,
        'movements': movements,
        'low_stock_items': low_stock_items,
        'category_filter': category_filter,
        'category_choices': InventoryItem.CATEGORY_CHOICES,
    }
    return render(request, 'warehouse/warehouse_detail.html', context)


def add_stock(request, pk):
    """Add stock to a warehouse item."""
    if request.method == 'POST':
        item = get_object_or_404(InventoryItem, pk=pk)
        quantity = int(request.POST.get('quantity', 0))
        reference = request.POST.get('reference', '')
        notes = request.POST.get('notes', '')

        if quantity > 0:
            item.quantity += quantity
            item.save()

            StockMovement.objects.create(
                item=item,
                movement_type='in',
                quantity=quantity,
                to_warehouse=item.warehouse,
                reference=reference,
                notes=notes,
                performed_by=request.user if request.user.is_authenticated else None,
            )

            # Update warehouse utilization
            item.warehouse.current_utilization += quantity
            item.warehouse.save()

            messages.success(request, f'Added {quantity} {item.get_unit_display()} of {item.name}')

        return redirect('warehouse:warehouse_detail', pk=item.warehouse.pk)
    return redirect('warehouse:warehouse_list')


def remove_stock(request, pk):
    """Remove stock from a warehouse item."""
    if request.method == 'POST':
        item = get_object_or_404(InventoryItem, pk=pk)
        quantity = int(request.POST.get('quantity', 0))
        reference = request.POST.get('reference', '')
        notes = request.POST.get('notes', '')

        if 0 < quantity <= item.quantity:
            item.quantity -= quantity
            item.save()

            StockMovement.objects.create(
                item=item,
                movement_type='out',
                quantity=quantity,
                from_warehouse=item.warehouse,
                reference=reference,
                notes=notes,
                performed_by=request.user if request.user.is_authenticated else None,
            )

            # Update warehouse utilization
            item.warehouse.current_utilization = max(0, item.warehouse.current_utilization - quantity)
            item.warehouse.save()

            messages.success(request, f'Removed {quantity} {item.get_unit_display()} of {item.name}')
        else:
            messages.error(request, 'Invalid quantity')

        return redirect('warehouse:warehouse_detail', pk=item.warehouse.pk)
    return redirect('warehouse:warehouse_list')


from django.db import models
