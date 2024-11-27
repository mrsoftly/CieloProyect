from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

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
            return redirect('home')  # Redirigir al inicio o a una página segura
        else:
            messages.error(request, "Credenciales incorrectas")
            return redirect('login')  # Redirigir a la página de inicio de sesión con el error

    return render(request, 'login.html')
