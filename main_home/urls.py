from django.urls import path
from django.views.generic import RedirectView
from .views import (
    AboutView,
    ContactView,
    DistributorView,
    HomeView,
    HowItWorksView,
    WhatWeDoView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('main/', DistributorView.as_view(), name='main_distributor'),
    path('dashboard/', RedirectView.as_view(pattern_name='main_distributor', permanent=False), name='dashboard_redirect'),
    path('what_we_do/', WhatWeDoView.as_view(), name='what_we_do'),
    path('how_it_works/', HowItWorksView.as_view(), name='how_it_works'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
]
