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
        selected_day_str = self.request.GET.get('day', '')
        selected_day = int(selected_day_str) if selected_day_str.isdigit() else None

        # Manejo de fechas seguras
        try:
            if selected_day:
                start_date = timezone.make_aware(datetime(selected_year, selected_month, selected_day))
                end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
            else:
                start_date = timezone.make_aware(datetime(selected_year, selected_month, 1))
                last_day = calendar.monthrange(selected_year, selected_month)[1]
                end_date = timezone.make_aware(datetime(selected_year, selected_month, last_day, 23, 59, 59))
        except ValueError:
            messages.error(self.request, "Fecha inválida seleccionada. Usando fecha actual.")
            start_date = timezone.make_aware(datetime(today.year, today.month, today.day))
            end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
            selected_year, selected_month, selected_day = today.year, today.month, today.day

        # Datos filtrados para estadísticas generales
        filtered_sales = closedSales.objects.filter(date_sale__gte=start_date, date_sale__lte=end_date)
        filtered_budgets = Budget.objects.filter(emission_date__gte=start_date, emission_date__lte=end_date)

        # Estadísticas de presupuestos
        budget_stats = {
            'total': filtered_budgets.count(),
            'pending': filtered_budgets.filter(state='pendiente').count(),
            'accepted': filtered_budgets.filter(state='aceptado').count(),
            'rejected': filtered_budgets.filter(state='rechazado').count()
        }

        # Ganancias semanales (usando un rango independiente)
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        ventas_por_dia = []

        # Obtener el primer día del mes seleccionado
        first_day = timezone.make_aware(datetime(selected_year, selected_month, 1))
        # Obtener el último día del mes seleccionado
        last_day = timezone.make_aware(datetime(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1], 23, 59, 59))

        # Si se selecciona un día, obtener la semana correspondiente
        if selected_day:
            selected_date = timezone.make_aware(datetime(selected_year, selected_month, selected_day))
            week_number = selected_date.isocalendar()[1]  # Obtenemos el número de la semana
            start_of_week = selected_date - timedelta(days=selected_date.weekday())  # Lunes de la semana
            end_of_week = start_of_week + timedelta(days=6)  # Domingo de la semana

            # Filtrar ventas solo para la semana seleccionada
            ventas_por_dia = []
            for i in range(7):
                day_of_week = start_of_week + timedelta(days=i)
                ventas_dia = closedSales.objects.filter(
                    date_sale__gte=day_of_week,
                    date_sale__lte=day_of_week + timedelta(days=1) - timedelta(seconds=1)
                ).aggregate(total=Sum('fee_vendor'))['total'] or 0
                ventas_por_dia.append(float(ventas_dia))
        else:
            # Si no se selecciona un día, mostramos las ventas por día del mes
            for i in range(7):
                ventas_dia = closedSales.objects.filter(
                    date_sale__gte=first_day,
                    date_sale__lte=last_day,
                    date_sale__week_day=i + 2  # Django usa 1-7 donde 1=Domingo, necesitamos 2-8 donde 2=Lunes
                ).aggregate(
                    total=Sum('fee_vendor')
                )['total'] or 0
                ventas_por_dia.append(float(ventas_dia))

        # Ganancias mensuales (usando un rango independiente)
        meses = []
        ganancias_mensuales_data = []
        for i in range(12):
            month_date = today - relativedelta(months=i)
            month_start = month_date.replace(day=1)
            month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
            
            month_sales = closedSales.objects.filter(
                date_sale__gte=month_start,
                date_sale__lte=month_end
            ).aggregate(total=Sum('fee_vendor'))['total'] or 0
            
            meses.insert(0, calendar.month_abbr[month_date.month])
            ganancias_mensuales_data.insert(0, float(month_sales))

        # Top vendedores
        top_vendors = list(
            filtered_sales.values(
                'vendor__username', 'vendor__first_name', 'vendor__last_name'
            )
            .annotate(total_sales=Sum('fee_vendor'))
            .order_by('-total_sales')[:3]
        )

        formatted_top_vendors = [
            {
                'vendor': f"{vendor['vendor__first_name']} {vendor['vendor__last_name']}".strip() or vendor['vendor__username'],
                'total_sales': float(vendor['total_sales']) if vendor['total_sales'] else 0
            }
            for vendor in top_vendors
        ]

        while len(formatted_top_vendors) < 3:
            formatted_top_vendors.append({'vendor': 'Sin datos', 'total_sales': 0})

        # Años disponibles para filtro
        available_years = [date.year for date in closedSales.objects.dates('date_sale', 'year')]
        if not available_years:
            available_years = [today.year]

        # Asegurar que tenemos datos válidos para los gráficos
        if not ganancias_mensuales_data:
            meses = ["Sin datos"]
            ganancias_mensuales_data = [0]

        context.update({
            'monthly_revenue': filtered_sales.aggregate(Sum('fee_vendor'))['fee_vendor__sum'] or 0,
            'top_vendors': formatted_top_vendors,
            'ganancias_mensuales': json.dumps(ganancias_mensuales_data),
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
            'has_data': filtered_sales.exists(),
            'dias_semana': json.dumps(dias_semana),
            'ventas_por_dia': json.dumps(ventas_por_dia),
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

class AdminBudgetCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    allowed_groups = ADMIN_GROUP
    model = Budget
    form_class = BudgetForm
    template_name = 'admins/admins_budgtes/budget_form.html'
    success_url = reverse_lazy('budget_list') 

class AdminBudgetEdit(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    model = Budget
    template_name = 'admins/admins_budgtes/budget_form.html'
    form_class = BudgetForm
    success_url = reverse_lazy('budget_list')
    allowed_groups = ADMIN_GROUP  # Use defined group names

    def form_valid(self, form):
        budget = form.save(commit=False)
        previous_state = Budget.objects.get(pk=budget.pk).state if budget.pk else None
        
        budget.save()  # Guardar cambios en el presupuesto
        
        # Si el estado cambió a "aceptado", manejar closedSales
        if previous_state in ['pendiente', 'rechazado'] and budget.state == 'aceptado':
            closed_sale, created = closedSales.objects.get_or_create(budget=budget, defaults={
                'client': budget.client,
                'vendor': budget.vendor,
                'sales_price': budget.sale_price,
                'fee_sale': budget.sale_fee,
                'fee_cielo': budget.cielo_fee,
                'fee_vendor': budget.vendor_fee,
                'paid': "Pendiente"
            })
            
            if not created:  # Si ya existía, actualizar los valores
                closed_sale.sales_price = budget.sale_price
                closed_sale.fee_sale = budget.sale_fee
                closed_sale.fee_cielo = budget.cielo_fee
                closed_sale.fee_vendor = budget.vendor_fee
                closed_sale.save()

        
        return redirect(self.success_url)

    def form_invalid(self, form):
        ## messages.error(self.request, 'Error al actualizar el presupuesto. Revisa los campos.')
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
        ##messages.success(self.request, 'Presupuesto eliminado exitosamente.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        ##messages.error(self.request, 'Error al eliminar el presupuesto.')
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
    
class AdminclosedSalesDetail(LoginRequiredMixin, GroupRequiredMixin, DetailView):
    model = closedSales
    context_object_name = 'sales'  # Se utiliza 'budget' porque estamos mostrando detalles de un solo presupuesto.
    template_name = 'admins/admins_sales/closed_sales_detail.html'  # Asegúrate de que la ruta del template sea correcta.
    allowed_groups = ADMIN_GROUP

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ya no es necesario agregar budgets al contexto, ya que 'object' ya lo provee DetailView.
        return context


class ClosedSalesForm(forms.ModelForm):
    class Meta:
        model = closedSales
        fields = [ 'sales_price', 'fee_sale', 'fee_cielo', 'fee_vendor', 'paid']
        widgets = {
            'date_sale': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'paid': forms.Select(choices=[('Efectivo', 'Efectivo'), ('Tarjeta', 'Tarjeta'), ('Transferencia', 'Transferencia')])
        }
         

        # Si aún necesitas mostrar como solo lectura los campos excluidos, puedes hacerlo aquí:
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Desactivar campos de solo lectura
            self.fields['budget'].widget.attrs['readonly'] = True
            self.fields['client'].widget.attrs['readonly'] = True
            self.fields['vendor'].widget.attrs['readonly'] = True

class AdminsclosedSalesUpdate(LoginRequiredMixin, GroupRequiredMixin,UpdateView):
    model = closedSales
   
    template_name = 'admins/admins_sales/closed_sales_form.html'
    form_class = ClosedSalesForm
    success_url = reverse_lazy('closedSales_list')  # Ajusta al nombre correcto de la lista de ventas
    allowed_groups = ADMIN_GROUP
    def form_valid(self, form):
        closed_sale = form.save(commit=False)  # Obtener la instancia sin guardar aún
        
        #print("Datos antes de guardar:", form.cleaned_data)  # Debugging

        closed_sale.save()  # Guardar los cambios en la base de datos

        #messages.success(self.request, 'Venta actualizada exitosamente.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        #print("Error en el formulario:", form.errors)  # Debugging
        #messages.error(self.request, 'Error al actualizar la venta. Revisa los campos.')
        return super().form_invalid(form)

class AdminclosedSaleDelete(LoginRequiredMixin, GroupRequiredMixin, DeleteView):
    model = closedSales
    model = Budget
    template_name = 'admins/admins_sales/closed_sales_confirm_delete.html'
    context_object_name = 'sales'
    success_url = reverse_lazy('closedSales_list')
    allowed_groups = ADMIN_GROUP

    def get_queryset(self): # Admins can delete all
        return closedSales.objects.all() and Budget.objects.all()
        

    def form_valid(self, form):
        self.object.delete()  # Delete the object explicitly
        #messages.success(self.request, 'Presupuesto eliminado exitosamente.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        #messages.error(self.request, 'Error al eliminar el presupuesto.')
        return super().form_invalid(form)
def logout_view(request):
    logout(request)
    return redirect('home')

def acceso_denegado(request):
    return render(request, 'acceso_denegado.html')