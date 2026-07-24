from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def requiere_rol(*roles):
    """
    Decorador de control de acceso por rol para vistas Django.

    Uso:
        @login_required
        @requiere_rol('Cajero', 'Administrador')
        def mi_vista(request): ...

    Roles válidos definidos en la tabla Rol:
        - 'Mozo'          — toma pedidos, ve reservaciones
        - 'Chef'          — accede al monitor de cocina
        - 'Cajero'        — caja, cobro, historial, clientes, menú, dashboard
        - 'Administrador' — todos los módulos + configuración del restaurante

    Jerarquía de acceso:
        Superusuario Django (is_superuser=True) → acceso total, sin chequeo de rol.
        Rol correcto → accede a la vista normalmente.
        Rol incorrecto o sin empleado asociado → redirect('salon') con messages.error
            mostrando los roles requeridos en el mensaje.

    El rol se obtiene desde request.user.empleado.rol.nombre. Si el usuario no tiene
    un Empleado asociado (AttributeError), se trata como sin rol y se deniega el acceso.

    Args:
        *roles: nombres de roles permitidos (str). Se puede pasar uno o varios.

    Returns:
        Decorador que envuelve la función de vista con la lógica de control de acceso.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            try:
                rol = request.user.empleado.rol.nombre
            except AttributeError:
                rol = None
            if rol in roles:
                return view_func(request, *args, **kwargs)
            messages.error(
                request,
                f'No tenés permiso para acceder a esa sección (requiere: {", ".join(roles)}).'
            )
            return redirect('salon')
        return wrapper
    return decorator
