from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from events.models import Event, Booking
from groq import Groq
from datetime import datetime, timedelta
import pytz

# Initialize Groq client
groq_client = Groq(api_key=settings.GROQ_API_KEY)

def format_price(price):
    return f"<b>₹</b>{price:,.2f}" if price > 0 else "Free"

def get_event_info():
    current_time = timezone.now()
    next_week = current_time + timedelta(days=7)
    
    upcoming_events = Event.objects.filter(
        date__gte=current_time,
        date__lte=next_week
    ).values('title', 'date', 'price').order_by('date')[:5]

    if not upcoming_events:
        return "\nNo upcoming events scheduled for next week.\n"

    events_info = "\nUpcoming Events:\n"
    for event in upcoming_events:
        date_str = timezone.localtime(event['date']).strftime('%Y-%m-%d %H:%M')
        price_str = format_price(event['price'])
        events_info += f"• {event['title']} on {date_str} ({price_str})\n"

    return events_info

@login_required
@require_POST
def chat_message(request):
    try:
        message = request.POST.get('message')
        current_time = "2025-04-24 20:26:39"
        username = request.user.username
        
        if not message:
            return JsonResponse({'error': 'No message provided'}, status=400)
        
        events_info = get_event_info()
        
        user_bookings = Booking.objects.filter(
            attendee=request.user
        ).select_related('event').values('event__title', 'booking_date', 'quantity')
        
        bookings_info = "\nYour Current Bookings:\n"
        if user_bookings:
            for booking in user_bookings:
                bookings_info += f"• {booking['event__title']} booked for {timezone.localtime(booking['booking_date']).strftime('%Y-%m-%d %H:%M')}\n"
        else:
            bookings_info += "No current bookings found.\n"

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an Event Booking Assistant.
Current Time: {current_time}
User: {username}

{events_info}
{bookings_info}

Available Features:
1. Browse Events
   • View upcoming events
   • Get event details

2. Book Events
   • Select event
   • Payment options
   • Confirm booking

3. Manage Bookings
   • View bookings
   • Cancel bookings
   • Get details

Booking Rules:
• Login required
• No booking for past events
• Maximum 1 tickets per booking
• Cancellations allowed up to 24h before event
• Full refund for valid cancellations

IMPORTANT: Do not use any markdown formatting (no asterisks) in your responses. Use simple text formatting with bullet points (•) only."""
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            model="gemma2-9b-it",
            temperature=0.7,
            max_tokens=1000
        )
            
        response = chat_completion.choices[0].message.content

        # Add action buttons based on query type
        if "book" in message.lower():
            return JsonResponse({
                'status': 'success',
                'response': response,
                'timestamp': current_time,
                'actions': [
                    {
                        'type': 'button',
                        'text': 'Book Event',
                        'url': '/events/book/'
                    }
                ]
            })
        elif "cancel" in message.lower():
            return JsonResponse({
                'status': 'success',
                'response': response,
                'timestamp': current_time,
                'actions': [
                    {
                        'type': 'button',
                        'text': 'My Bookings',
                        'url': '/events/my-bookings/'
                    }
                ]
            })

        return JsonResponse({
            'status': 'success',
            'response': response,
            'timestamp': current_time
        })

    except Exception as e:
        print(f"Error in chat_message: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'response': "I'm having trouble connecting right now. Please try again.",
            'timestamp': current_time
        })