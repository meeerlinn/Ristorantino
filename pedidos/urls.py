from django.urls import path
from . import views

urlpatterns = [
    # Salón y mesas
    path('salon/', views.salon_principal, name='salon'),
    path('mesa/<int:mesa_id>/abrir/', views.abrir_mesa, name='abrir_mesa'),

    # Pedidos
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('pedido/<int:pedido_id>/tomar/', views.tomar_pedido, name='tomar_pedido'),
    path('pedido/<int:pedido_id>/agregar/<int:producto_id>/', views.agregar_producto, name='agregar_producto'),
    path('pedido/<int:pedido_id>/agregar-ajax/<int:producto_id>/', views.agregar_producto_ajax, name='agregar_producto_ajax'),
    path('pedido/<int:pedido_id>/eliminar-detalle/<int:detalle_id>/', views.eliminar_detalle_ajax, name='eliminar_detalle_ajax'),
    path('pedido/<int:pedido_id>/cantidad/<int:detalle_id>/', views.actualizar_cantidad_ajax, name='actualizar_cantidad_ajax'),
    path('producto/<int:producto_id>/toggle-disponible/', views.toggle_disponible_ajax, name='toggle_disponible_ajax'),
    path('pedido/<int:pedido_id>/confirmar/', views.confirmar_pedido, name='confirmar_pedido'),
    path('pedido/<int:pedido_id>/cobrar/', views.cobrar_pedido, name='cobrar_pedido'),

    # Cocina
    path('cocina/', views.monitor_cocina, name='vista_cocina'),
    path('cocina/datos/', views.cocina_datos_ajax, name='cocina_datos_ajax'),
    path('cocina/estado/<int:detalle_id>/<str:nuevo_estado>/', views.cambiar_estado_cocina, name='cambiar_estado_cocina'),

    # Caja
    path('caja/', views.gestion_caja, name='gestion_caja'),
    path('caja/abrir/', views.abrir_caja, name='abrir_caja'),
    path('caja/cerrar/<int:arqueo_id>/', views.cerrar_caja, name='cerrar_caja'),

    # Clientes AJAX
    path('clientes/buscar/', views.buscar_clientes, name='buscar_clientes'),

    # Acciones de Mesa (AJAX)
    path('mesa/<int:mesa_id>/marcar-sucia/', views.marcar_sucia,   name='marcar_sucia'),
    path('mesa/<int:mesa_id>/bloquear/',     views.bloquear_mesa,  name='bloquear_mesa'),

    # Dashboard / KPIs
    path('dashboard/', views.dashboard, name='dashboard'),

    # Historial de Pedidos + Anulación
    path('pedidos/historial/',                         views.historial_pedidos,  name='historial_pedidos'),
    path('pedidos/<int:pedido_id>/detalle-historial/', views.detalle_historial,  name='detalle_historial'),
    path('pedidos/<int:pedido_id>/anular/',            views.anular_pedido,      name='anular_pedido'),

    # Reservaciones
    path('reservaciones/',                                     views.lista_reservaciones,   name='lista_reservaciones'),
    path('reservaciones/crear/<int:mesa_id>/',                 views.crear_reservacion,     name='crear_reservacion'),
    path('reservaciones/<int:reservacion_id>/cancelar/',       views.cancelar_reservacion,  name='cancelar_reservacion'),
    path('reservaciones/<int:reservacion_id>/activar-mesa/',   views.activar_mesa_reservada,name='activar_mesa_reservada'),

    # Gestión de Clientes
    path('clientes/',                         views.lista_clientes,  name='lista_clientes'),
    path('clientes/crear/',                   views.crear_cliente,   name='crear_cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente,  name='editar_cliente'),

    # Fase 7 — Gestión de Menú
    path('productos/',                                    views.lista_productos,  name='lista_productos'),
    path('productos/crear/',                              views.crear_producto,   name='crear_producto'),
    path('productos/<int:producto_id>/editar/',           views.editar_producto,  name='editar_producto'),
    path('productos/<int:producto_id>/reponer-stock/',    views.reponer_stock,    name='reponer_stock'),
    path('categorias/',                                   views.lista_categorias, name='lista_categorias'),

    # Nota de ítem
    path('detalle/<int:detalle_id>/nota/', views.guardar_nota_ajax, name='guardar_nota_ajax'),

    # Transferencia de mesa
    path('pedido/<int:pedido_id>/transferir/', views.transferir_pedido, name='transferir_pedido'),

    # Fase 8 — Factura imprimible
    path('pedido/<int:pedido_id>/factura/',           views.imprimir_factura, name='imprimir_factura'),

    # Reportes
    path('reporte/iva/', views.reporte_iva, name='reporte_iva'),
    path('reporte/z/',   views.reporte_z,   name='reporte_z'),

    # Exportaciones Excel
    path('historial/exportar/', views.exportar_historial_excel, name='exportar_historial_excel'),
    path('dashboard/exportar/', views.exportar_dashboard_excel, name='exportar_dashboard_excel'),

    # Fase 9 — Configuración
    path('configuracion/',                           views.configuracion,    name='configuracion'),
]