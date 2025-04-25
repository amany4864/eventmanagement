from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import Event, Booking
from .forms import EventForm
from django.db.models import Q

from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import Event, Booking

class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 9

    def get_queryset(self):
        return Event.objects.filter(
            date__gte=timezone.now(),
            is_approved=True
        ).order_by('date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_time'] = timezone.now()
        return context

class CreateEventView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('events:my_events')

    def test_func(self):
        return self.request.user.user_type == 'organizer'

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        form.instance.is_approved = True
        messages.success(self.request, 'Event created successfully!')
        return super().form_valid(form)

class MyEventsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Event
    template_name = 'events/my_events.html'
    context_object_name = 'events'

    def test_func(self):
        return self.request.user.user_type == 'organizer'

    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user).order_by('date')

class MyBookingsView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'events/my_bookings.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(attendee=self.request.user).order_by('-booking_date')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_time'] = timezone.now()
        return context

def search_events(request):
    query = request.GET.get('q')
    current_time = timezone.now()
    
    if query:
        # Search in title, description, and location
        events = Event.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query),
            date__gte=current_time  # Only show upcoming events
        ).order_by('date')
    else:
        events = Event.objects.filter(date__gte=current_time).order_by('date')

    context = {
        'events': events,
        'query': query,
        'current_time': current_time
    }
    
    return render(request, 'events/search_results.html', context)
@login_required
def book_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user is an organizer
    if request.user.user_type == 'organizer':
        messages.error(request, 'Organizers cannot book events.')
        return redirect('events:event_list')
    
    # Check if event is in the past
    if event.date < timezone.now():
        messages.error(request, 'Cannot book past events.')
        return redirect('events:event_list')
    
    # Check if user already has a booking
    existing_booking = Booking.objects.filter(event=event, attendee=request.user).first()
    if existing_booking:
        if existing_booking.status == 'cancelled':
            existing_booking.status = 'confirmed'
            existing_booking.save()
            messages.success(request, f'Your booking for {event.title} has been reactivated!')
        else:
            messages.warning(request, 'You have already booked this event.')
        return redirect('events:my_bookings')
    
    # Check event capacity
    booked_count = Booking.objects.filter(event=event, status='confirmed').count()
    if booked_count >= event.capacity:
        messages.error(request, 'Sorry, this event is fully booked.')
        return redirect('events:event_list')
    
    # Handle free vs paid events
    if event.price > 0 and request.method != 'POST':
        messages.error(request, 'Please complete the payment process.')
        return redirect('events:event_list')
    
    # Create new booking
    Booking.objects.create(
        event=event,
        attendee=request.user,
        status='confirmed'
    )
    
    messages.success(request, f'Successfully booked {event.title}!')
    return redirect('events:my_bookings')


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    # Check if the user is the organizer of this event
    if event.organizer != request.user:
        messages.error(request, "You don't have permission to edit this event.")
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('events:my_events')
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/edit_event.html', {
        'form': form,
        'event': event
    })

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    # Check if the user is the organizer of this event
    if event.organizer != request.user:
        messages.error(request, "You don't have permission to delete this event.")
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('events:my_events')
    
    return render(request, 'events/delete_event.html', {'event': event})
@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, attendee=request.user)
    
    if booking.status == 'cancelled':
        messages.warning(request, 'This booking is already cancelled.')
        return redirect('events:my_bookings')
    
    if booking.event.date < timezone.now():
        messages.error(request, 'Cannot cancel bookings for past events.')
        return redirect('events:my_bookings')
    
    booking.status = 'cancelled'
    booking.save()
    
    # If this is a paid event, you might want to handle refund logic here
    if booking.event.price > 0:
        messages.success(request, f'Your booking for {booking.event.title} has been cancelled. A refund will be processed within 3-5 business days.')
    else:
        messages.success(request, f'Your booking for {booking.event.title} has been cancelled.')
    
    return redirect('events:my_bookings')