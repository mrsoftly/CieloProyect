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

class DashboardAdminView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    """Vista para dashboard de administradores"""
    template_name = 'admins/info_admin.html'
    allowed_groups = 'admi'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()

        # Filtros desde la solicitud GET
        selected_year = int(self.request.GET.get('year', today.year))
        selected_month = int(self.request.GET.get('month', today.month)) if self.request.GET.get('month') else None
        selected_day = int(self.request.GET.get('day')) if self.request.GET.get('day') else None

        # Define start and end dates considering timezone awareness
        start_date = timezone.make_aware(datetime(selected_year, 1, 1))
        end_date = start_date + relativedelta(years=1) - timedelta(seconds=1)

        if selected_month:
            start_date = start_date.replace(month=selected_month)
            end_date = start_date + relativedelta(months=1) - timedelta(seconds=1)

        if selected_day:
            try:
                start_date = start_date.replace(day=selected_day)
                end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
            except ValueError:
                messages.error(self.request, "Fecha inválida seleccionada.")

        # Consultas para obtener los datos filtrados
        filtered_sales = closedSales.objects.filter(date_sale__gte=start_date, date_sale__lte=end_date)

        # Ganancias semanales
        weekly_sales = filtered_sales.annotate(
            week=TruncWeek('date_sale')
        ).values('week').annotate(
            total=Sum('fee_vendor')
        ).order_by('week')

        weekly_sales_dict = {sale['week']: sale['total'] for sale in weekly_sales}
        semanas = [f"Semana {4 - i}" for i in range(4)]
        ganancias_semanales_data = [weekly_sales_dict.get(today - timedelta(weeks=i), 0) for i in range(4)]

        # Ganancias mensuales
        monthly_sales = filtered_sales.annotate(
            month=TruncMonth('date_sale')
        ).values('month').annotate(
            total=Sum('fee_vendor')
        ).order_by('month')

        monthly_sales_dict = {sale['month']: sale['total'] for sale in monthly_sales}
        meses = list(calendar.month_name[1:])
        ganancias_mensuales_data = []

        for i in range(12):
            month_date = today.replace(day=1) - relativedelta(months=i)
            month_key = timezone.make_aware(datetime(month_date.year, month_date.month, 1))
            ganancia = monthly_sales_dict.get(month_key, 5000 + (i * 1000))
            ganancias_mensuales_data.insert(0, float(ganancia) if ganancia else 0)

        # Top vendedores
        top_vendors = list(filtered_sales.values('vendor')
            .annotate(total_sales=Sum('fee_vendor'))
            .order_by('-total_sales')[:3])

        while len(top_vendors) < 3:
            top_vendors.append({'vendor': f'Vendedor {len(top_vendors) + 1}', 'total_sales': 5000 - len(top_vendors) * 1000})

        # Años disponibles para filtro
        available_years = [date.year for date in closedSales.objects.dates('date_sale', 'year')]
        semanas_json = json.dumps(semanas, cls=DjangoJSONEncoder)
        ganancias_semanales_json = json.dumps(ganancias_semanales_data, cls=DjangoJSONEncoder)
        meses_json = json.dumps(meses, cls=DjangoJSONEncoder)
        ganancias_mensuales_json = json.dumps(ganancias_mensuales_data, cls=DjangoJSONEncoder)

        # Añadir todos los datos al contexto
        context.update({
            'weekly_revenue': sum(weekly_sales_dict.values()),
            'monthly_revenue': filtered_sales.aggregate(Sum('fee_vendor'))['fee_vendor__sum'] or 0,
            'top_vendors': top_vendors,
            'ganancias_semanales': ganancias_semanales_json,
            'ganancias_mensuales': ganancias_mensuales_json,
            'semanas': semanas_json,
            'meses': meses_json,
            'stats': {
                'total_clients': filtered_sales.values('client').distinct().count() or 10,
                'total_sales': filtered_sales.count() or 25,
                'average_sale': filtered_sales.aggregate(avg=Avg('fee_vendor'))['avg'] or 2500
            },
            'available_years': available_years,
            'months': list(enumerate(calendar.month_name[1:], start=1)),
            'selected_year': selected_year,
            'selected_month': selected_month,
            'selected_day': selected_day,
            'days_range': list(range(1, 32))
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

class AdminBudgetCreateView(CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'admins/admins_budgtes/budget_form.html'
    success_url = reverse_lazy('budget_list') 




def logout_view(request):
    logout(request)
    return redirect('home')

def acceso_denegado(request):
    return render(request, 'acceso_denegado.html')