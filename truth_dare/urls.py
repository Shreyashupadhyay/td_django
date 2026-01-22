"""
URL configuration for truth_dare project.
"""
from django.contrib import admin
from django.urls import path, include
from game import views as game_views

urlpatterns = [
    # Custom admin dashboard must come before admin.site.urls
    path('admin/dashboard/', game_views.admin_dashboard, name='admin_dashboard'),
    path('admin/', admin.site.urls),
    path('', include('game.urls')),
]
