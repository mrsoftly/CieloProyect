from django.urls import path
from .views import DashboardAdminView, DashboardAsesorView, acceso_denegado,logout_view,view_adclient,view_adsales,view_ases
urlpatterns = [
    path('ad_dashboard/', DashboardAdminView.as_view(), name='dashboard_admin'),
    path('as_dashboard/', DashboardAsesorView.as_view(), name='dashboard_asesor'),
    path('error/', acceso_denegado, name='404'),
    path('logout/', logout_view, name='logout'),
    path('clientes/',view_adclient,name = 'ad_clientes'),
    path('asesores/',view_ases,name = 'ad_asesor'),
    path('ventas/',view_adsales,name = 'ad_ventas'),
]