from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'organizer', 'is_approved')
    list_filter = ('is_approved', 'date')
    search_fields = ('title', 'description', 'location')