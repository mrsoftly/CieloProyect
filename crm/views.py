from django.views.generic import (
    ListView, 
    DetailView, 
    CreateView, 
    UpdateView, 
    DeleteView
)
from django.shortcuts import render,get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib.auth.models import User,Group
from crm.models import Client, Budget, closedSales
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncWeek, TruncMonth
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import calendar
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from django.core.serializers.json import DjangoJSONEncoder
import json


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
    allowed_groups = ['admi']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()

        # Filtros desde la solicitud GET
        selected_year = self.request.GET.get('year', today.year)
        selected_month = self.request.GET.get('month', None)
        selected_day = self.request.GET.get('day', None)

        # Convertir valores a enteros si están presentes
        selected_year = int(selected_year)
        selected_month = int(selected_month) if selected_month else None
        selected_day = int(selected_day) if selected_day else None

        # Rango de días (1-31)
        days_range = list(range(1, 32))

        # Define start and end dates considering timezone awareness
        start_date = timezone.make_aware(datetime(selected_year, 1, 1))
        end_date = start_date + relativedelta(years=1) - timedelta(seconds=1)

        if selected_month:
            start_date = start_date.replace(month=selected_month)
            end_date = start_date + relativedelta(months=1) - timedelta(seconds=1)

        if selected_day:
            start_date = start_date.replace(day=selected_day)
            end_date = start_date + timedelta(days=1) - timedelta(seconds=1)

        # Consultas para obtener los datos filtrados
        filtered_sales = closedSales.objects.filter(date_sale__gte=start_date, date_sale__lte=end_date)

        # Ganancias semanales
        weekly_sales = filtered_sales.annotate(
            week=TruncWeek('date_sale')
        ).values('week').annotate(
            total=Sum('fee_vendor')
        ).order_by('week')

        weekly_sales_dict = {sale['week']: sale['total'] for sale in weekly_sales}
        
        semanas = []
        ganancias_semanales_data = []

        for i in range(4):
            week_date = today - timedelta(weeks=i)
            week_start = week_date - timedelta(days=week_date.weekday())
            
            semanas.insert(0, f"Semana {4 - i}")
            ganancias = weekly_sales_dict.get(week_start.date(), 0)
            ganancias_semanales_data.insert(0, float(ganancias) if ganancias else 0)

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
            ganancia = monthly_sales_dict.get(TruncMonth(month_date), 5000 + (i * 1000))
            ganancias_mensuales_data.insert(0, float(ganancia) if ganancia else 0)

        # Top vendedores
        top_vendors = filtered_sales.values('vendor')\
            .annotate(total_sales=Sum('fee_vendor'))\
            .order_by('-total_sales')[:3]

        if not top_vendors:
            top_vendors = [
                {'vendor': 'Vendedor 1', 'total_sales': 5000},
                {'vendor': 'Vendedor 2', 'total_sales': 4000},
                {'vendor': 'Vendedor 3', 'total_sales': 3000}
            ]

        # Años disponibles para filtro
        available_years = closedSales.objects.dates('date_sale', 'year')
        available_years = [date.year for date in available_years]
        
        # Serializar datos para los gráficos
        semanas_json = json.dumps(semanas, cls=DjangoJSONEncoder)
        ganancias_semanales_json = json.dumps(ganancias_semanales_data, cls=DjangoJSONEncoder)
        meses_json = json.dumps(meses, cls=DjangoJSONEncoder)
        ganancias_mensuales_json = json.dumps(ganancias_mensuales_data, cls=DjangoJSONEncoder)

        # Añadir todos los datos al contexto
        context.update({
            'weekly_revenue': sum(sale['total'] for sale in weekly_sales if sale['total']),
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
            'days_range': days_range
        })

        return context

class DashboardAsesorView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
  """Vista para dashboard de usuarios"""
  template_name = 'info_asesor.html' # Cambia a la plantilla correspondiente
  allowed_groups = ['asesor']  # Cambia al grupo correspondiente si es necesario
  def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user  # Usuario conectado
        today = timezone.now()

        # Filtros desde la solicitud GET
        selected_year = self.request.GET.get('year', today.year)
        selected_month = self.request.GET.get('month', None)
        selected_day = self.request.GET.get('day', None)

        # Convertir valores a enteros si están presentes
        selected_year = int(selected_year)
        selected_month = int(selected_month) if selected_month else None
        selected_day = int(selected_day) if selected_day else None

        # Rango de días (1-31)
        days_range = list(range(1, 32))

        # Define start and end dates considering timezone awareness
        start_date = timezone.make_aware(datetime(selected_year, 1, 1))
        end_date = start_date + relativedelta(years=1) - timedelta(seconds=1)

        if selected_month:
            start_date = start_date.replace(month=selected_month)
            end_date = start_date + relativedelta(months=1) - timedelta(seconds=1)

        if selected_day:
            start_date = start_date.replace(day=selected_day)
            end_date = start_date + timedelta(days=1) - timedelta(seconds=1)

        # Filtrar las ventas del usuario actual
        filtered_sales = closedSales.objects.filter(
            date_sale__gte=start_date,
            date_sale__lte=end_date,
            vendor=user  # Filtrar por el usuario conectado
        )

        # Ganancias semanales
        weekly_sales = filtered_sales.annotate(
            week=TruncWeek('date_sale')
        ).values('week').annotate(
            total=Sum('fee_vendor')
        ).order_by('week')

        weekly_sales_dict = {sale['week']: sale['total'] for sale in weekly_sales}

        semanas = []
        ganancias_semanales_data = []

        for i in range(4):
            week_date = today - timedelta(weeks=i)
            week_start = week_date - timedelta(days=week_date.weekday())
            
            semanas.insert(0, f"Semana {4 - i}")
            ganancias = weekly_sales_dict.get(week_start.date(), 0)
            ganancias_semanales_data.insert(0, float(ganancias) if ganancias else 0)

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
            ganancia = monthly_sales_dict.get(TruncMonth(month_date), 0)
            ganancias_mensuales_data.insert(0, float(ganancia) if ganancia else 0)

        # Años disponibles para filtro
        available_years = closedSales.objects.filter(vendor=user).dates('date_sale', 'year')
        available_years = [date.year for date in available_years]

        # Serializar datos para los gráficos
        semanas_json = json.dumps(semanas, cls=DjangoJSONEncoder)
        ganancias_semanales_json = json.dumps(ganancias_semanales_data, cls=DjangoJSONEncoder)
        meses_json = json.dumps(meses, cls=DjangoJSONEncoder)
        ganancias_mensuales_json = json.dumps(ganancias_mensuales_data, cls=DjangoJSONEncoder)

        # Añadir todos los datos al contexto
        context.update({
            'weekly_revenue': sum(sale['total'] for sale in weekly_sales if sale['total']),
            'monthly_revenue': filtered_sales.aggregate(Sum('fee_vendor'))['fee_vendor__sum'] or 0,
            'ganancias_semanales': ganancias_semanales_json,
            'ganancias_mensuales': ganancias_mensuales_json,
            'semanas': semanas_json,
            'meses': meses_json,
            'stats': {
                'total_clients': filtered_sales.values('client').distinct().count() or 0,
                'total_sales': filtered_sales.count() or 0,
                'average_sale': filtered_sales.aggregate(avg=Avg('fee_vendor'))['avg'] or 0
            },
            'available_years': available_years,
            'months': list(enumerate(calendar.month_name[1:], start=1)),
            'selected_year': selected_year,
            'selected_month': selected_month,
            'selected_day': selected_day,
            'days_range': days_range
        })

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
        # Pre-configuración para el campo 'vendor'
        if self.request.user.groups.filter(name='asesor').exists():
            form.fields['vendor'].initial = self.request.user.username
            form.fields['vendor'].disabled = True

        # Configuración del campo 'client' para que sea un campo de texto con autocompletado
        form.fields['client'].widget.attrs.update({
            'class': 'form-control',
            'id': 'client-autocomplete',
            'placeholder': 'Buscar cliente por nombre, teléfono o correo'
        })

        return form

    def form_valid(self, form):
   
        client_input = form.cleaned_data['client']

        # Buscar el cliente por nombre, correo o teléfono
        from django.core.exceptions import ValidationError

        try:
            client = Client.objects.filter(
                models.Q(name__icontains=client_input) | 
                models.Q(email__icontains=client_input) | 
                models.Q(phone__icontains=client_input)
            ).first()

            if client:
                form.instance.client = client
            else:
                raise ValidationError("El cliente ingresado no existe. Por favor seleccione uno válido.")
        except ValidationError as e:
            form.add_error('client', e)

        return super().form_valid(form)

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

@login_required
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'Users/asesor.html', {'users': users})
@login_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    groups = Group.objects.all()
    
    if request.method == 'POST':
        user.username = request.POST['username']
        user.email = request.POST['email']
        user.is_active = 'is_active' in request.POST
        
        # Manejar la asignación de grupo
        group_id = request.POST.get('group')
        # Primero removemos todos los grupos actuales
        user.groups.clear()
        # Si se seleccionó un grupo, lo asignamos
        if group_id:
            group = Group.objects.get(id=group_id)
            user.groups.add(group)
            
        user.save()
        messages.success(request, 'Usuario actualizado correctamente')
        return redirect('lista_asesores')
        
    return render(request, 'Users/edit_asesor.html', {
        'user': user,
        'groups': groups
    })
@login_required
def user_delete(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        user.delete()
        messages.success(request, 'Usuario eliminado correctamente')
    return redirect('lista_asesores')
@login_required
def user_create(request):
    groups = Group.objects.all()
    
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        
        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'Users/new_asesor.html', {'groups': groups})
        
        try:
            # Crear el nuevo usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            
            # Establecer estado activo
            user.is_active = 'is_active' in request.POST
            
            # Asignar grupo si se seleccionó uno
            group_id = request.POST.get('group')
            if group_id:
                group = Group.objects.get(id=group_id)
                user.groups.add(group)
            
            user.save()
            
           
            return redirect('lista_asesores')
            
        except Exception as e:
            messages.error(request, f'Error al crear usuario: {str(e)}')
    
    return render(request, 'Users/new_asesor.html', {'groups': groups})