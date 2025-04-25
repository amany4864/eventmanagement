from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


from django.contrib.auth import views as auth_views

def home_redirect(request):
    return redirect('events:event_list')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('events/', include('events.urls')),
    path('accounts/', include('accounts.urls')),
    path('chatbot/', include('chatbot.urls')),
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='events:event_list'), name='logout'),
    # path('register/', views.register, name='register'),
]