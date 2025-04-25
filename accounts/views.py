from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import UserRegistrationForm
from .models import User

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('events:event_list')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Registration successful!')
        return super().form_valid(form)

@login_required
def profile_view(request):
    user = request.user
    context = {
        'user': user,
        'total_events': user.event_set.count(),
        'active_events': user.event_set.filter(is_approved=True).count(),
        'pending_events': user.event_set.filter(is_approved=False).count(),
    }
    return render(request, 'accounts/profile.html', context)