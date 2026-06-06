# main_users/urls.py
from django.urls import path
from django.contrib.auth.views import LoginView
from .views import RegisterView, LogoutView, ProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),  # Custom registration view
    path('login/', LoginView.as_view(template_name='main_users/login.html', redirect_authenticated_user=True), name='login'),  # Django's built-in login view
    path('logout/', LogoutView.as_view(), name='logout'),  # Django's built-in logout view
    path('profile/', ProfileView.as_view(), name='profile'),  # Class-based profile view


]
