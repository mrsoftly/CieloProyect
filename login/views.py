from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import Group

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Verificar las credenciales
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Si el usuario es autenticado correctamente, inicia sesión
            login(request, user)
            messages.success(request, "Inicio de sesión exitoso")
            
            # Verificar el grupo del usuario y redirigir según su rol
            if user.groups.filter(name='admi').exists():
                return redirect('dashboard_admin')  # Cambiar por el nombre de la vista/URL del grupo 1
            elif user.groups.filter(name='asesor').exists():
                return redirect('dashboard_asesor')  # Cambiar por el nombre de la vista/URL del grupo 2
            else:
                return redirect('404')  # Redirigir al inicio si no tiene grupo o rol específico
        else:
            messages.error(request, "Credenciales incorrectas")
            return redirect('login')  # Redirigir a la página de inicio de sesión con el error
    
    return render(request, 'login.html')
