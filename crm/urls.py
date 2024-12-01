from django.urls import path
from . import views
urlpatterns = [
    path('', views.crm_view, name='basecrm'),  # Ruta para la vista de login
]