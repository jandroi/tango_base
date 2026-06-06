from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView


class PublicPageView(TemplateView):
    """Shared base class for public marketing pages."""


class HomeView(PublicPageView):
    template_name = "main_home/home.html"


class WhatWeDoView(PublicPageView):
    template_name = "main_home/what_we_do.html"


class HowItWorksView(PublicPageView):
    template_name = "main_home/how_it_works.html"


class AboutView(PublicPageView):
    template_name = "main_home/about.html"


class ContactView(PublicPageView):
    template_name = "main_home/contact.html"


class DistributorView(LoginRequiredMixin, TemplateView):
    template_name = "main_home/distributor.html"
    login_url = reverse_lazy("login")
