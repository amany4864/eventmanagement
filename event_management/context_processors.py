from django.utils import timezone

def current_time(request):
    return {
        'current_time': timezone.now(),
        'user_login': request.user.username if request.user.is_authenticated else None
    }