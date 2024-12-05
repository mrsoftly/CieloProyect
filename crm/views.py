from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth import logout

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
    template_name = 'dashboard_admin.html'
    allowed_groups = ['admi']  # Solo accesible para el grupo Admin

class DashboardAsesorView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    """Vista para dashboard de asesores"""
    template_name = 'dashboard_asesor.html'
    allowed_groups = ['asesor']  # Solo accesible para el grupo Asesor

# Vista para manejar acceso denegado
def acceso_denegado(request):
    return render(request, '404.html')

def logout_view(request):
    logout(request)
    return redirect('home')