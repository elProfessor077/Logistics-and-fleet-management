from django.urls import path
from . import views

app_name = 'transport'

urlpatterns = [
    path('', views.line_list, name='line_list'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('book/', views.book_ticket, name='book_ticket'),
    path('ticket/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('line/<int:pk>/', views.line_detail, name='line_detail'),
]
