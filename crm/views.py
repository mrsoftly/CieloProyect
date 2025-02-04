import calendar
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib.auth.models import User, Group
from crm.models import Client, Budget, closedSales
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncWeek, TruncMonth
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ValidationError
from django import forms
from django.views.decorators.csrf import csrf_exempt

class GroupRequiredMixin(UserPassesTestMixin):
    login_url = reverse_lazy('login')

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False

        allowed_groups = getattr(self, 'allowed_groups', [])
        if isinstance(allowed_groups, str):
            allowed_groups = [allowed_groups]

        return self.request.user.groups.filter(name__in=allowed_groups).exists()

    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permiso para acceder a esta página.')
        return redirect('acceso_denegado')

ADMIN_GROUP = 'admi'
ASESOR_GROUP = 'asesor'

from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum, Avg
from django.db.models.functions import TruncWeek, TruncMonth
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import calendar

from .models import closedSales, Budget

class DashboardAdminView(LoginRequiredMixin, TemplateView):
    """Vista para el dashboard de administradores."""
    template_name = 'admins/info_admin.html'
    allowed_groups = 'admi'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()

        # Obtener filtros de la solicitud GET con valores por defecto
        selected_year = int(self.request.GET.get('year', today.year))
        selected_month = int(self.request.GET.get('month', today.month))
        selected_day = int(self.request.GET.get('day', today.day))

        # Manejo de fechas seguras
        try:
            start_date = timezone.make_aware(datetime(selected_year, selected_month, selected_day))
            end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
        except ValueError:
            messages.error(self.request, "Fecha inválida seleccionada. Usando fecha actual.")
            start_date = timezone.make_aware(datetime(today.year, today.month, today.day))
            end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
            selected_year, selected_month, selected_day = today.year, today.month, today.day

        # Obtener datos filtrados
        filtered_sales = closedSales.objects.filter(date_sale__gte=start_date, date_sale__lte=end_date)
        filtered_budgets = Budget.objects.filter(emission_date__gte=start_date, emission_date__lte=end_date)

        # Estadísticas de presupuestos
        budget_stats = {
            'total': filtered_budgets.count(),
            'pending': filtered_budgets.filter(state='pendiente').count(),
            'accepted': filtered_budgets.filter(state='aceptado').count(),
            'rejected': filtered_budgets.filter(state='rechazado').count()
        }

        # Ganancias semanales
        weekly_sales = filtered_sales.annotate(week=TruncWeek('date_sale')) \
            .values('week') \
            .annotate(total=Sum('fee_vendor')) \
            .order_by('week')

        weekly_sales_dict = {sale['week']: sale['total'] for sale in weekly_sales}
        semanas = [f"Semana {4 - i}" for i in range(4)]
        ganancias_semanales_data = [weekly_sales_dict.get(today - timedelta(weeks=i), 0) for i in range(4)]

        # Ganancias mensuales
        monthly_sales = filtered_sales.annotate(month=TruncMonth('date_sale')) \
            .values('month') \
            .annotate(total=Sum('fee_vendor')) \
            .order_by('month')

        monthly_sales_dict = {sale['month']: sale['total'] for sale in monthly_sales}
        meses = list(calendar.month_name[1:])
        ganancias_mensuales_data = []

        for i in range(12):
            month_date = today.replace(day=1) - relativedelta(months=i)
            month_key = timezone.make_aware(datetime(month_date.year, month_date.month, 1))
            ganancia = monthly_sales_dict.get(month_key, 0)
            ganancias_mensuales_data.insert(0, float(ganancia) if ganancia else 0)

        # Top vendedores
        top_vendors = list(
            filtered_sales.values(
                'vendor__username', 'vendor__first_name', 'vendor__last_name'
            )
            .annotate(total_sales=Sum('fee_vendor'))
            .order_by('-total_sales')[:3]
        )

        # Formatear los nombres de los vendedores
        formatted_top_vendors = [
            {
                'vendor': f"{vendor['vendor__first_name']} {vendor['vendor__last_name']}".strip() or vendor['vendor__username'],
                'total_sales': vendor['total_sales']
            }
            for vendor in top_vendors
        ]

        # Rellenar con datos vacíos si hay menos de 3 vendedores
        while len(formatted_top_vendors) < 3:
            formatted_top_vendors.append({'vendor': 'Sin datos', 'total_sales': 0})

        # Años disponibles para filtro
        available_years = [date.year for date in closedSales.objects.dates('date_sale', 'year')]
        if not available_years:
            available_years = [today.year]

        # Serializar datos para gráficos
        context.update({
            'weekly_revenue': sum(weekly_sales_dict.values()),
            'monthly_revenue': filtered_sales.aggregate(Sum('fee_vendor'))['fee_vendor__sum'] or 0,
            'top_vendors': formatted_top_vendors,
            'ganancias_semanales': json.dumps(ganancias_semanales_data),
            'ganancias_mensuales': json.dumps(ganancias_mensuales_data),
            'semanas': json.dumps(semanas),
            'meses': json.dumps(meses),
            'budget_stats': budget_stats,
            'stats': {
                'total_clients': filtered_sales.values('client').distinct().count(),
                'total_sales': filtered_sales.count(),
                'average_sale': round(filtered_sales.aggregate(avg=Avg('fee_vendor'))['avg'] or 0, 2)
            },
            'available_years': available_years,
            'months': list(enumerate(calendar.month_name[1:], start=1)),
            'selected_year': selected_year,
            'selected_month': selected_month,
            'selected_day': selected_day,
            'days_range': list(range(1, 32)),
            'has_data': filtered_sales.exists()
        })

        return context

#### ---- admins clients -------####
class AdminsClientList(LoginRequiredMixin, GroupRequiredMixin, ListView):
    model = Client
    context_object_name = 'clients'
    template_name = 'admins/admins_clients/client_list.html'  # Use template_name instead of template
    paginate_by = 5
    allowed_groups = ADMIN_GROUP

class AdminsClientDetails(LoginRequiredMixin,GroupRequiredMixin,DetailView):
    model = Client
    context_object_name = 'client'
    template_name = 'admins/admins_clients/client_detail.html'
    allowed_groups = ADMIN_GROUP

class AdminsClientUpdate (LoginRequiredMixin,GroupRequiredMixin,UpdateView):
    model = Client
    template_name = 'admins/admins_clients/client_edit.html'
    fields = ['first_name', 'paternal_last_name', 'maternal_last_name', 'email', 'phone_number']
    success_url = reverse_lazy('client_list')
    allowed_groups = ADMIN_GROUP
 
class AdminsClientDelete (LoginRequiredMixin,GroupRequiredMixin,DeleteView):
    model = Client
    template_name = 'admins/admins_clients/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')
    allowed_groups = [ADMIN_GROUP]
###### ------------- end clients admin ----------- #####

class AdminBudgetList(LoginRequiredMixin, GroupRequiredMixin, ListView):
    model = Budget
    context_object_name = 'budgets '  # Este es el nombre que usarás en la plantilla.
    template_name = 'admins/admins_budgtes/budget_list.html'
    paginate_by = 5  # Esto paginará los resultados de 5 en 5.
    allowed_groups = ADMIN_GROUP

    # Este método se asegura de que los datos sean pasados a la plantilla con la paginación correcta.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Asegúrate de que la variable 'budgets' esté en el contexto.
        context['budgets'] = self.get_queryset()
        return context
    
class AdminBudgetDetail(LoginRequiredMixin, GroupRequiredMixin, DetailView):
    model = Budget
    context_object_name = 'budget'  # Se utiliza 'budget' porque estamos mostrando detalles de un solo presupuesto.
    template_name = 'admins/admins_budgtes/budget_detail.html'  # Asegúrate de que la ruta del template sea correcta.
    allowed_groups = ADMIN_GROUP

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ya no es necesario agregar budgets al contexto, ya que 'object' ya lo provee DetailView.
        return context



class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = [
            'emission_date', 'client', 'itinerary', 'cod_airline',
            'reserv_system', 'beeper', 'base_price', 'emisor_cost',
            'sale_price', 'special_services', 'vendor', 'provider', 'state'
        ]

class AdminBudgetCreateView(LoginRequiredMixin, GroupRequiredMixin,CreateView):
    allowed_groups = ADMIN_GROUP
    model = Budget
    form_class = BudgetForm
    template_name = 'admins/admins_budgtes/budget_form.html'
    success_url = reverse_lazy('budget_list') 

class AdminBudgetEdit(LoginRequiredMixin, GroupRequiredMixin,UpdateView):
    model = Budget
    template_name = 'admins/admins_budgtes/budget_form.html'
    form_class = BudgetForm
    success_url = reverse_lazy('budget_list')
    allowed_groups = ADMIN_GROUP  # Use defined group names

    def form_valid(self, form):
        budget = form.save()
        messages.success(self.request, 'Presupuesto actualizado exitosamente.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al actualizar el presupuesto. Revisa los campos.')
        return super().form_invalid(form)
    
class AdminBudgetDeleteView(LoginRequiredMixin, GroupRequiredMixin, DeleteView):
    model = Budget
    template_name = 'admins/admins_budgtes/budget_confirm_delete.html'
    success_url = reverse_lazy('budget_list')
    allowed_groups = ADMIN_GROUP

    def get_queryset(self): # Admins can delete all
        return Budget.objects.all()

    def form_valid(self, form):
        self.object.delete()  # Delete the object explicitly
        messages.success(self.request, 'Presupuesto eliminado exitosamente.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al eliminar el presupuesto.')
        return super().form_invalid(form)

class AdminClosedSalesList(LoginRequiredMixin, GroupRequiredMixin, ListView):
    model = closedSales  # Usa el nombre correcto del modelo con CamelCase
    context_object_name = 'sales'  # Quitado el espacio extra y usado un nombre más claro
    template_name = 'admins/admins_sales/closed_sales_list.html'
    paginate_by = 5
    allowed_groups = ADMIN_GROUP

    def get_queryset(self):
        return closedSales.objects.all().order_by('-date_sale')  # Ordenado por fecha descendente

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sales'] = self.get_queryset()  # Usando el mismo nombre que en context_object_name
        return context



def logout_view(request):
    logout(request)
    return redirect('home')

def acceso_denegado(request):
    return render(request, 'acceso_denegado.html')