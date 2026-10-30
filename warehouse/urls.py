from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    path('', views.warehouse_list, name='warehouse_list'),
    path('<int:pk>/', views.warehouse_detail, name='warehouse_detail'),
    path('item/<int:pk>/add/', views.add_stock, name='add_stock'),
    path('item/<int:pk>/remove/', views.remove_stock, name='remove_stock'),
]
