# main_users/views.py
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from .forms import UserRegistrationForm, UserProfileForm
from .models import MainUser
from django.urls import reverse_lazy

class RegisterView(View):
    """Handle user registration."""
    def get(self, request):
        """Display the registration form."""
        form = UserRegistrationForm()
        return render(request, 'main_users/register.html', {'form': form})

    def post(self, request):
        """Handle form submission."""
        form = UserRegistrationForm(request.POST, request.FILES)  # Handle file uploads (e.g., profile picture)
        if form.is_valid():
            form.save()  # Save the new user
            messages.success(request, 'Your account has been created successfully! You can now log in.')
            return redirect('login')  # Redirect to the login page after successful registration
        return render(request, 'main_users/register.html', {'form': form})


class LogoutView(LoginRequiredMixin, View):
    login_url = "/users/login/"
    http_method_names = ["post"]

    def post(self, request):
        logout(request)
        return redirect('login')


class ProfileView(LoginRequiredMixin, UpdateView):
    """Displays the user's profile information."""
    model = MainUser
    template_name = 'main_users/profile.html'
    form_class = UserProfileForm
    context_object_name = 'user'
    success_url = reverse_lazy('profile')

    def get_object(self):
        """Retrieve the logged-in user."""
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)
