from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='event_list'),
    path('create/', views.CreateEventView.as_view(), name='create_event'),
    path('my-events/', views.MyEventsView.as_view(), name='my_events'),
    path('my-bookings/', views.MyBookingsView.as_view(), name='my_bookings'),
    path('book/<int:event_id>/', views.book_event, name='book_event'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),  # New URL
    # path('register/', views.register, name='register'),
     path('edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('search/', views.search_events, name='search_events'),

]