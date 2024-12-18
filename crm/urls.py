from django.urls import path
from .views import DashboardAdminView, DashboardAsesorView, acceso_denegado, logout_view
from . import views
urlpatterns = [
    path('ad_dashboard/', DashboardAdminView.as_view(), name='dashboard_admin'),
    path('as_dashboard/', DashboardAsesorView.as_view(), name='dashboard_asesor'),
    path('error/', acceso_denegado, name='404'),
    path('logout/', logout_view, name='logout'),
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('clients/new/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),

    # URLs de Presupuestos (Budgets)
    path('budgets/', views.BudgetListView.as_view(), name='budget_list'),
    path('budgets/<int:pk>/', views.BudgetDetailView.as_view(), name='budget_detail'),
    path('budgets/new/', views.BudgetCreateView.as_view(), name='budget_create'),
    path('budgets/<int:pk>/edit/', views.BudgetUpdateView.as_view(), name='budget_update'),
    path('budgets/<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='budget_delete'),

    # URLs de Ventas Cerradas
    path('sales/', views.ClosedSalesListView.as_view(), name='closed_sales_list'),
    path('sales/<int:pk>/', views.ClosedSalesDetailView.as_view(), name='closed_sales_detail'),
    path('sales/new/', views.ClosedSalesCreateView.as_view(), name='closed_sales_create'),
    path('sales/<int:pk>/edit/', views.ClosedSalesUpdateView.as_view(), name='closed_sales_update'),
    path('sales/<int:pk>/delete/', views.ClosedSalesDeleteView.as_view(), name='closed_sales_delete'),
    
]