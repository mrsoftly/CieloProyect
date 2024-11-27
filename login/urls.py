# login/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # Ruta para la vista de login
]
