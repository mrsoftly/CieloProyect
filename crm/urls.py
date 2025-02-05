from django.urls import path
from .views import DashboardAdminView,  acceso_denegado, logout_view
from . import views
urlpatterns = [
    path('ad_dashboard/', DashboardAdminView.as_view(), name='dashboard_admin'),
    #path('as_dashboard/', DashboardAsesorView.as_view(), name='dashboard_asesor'),
    path('acceso_denegado/', views.acceso_denegado, name='acceso_denegado'),
   # path('error/', acceso_denegado, name='404'),
    path('logout/', logout_view, name='logout'),

    ###------- admins clients urls ------------##
    path('admins_clients/',views.AdminsClientList.as_view(),name='client_list'),
    path('admins_clients/details/<int:pk>', views.AdminsClientDetails.as_view(), name= 'client_detail'),
    path('admins_clients/<int:pk>/edit/', views.AdminsClientUpdate.as_view(), name='client_update'),
    path('admins_clients/<int:pk>/delete/', views.AdminsClientDelete.as_view(), name='client_delete'),
    ###------- end admins clients urls --------####

    ## --------- admins budgets urls --------- ###
    path('admins_budgets/',views.AdminBudgetList.as_view(),name = 'budget_list'),
    path('admins_budgets/details/<int:pk>',views.AdminBudgetDetail.as_view(), name = 'budget_details'),
    path('admins_budgets/create/',views.AdminBudgetCreateView.as_view(), name='budget_create'),
    path('admins_budgets/edit/<int:pk>',views.AdminBudgetEdit.as_view(), name='budget_edit'),
    path('admins_budgets/delete/<int:pk>',views.AdminBudgetDeleteView.as_view(),name='budget_delete'),
    ## ----------- end admins budgets urls ------- ###

    path('admins_closedSales/',views.AdminClosedSalesList.as_view(),name = 'closedSales_list'),
    path('admins_closedSales/details/<int:pk>',views.AdminclosedSalesDetail.as_view(),name='closedSales_details'),
    path('admins_closedSales/edit/<int:pk>',views.AdminsclosedSalesUpdate.as_view(),name='closedSales_edit'),
    path('admins_closedSales/delete/<int:pk>',views.AdminclosedSaleDelete.as_view(),name='closedSales_delete'),
]