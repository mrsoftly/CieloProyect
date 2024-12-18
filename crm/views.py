from django.views.generic import (
    ListView, 
    DetailView, 
    CreateView, 
    UpdateView, 
    DeleteView
)
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth import logout
from crm.models import Client, Budget, closedSales
class GroupRequiredMixin(UserPassesTestMixin):
    """Mixin para validar pertenencia a grupos"""
    login_url = reverse_lazy('login')  # URL de inicio de sesión
    
    def test_func(self):
        # Si el usuario no está autenticado, redirigir al login
        if not self.request.user.is_authenticated:
            return False
        
        # Obtener los grupos permitidos (definidos en la vista)
        allowed_groups = getattr(self, 'allowed_groups', [])
        
        # Verificar si el usuario pertenece a alguno de los grupos permitidos
        return self.request.user.groups.filter(name__in=allowed_groups).exists()
    
    def handle_no_permission(self):
        # Redirigir a una página de acceso denegado
        return redirect('acceso_denegado')

class DashboardAdminView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    """Vista para dashboard de administradores"""
    template_name = 'info_admin.html'
    allowed_groups = ['admi']  # Solo accesible para el grupo Admin

class DashboardAsesorView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    """Vista para dashboard de asesores"""
    template_name = 'info_asesor.html'
    allowed_groups = ['asesor']  # Solo accesible para el grupo Asesor

def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calcula si el usuario pertenece a un grupo específico
        user = self.request.user
        context['is_asesor'] = user.groups.filter(name='asesor').exists()
        context['is_admin'] = user.groups.filter(name='admi').exists()
        return context

# Vista para manejar acceso denegado
def acceso_denegado(request):
    return render(request, '404.html')


# CRUD para Client
class ClientListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 10
    allowed_groups = ['asesor', 'admi']

class ClientDetailView(LoginRequiredMixin, GroupRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    allowed_groups = ['asesor', 'admi']

class ClientCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    model = Client
    template_name = 'clients/client_form.html'
    fields = [
        'first_name', 
        'paternal_last_name', 
        'maternal_last_name', 
        'email', 
        'phone_number'
    ]
    success_url = reverse_lazy('client_list')
    allowed_groups = ['asesor', 'admi']

class ClientUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    model = Client
    template_name = 'clients/client_form.html'
    fields = [
        'first_name', 
        'paternal_last_name', 
        'maternal_last_name', 
        'email', 
        'phone_number'
    ]
    success_url = reverse_lazy('client_list')
    allowed_groups = ['asesor', 'admi']

class ClientDeleteView(LoginRequiredMixin, GroupRequiredMixin, DeleteView):
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')
    allowed_groups = ['admi']  # Solo admin puede eliminar

# CRUD para Budget
class BudgetListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    model = Budget
    template_name = 'budgets/budget_list.html'
    context_object_name = 'budgets'
    paginate_by = 10
    allowed_groups = ['asesor', 'admi']

class BudgetDetailView(LoginRequiredMixin, GroupRequiredMixin, DetailView):
    model = Budget
    template_name = 'budgets/budget_detail.html'
    context_object_name = 'budget'
    allowed_groups = ['asesor', 'admi']

class BudgetCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    model = Budget
    template_name = 'budgets/budget_form.html'
    fields = [
        'emission_date', 
        'client', 
        'itinerary', 
        'cod_airline',
        'reserv_system', 
        'beeper', 
        'base_price', 
        'emisor_cost', 
        'sale_price', 
        'special_services', 
        'vendor', 
        'provider', 
        'state'
    ]
    success_url = reverse_lazy('budget_list')
    allowed_groups = ['asesor', 'admi']

class BudgetUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    model = Budget
    template_name = 'budgets/budget_form.html'
    fields = [
        'emission_date', 
        'client', 
        'itinerary', 
        'cod_airline',
        'reserv_system', 
        'beeper', 
        'base_price', 
        'emisor_cost', 
        'sale_price', 
        'special_services', 
        'vendor', 
        'provider', 
        'state'
    ]
    success_url = reverse_lazy('budget_list')
    allowed_groups = ['asesor', 'admi']

class BudgetDeleteView(LoginRequiredMixin, GroupRequiredMixin, DeleteView):
    model = Budget
    template_name = 'budgets/budget_confirm_delete.html'
    success_url = reverse_lazy('budget_list')
    allowed_groups = ['admi']  # Solo admin puede eliminar

# CRUD para ClosedSales
class ClosedSalesListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    model = closedSales
    template_name = 'sales/closed_sales_list.html'
    context_object_name = 'sales'
    paginate_by = 10
    allowed_groups = ['asesor', 'admi']

class ClosedSalesDetailView(LoginRequiredMixin, GroupRequiredMixin, DetailView):
    model = closedSales
    template_name = 'sales/closed_sales_detail.html'
    context_object_name = 'sale'
    allowed_groups = ['asesor', 'admi']

class ClosedSalesCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    model = closedSales
    template_name = 'sales/closed_sales_form.html'
    fields = [
        'budget', 
        'client', 
        'vendor', 
        'sales_price', 
        'fee_sale', 
        'fee_cielo', 
        'fee_vendor', 
        'paid'
    ]
    success_url = reverse_lazy('closed_sales_list')
    allowed_groups = ['asesor', 'admi']

    def get_form(self, form_class=None):
        # Si es un asesor, establecer el vendedor como el usuario actual
        form = super().get_form(form_class)
        if self.request.user.groups.filter(name='asesor').exists():
            form.fields['vendor'].initial = self.request.user.username
            form.fields['vendor'].disabled = True
        return form

class ClosedSalesUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    model = closedSales
    template_name = 'sales/closed_sales_form.html'
    fields = [
        'budget', 
        'client', 
        'vendor', 
        'sales_price', 
        'fee_sale', 
        'fee_cielo', 
        'fee_vendor', 
        'paid'
    ]
    success_url = reverse_lazy('closed_sales_list')
    allowed_groups = ['asesor', 'admi']

    def get_form(self, form_class=None):
        # Si es un asesor, no permitir cambiar el vendedor
        form = super().get_form(form_class)
        if self.request.user.groups.filter(name='asesor').exists():
            form.fields['vendor'].disabled = True
        return form

class ClosedSalesDeleteView(LoginRequiredMixin, GroupRequiredMixin, DeleteView):
    model = closedSales
    template_name = 'sales/closed_sales_confirm_delete.html'
    success_url = reverse_lazy('closed_sales_list')
    allowed_groups = ['admi']  # Solo admin puede eliminar

def logout_view(request):
    logout(request)
    return redirect('home')