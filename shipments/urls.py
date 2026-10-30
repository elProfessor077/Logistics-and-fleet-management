from django.urls import path
from . import views

app_name = 'shipments'

urlpatterns = [
    path('', views.shipment_list, name='shipment_list'),
    path('create/', views.create_shipment, name='create_shipment'),
    path('track/', views.track_shipment, name='track_shipment'),
    path('<int:pk>/', views.shipment_detail, name='shipment_detail'),
]
