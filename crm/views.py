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
from django.db.models import Sum
from django.utils import timezone
import calendar

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

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone
import calendar
from crm.models import closedSales  # Asegúrate de que esta es la importación correcta

from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import render
from .models import closedSales
import calendar

class DashboardAdminView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    """Vista para dashboard de administradores"""
    template_name = 'info_admin.html'
    allowed_groups = ['admi']  # Solo accesible para el grupo Admin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener la fecha actual
        today = timezone.now()

        # Calcular el primer día de la semana (lunes)
        start_of_week = today - timezone.timedelta(days=today.weekday())  # Lunes de esta semana

        # Calcular el primer día del mes (día 1 del mes)
        try:
            start_of_month = today.replace(day=1)  # Primer día del mes
        except ValueError:
            # Si ocurre un error al crear la fecha (por ejemplo, mes inválido), manejarlo adecuadamente
            start_of_month = today.replace(day=1)  # Asegurarse de que el valor sea válido

        # Ganancias de la semana
        weekly_revenue = closedSales.objects.filter(
            date_sale__gte=start_of_week,  # Filtra por fecha de venta (de la semana)
            date_sale__lte=today
        ).aggregate(Sum('fee_vendor'))['fee_vendor__sum'] or 0
        
        # Ganancias del mes
        monthly_revenue = closedSales.objects.filter(
            date_sale__gte=start_of_month,  # Filtra por fecha de venta (del mes)
            date_sale__lte=today
        ).aggregate(Sum('fee_vendor'))['fee_vendor__sum'] or 0

        # Top 3 vendedores con más ventas
        top_vendors = closedSales.objects.values('vendor').annotate(
            total_sales=Sum('fee_vendor')
        ).order_by('-total_sales')[:3]

        # Datos para las ganancias semanales y mensuales
        semanas = ["Semana 1", "Semana 2", "Semana 3", "Semana 4"]  # Aquí puedes ajustar las semanas reales si lo necesitas
        ganancias_semanales_data = [1000, 1500, 2000, 1800]  # Ajusta según los datos reales de tu base de datos

        meses = list(calendar.month_name[1:])  # Meses del año
        ganancias_mensuales_data = [12000, 15000, 17000, 20000]  # Ajusta según los datos reales de tu base de datos

        # Pasar los datos a la plantilla
        context['ganancias_semanales'] = ganancias_semanales_data
        context['ganancias_mensuales'] = ganancias_mensuales_data
        context['semanas'] = semanas
        context['meses'] = meses
        context['weekly_revenue'] = weekly_revenue
        context['monthly_revenue'] = monthly_revenue
        context['top_vendors'] = top_vendors

        return context


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


ADMIN_GROUP = 'admi'
ASESOR_GROUP = 'asesor'

class BudgetListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    model = Budget
    template_name = 'budgets/budget_list.html'
    context_object_name = 'budgets'
    paginate_by = 10
    allowed_groups = [ADMIN_GROUP, ASESOR_GROUP]

    def is_in_group(self, group_name):
        return self.request.user.groups.filter(name=group_name).exists()

    def get_queryset(self):
        if self.is_in_group(ADMIN_GROUP):
            return Budget.objects.all()
        if self.is_in_group(ASESOR_GROUP):
            return Budget.objects.filter(vendor=self.request.user.username)
        return Budget.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.is_in_group(ADMIN_GROUP)
        context['is_asesor'] = self.is_in_group(ASESOR_GROUP)
        return context


class BudgetDetailView(LoginRequiredMixin, GroupRequiredMixin, DetailView):
    model = Budget
    template_name = 'budgets/budget_detail.html'
    context_object_name = 'budget'
    allowed_groups = ['asesor', 'admi']

    def get_queryset(self):
        # Si es un administrador, mostrar todos los registros
        if self.request.user.groups.filter(name='admi').exists():
            return Budget.objects.all()
        
        # Si es un asesor, mostrar solo sus propios registros
        if self.request.user.groups.filter(name='asesor').exists():
            return Budget.objects.filter(vendor=self.request.user.username)
        
        # Si no pertenece a ningún grupo, no mostrar registros
        return Budget.objects.none()

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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.groups.filter(name='asesor').exists():
            form.fields['vendor'].initial = self.request.user.username
            form.fields['vendor'].disabled = True
        return form


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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.groups.filter(name='asesor').exists():
            form.fields['vendor'].disabled = True
        return form

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

    def is_in_group(self, group_name):
        """Verifica si el usuario pertenece a un grupo específico."""
        return self.request.user.groups.filter(name=group_name).exists()

    def get_queryset(self):
        """Devuelve el conjunto de datos según el grupo del usuario."""
        if self.is_in_group('admi'):
            return closedSales.objects.all()
        if self.is_in_group('asesor'):
            return closedSales.objects.filter(vendor=self.request.user.username)
        return closedSales.objects.none()

    def get_context_data(self, **kwargs):
        """Agrega variables adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.is_in_group('admi')
        return context


class ClosedSalesDetailView(LoginRequiredMixin, GroupRequiredMixin, DetailView):
    model = closedSales
    template_name = 'sales/closed_sales_detail.html'
    context_object_name = 'sale'
    allowed_groups = ['asesor', 'admi']

    def get_queryset(self):
        # Si es un administrador, mostrar todos los registros
        if self.request.user.groups.filter(name='admi').exists():
            return closedSales.objects.all()
        
        # Si es un asesor, mostrar solo sus propios registros
        if self.request.user.groups.filter(name='asesor').exists():
            return closedSales.objects.filter(vendor=self.request.user.username)
        
        # Si no pertenece a ningún grupo, no mostrar registros
        return closedSales.objects.none()

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