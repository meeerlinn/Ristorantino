import io
import json
from datetime import datetime, date, time, timedelta

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import (
    Sum, F, OuterRef, Subquery, Q, Max, Count, Avg,
    ExpressionWrapper, DecimalField, DurationField
)
from django.utils import timezone
from .models import (
    Sector, Mesa, Pedido, Cliente, Producto, PedidoDetalle, Categoria,
    FlujoEstado, Arqueo, Caja, CajaTimbrado, DocumentoTributario,
    PedidoDocumento, Reservacion, Empleado
)
from .decorators import requiere_rol

@login_required
def salon_principal(request):
    """
    Pantalla principal del restaurante: grilla de mesas por sector.

    Roles: todos los autenticados
    Método: GET
    Retorna: render salon.html — incluye estado actual de cada mesa,
             pedido_activo_id (si hay pedido Pendiente) y reservacion_activa.
    Performance: usa dicts O(1) para evitar N+1 queries.
    """
    sectores = Sector.objects.all()
    mesas = list(Mesa.objects.all().order_by('numero_mesa').select_related('sector'))

    # Precarga pedidos pendientes y reservaciones activas en dicts O(1)
    pedidos_activos = {
        p.mesa_id: p.id
        for p in Pedido.objects.filter(estado_pago='Pendiente').only('id', 'mesa_id')
    }
    reservaciones_activas = {
        r.mesa_id: r
        for r in Reservacion.objects.filter(estado='Confirmada').select_related('cliente')
    }
    for mesa in mesas:
        mesa.pedido_activo_id   = pedidos_activos.get(mesa.id)
        mesa.reservacion_activa = reservaciones_activas.get(mesa.id)

    context = {
        'sectores': sectores,
        'mesas': mesas,
    }
    return render(request, 'pedidos/salon.html', context)

@login_required
def abrir_mesa(request, mesa_id):
    """
    Abre una mesa y crea el Pedido inicial.

    Roles: todos los autenticados
    Método: GET (redirect)
    - Si la mesa ya está Ocupada: redirige al pedido activo existente.
    - Si está Libre o Sucia: cambia estado a Ocupada, crea Pedido con cliente
      genérico (RUC='0') y redirige a tomar_pedido.
    - Cualquier otro estado: redirige al salón sin acción.
    """
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    # Si la mesa ya está ocupada, buscamos el pedido pendiente para redirigir directamente
    if mesa.estado == 'Ocupada':
        pedido_activo = Pedido.objects.filter(mesa=mesa, estado_pago='Pendiente').first()
        if pedido_activo:
            return redirect('tomar_pedido', pedido_id=pedido_activo.id)

    # Solo permitimos abrir la mesa si está Libre o Sucia
    if mesa.estado == 'Libre' or mesa.estado == 'Sucia':
        # 1. Actualizamos el estado de la mesa
        mesa.estado = 'Ocupada'
        mesa.save()

        # 2. Obtenemos un cliente por defecto (asegúrate de que exista en la DB)
        # O podrías hacer que el campo cliente sea nullable en models.py
        cliente_generico, _ = Cliente.objects.get_or_create(
            ruc_ci="0", 
            defaults={'nombre_razon_social': "Sin Nombre / Ocasional"}
        )
        
        # 3. Creamos el pedido inicial
        nuevo_pedido = Pedido.objects.create(
            mesa=mesa,
            mozo=request.user,
            cliente=cliente_generico,
            estado_pago='Pendiente'
        )
        
        # Redireccionamos directamente a la toma de pedido
        return redirect('tomar_pedido', pedido_id=nuevo_pedido.id)
    
    return redirect('salon')

@login_required
def detalle_pedido(request, pedido_id):
    """
    Vista de resumen administrativo de un pedido (no es la comanda principal).

    Roles: todos los autenticados
    Método: GET
    Retorna: render detalle_pedido.html
    Nota: la pantalla de toma de pedidos real es tomar_pedido().
    """
    # Mantenemos esta vista por si necesitas un resumen administrativo,
    # pero la toma de pedidos principal será en 'tomar_pedido'
    pedido = get_object_or_404(Pedido, id=pedido_id)
    detalles = pedido.detalles.all()
    categorias = Categoria.objects.prefetch_related('producto_set').all()

    context = {
        'pedido': pedido,
        'detalles': detalles,
        'categorias': categorias,
    }
    return render(request, 'pedidos/detalle_pedido.html', context)

@login_required
def tomar_pedido(request, pedido_id):
    """
    Pantalla principal de toma de pedido (comanda digital).

    Roles: todos los autenticados
    Método: GET
    Retorna: render comanda.html con catálogo completo de productos, detalles
             del pedido anotados con su estado_actual de cocina, y flag
             puede_toggle para mostrar botones de disponibilidad a Cajero/Admin.
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    categorias = Categoria.objects.all()
    # Mostrar TODOS los productos; los no disponibles se ven greyed-out
    productos = Producto.objects.all().select_related('categoria')

    ultimo_estado = FlujoEstado.objects.filter(
        pedido_detalle=OuterRef('pk')
    ).order_by('-timestamp')

    detalles = pedido.detalles.annotate(
        estado_actual=Subquery(ultimo_estado.values('estado')[:1])
    ).select_related('producto')

    # Flag para mostrar el botón de toggle a Cajero/Administrador
    puede_toggle = request.user.is_superuser or (
        hasattr(request.user, 'empleado') and
        request.user.empleado.rol.nombre in ('Cajero', 'Administrador')
    )

    mesas_libres = Mesa.objects.filter(estado='Libre').exclude(id=pedido.mesa.id).order_by('numero_mesa')

    context = {
        'pedido': pedido,
        'categorias': categorias,
        'productos': productos,
        'detalles': detalles,
        'puede_toggle': puede_toggle,
        'mesas_libres': mesas_libres,
    }
    return render(request, 'pedidos/comanda.html', context)

@login_required
def agregar_producto(request, pedido_id, producto_id):
    """
    Agrega un producto al pedido (versión sin AJAX, redirect).

    Roles: todos los autenticados
    Método: GET (redirect)
    Retorna: redirect a tomar_pedido
    Nota: la versión AJAX (agregar_producto_ajax) es la usada en la comanda.
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    producto = get_object_or_404(Producto, id=producto_id)

    # Buscamos si el producto ya está en el detalle del pedido
    detalle, created = PedidoDetalle.objects.get_or_create(
        pedido=pedido,
        producto=producto,
        defaults={'precio_historico': producto.precio_venta, 'cantidad': 1}
    )

    if not created:
        detalle.cantidad += 1
        detalle.save()

    # Actualizamos el total del pedido de forma simple
    pedido.actualizar_total()

    return redirect('tomar_pedido', pedido_id=pedido.id)

@login_required
def agregar_producto_ajax(request, pedido_id, producto_id):
    """
    Agrega un producto al carrito vía AJAX (o incrementa su cantidad si ya existe).

    Roles: todos los autenticados
    Método: GET o POST (fetch desde comanda.html)
    Retorna: JsonResponse {"total": "...", "items": [...]}
    Al crear un nuevo detalle: crea FlujoEstado='Pendiente' y captura precio_historico.
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    producto = get_object_or_404(Producto, id=producto_id)

    detalle, created = PedidoDetalle.objects.get_or_create(
        pedido=pedido,
        producto=producto,
        defaults={'cantidad': 1}
    )

    if not created:
        detalle.cantidad += 1

    # El modelo maneja el precio_historico en el save() si es nuevo
    detalle.save()

    if created:
        FlujoEstado.objects.create(pedido_detalle=detalle, estado='Pendiente')

    # Usamos el método centralizado en el modelo
    pedido.actualizar_total()

    # ── Gestión de stock ──────────────────────────────────
    stock_info = None
    if producto.stock_actual is not None:
        producto.stock_actual = max(0, producto.stock_actual - 1)
        if producto.stock_actual == 0:
            producto.disponible = False
        producto.save(update_fields=['stock_actual', 'disponible'])
        stock_info = {
            'producto_id': producto.id,
            'stock':       producto.stock_actual,
            'disponible':  producto.disponible,
        }

    items = [{
        'id': d.id,
        'cantidad': d.cantidad,
        'nombre': d.producto.nombre,
        'precio': str(d.precio_historico),
        'nota': d.observaciones or '',
    } for d in pedido.detalles.all().order_by('id')]

    return JsonResponse({
        'total':      str(pedido.total_pedido),
        'items':      items,
        'stock_info': stock_info,
    })

@login_required
def eliminar_detalle_ajax(request, pedido_id, detalle_id):
    """
    Elimina un ítem del pedido vía AJAX.

    Roles: todos los autenticados
    Método: GET o POST (fetch desde comanda.html)
    Retorna: JsonResponse {"total": "...", "items": [...]}
    Precaución: no verifica el estado del ítem; se confía en el template
    que solo muestra el botón X para ítems en estado Pendiente.
    """
    pedido  = get_object_or_404(Pedido, id=pedido_id)
    detalle = get_object_or_404(PedidoDetalle, id=detalle_id, pedido=pedido)

    # Guardar referencia antes de eliminar para restaurar stock
    producto  = detalle.producto
    cantidad  = detalle.cantidad
    detalle.delete()
    pedido.actualizar_total()

    # ── Restaurar stock ───────────────────────────────────
    stock_info = None
    if producto.stock_actual is not None:
        producto.stock_actual += cantidad
        if producto.stock_actual > 0 and not producto.disponible:
            producto.disponible = True
        producto.save(update_fields=['stock_actual', 'disponible'])
        stock_info = {
            'producto_id': producto.id,
            'stock':       producto.stock_actual,
            'disponible':  producto.disponible,
        }

    items = [{
        'id': d.id,
        'cantidad': d.cantidad,
        'nombre': d.producto.nombre,
        'precio': str(d.precio_historico),
        'nota': d.observaciones or '',
    } for d in pedido.detalles.all().order_by('id')]

    return JsonResponse({
        'total':      str(pedido.total_pedido),
        'items':      items,
        'stock_info': stock_info,
    })

@login_required
def cambiar_estado_cocina(request, detalle_id, nuevo_estado):
    """
    Avanza el estado de preparación de un ítem de cocina.

    Roles: todos los autenticados (chef usa esta URL desde el monitor)
    Método: GET (link directo en cocina.html y comanda.html)
    Retorna: redirect a vista_cocina
    Crea un FlujoEstado inmutable con el nuevo estado y timestamp actual.
    """
    detalle = get_object_or_404(PedidoDetalle, id=detalle_id)
    FlujoEstado.objects.create(pedido_detalle=detalle, estado=nuevo_estado)
    return redirect('vista_cocina')

@login_required
def confirmar_pedido(request, pedido_id):
    """
    Vuelve al salón desde la comanda. Si el pedido está vacío, lo elimina y libera la mesa.

    Roles: todos los autenticados
    Método: GET (redirect)
    Retorna: redirect a salon
    Caso pedido vacío: borra el Pedido y pone la mesa en estado Libre.
    Caso pedido con ítems: solo navega al salón (pedido queda activo).
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if not pedido.detalles.exists():
        mesa = pedido.mesa
        pedido.delete()
        mesa.estado = 'Libre'
        mesa.save()

    return redirect('salon')

@login_required
@requiere_rol('Chef', 'Administrador')
def monitor_cocina(request):
    """
    Monitor de cocina (KDS): muestra ítems Pendiente y En Cocina ordenados por antigüedad (FIFO).

    Roles: Chef, Administrador
    Método: GET
    Retorna: render cocina.html con detalles anotados con estado_actual y fecha_estado.
    El orden FIFO garantiza que los pedidos más viejos se atiendan primero.
    """
    ultimo_estado = FlujoEstado.objects.filter(
        pedido_detalle=OuterRef('pk')
    ).order_by('-timestamp')

    detalles = PedidoDetalle.objects.annotate(
        estado_actual=Subquery(ultimo_estado.values('estado')[:1]),
        fecha_estado=Subquery(ultimo_estado.values('timestamp')[:1])
    ).filter(
        estado_actual__in=['Pendiente', 'Cocina']
    ).select_related('pedido__mesa', 'producto').order_by('pedido__fecha_apertura')

    return render(request, 'pedidos/cocina.html', {'detalles': detalles})


@login_required
@requiere_rol('Chef', 'Administrador')
def cocina_datos_ajax(request):
    """
    Endpoint JSON para el auto-refresco del monitor de cocina.

    Roles: Chef, Administrador
    Método: GET
    Retorna: JsonResponse con lista de ítems activos (Pendiente/Cocina) y hora del servidor.
    Usado por el setInterval de cocina.html cada 20 segundos.
    Incluye: id, estado, mesa, producto, cantidad, observaciones, tiempo transcurrido,
             label del botón siguiente y URL de cambio de estado.
    """
    ultimo_estado = FlujoEstado.objects.filter(
        pedido_detalle=OuterRef('pk')
    ).order_by('-timestamp')

    detalles = PedidoDetalle.objects.annotate(
        estado_actual=Subquery(ultimo_estado.values('estado')[:1]),
        fecha_estado=Subquery(ultimo_estado.values('timestamp')[:1])
    ).filter(
        estado_actual__in=['Pendiente', 'Cocina']
    ).select_related('pedido__mesa', 'producto').order_by('pedido__fecha_apertura')

    ahora = timezone.now()
    items = []
    for d in detalles:
        if d.fecha_estado:
            mins = int((ahora - d.fecha_estado).total_seconds() / 60)
            if mins < 1:
                hace = 'recién'
            elif mins == 1:
                hace = '1 minuto'
            else:
                hace = f'{mins} minutos'
        else:
            hace = '—'

        if d.estado_actual == 'Pendiente':
            btn_label = 'Empezar'
            url_sig   = f'/cocina/estado/{d.id}/Cocina/'
        elif d.estado_actual == 'Cocina':
            btn_label = 'Listo'
            url_sig   = f'/cocina/estado/{d.id}/Listo/'
        else:
            btn_label = None
            url_sig   = None

        items.append({
            'id':            d.id,
            'estado_actual': d.estado_actual,
            'mesa':          d.pedido.mesa.numero_mesa,
            'producto':      d.producto.nombre,
            'cantidad':      d.cantidad,
            'observaciones': d.observaciones or '',
            'hace':          hace,
            'btn_label':     btn_label,
            'url_siguiente': url_sig,
        })

    return JsonResponse({
        'items': items,
        'hora':  timezone.localtime(ahora).strftime('%H:%M:%S'),
    })


# ==========================================
# VISTAS DE CAJA Y FACTURACIÓN
# ==========================================

@login_required
@requiere_rol('Cajero', 'Administrador')
def gestion_caja(request):
    """
    Panel de caja: muestra el arqueo activo del cajero y estadísticas del turno.

    Roles: Cajero, Administrador
    Método: GET
    Retorna: render caja.html con arqueo_activo, lista de cajas disponibles
             y stats (total_vendido, cant_facturas, monto_esperado al cierre).
    Si no hay arqueo abierto: muestra formulario para abrir caja.
    """
    arqueo_activo = Arqueo.objects.filter(usuario=request.user, estado='Abierto').first()
    cajas = Caja.objects.filter(is_active=True)

    stats = {}
    if arqueo_activo:
        docs = DocumentoTributario.objects.filter(arqueo=arqueo_activo, estado='Vigente')
        stats['total_vendido'] = docs.aggregate(t=Sum('monto_total'))['t'] or 0
        stats['cant_facturas'] = docs.count()
        stats['monto_esperado'] = arqueo_activo.monto_apertura + stats['total_vendido']

    context = {
        'arqueo_activo': arqueo_activo,
        'cajas': cajas,
        'stats': stats,
    }
    return render(request, 'pedidos/caja.html', context)


@login_required
@requiere_rol('Cajero', 'Administrador')
def abrir_caja(request):
    """
    Crea un nuevo Arqueo (turno de caja) para el cajero actual.

    Roles: Cajero, Administrador
    Método: POST
    Retorna: redirect a gestion_caja
    Restricción: solo puede haber un arqueo Abierto por usuario a la vez.
    """
    if request.method != 'POST':
        return redirect('gestion_caja')

    if Arqueo.objects.filter(usuario=request.user, estado='Abierto').exists():
        messages.warning(request, 'Ya tenés una caja abierta.')
        return redirect('gestion_caja')

    caja_id = request.POST.get('caja_id')
    monto_apertura = request.POST.get('monto_apertura', 0)
    caja = get_object_or_404(Caja, id=caja_id)

    Arqueo.objects.create(
        caja=caja,
        usuario=request.user,
        monto_apertura=monto_apertura,
    )
    messages.success(request, f'Caja "{caja.nombre}" abierta correctamente.')
    return redirect('gestion_caja')


@login_required
@requiere_rol('Cajero', 'Administrador')
def cerrar_caja(request, arqueo_id):
    """
    Cierra el turno de caja: registra monto real contado y calcula diferencia.

    Roles: Cajero, Administrador
    Método: POST
    Retorna: redirect a gestion_caja
    diferencia_arqueo = monto_real - (monto_apertura + monto_cierre_sistema)
    Un valor negativo indica faltante.
    """
    if request.method != 'POST':
        return redirect('gestion_caja')

    arqueo = get_object_or_404(Arqueo, id=arqueo_id, usuario=request.user, estado='Abierto')
    monto_real = int(request.POST.get('monto_cierre_real', 0))

    arqueo.monto_cierre_real = monto_real
    arqueo.diferencia_arqueo = monto_real - int(arqueo.monto_apertura + arqueo.monto_cierre_sistema)
    arqueo.estado = 'Cerrado'
    arqueo.fecha_cierre = timezone.now()
    arqueo.save()

    messages.success(request, 'Caja cerrada. El arqueo fue registrado.')
    return redirect('gestion_caja')


@login_required
@requiere_rol('Cajero', 'Administrador')
def cobrar_pedido(request, pedido_id):
    """
    Pantalla de cobro y generación de factura fiscal.

    Roles: Cajero, Administrador
    Método: GET (formulario) | POST (procesamiento)
    GET: render cobrar.html con ítems, métodos de pago, arqueo activo.
    POST: valida timbrado, genera DocumentoTributario con número secuencial,
          aplica descuento, calcula IVA 10%, actualiza arqueo y pedido.
          Redirige a imprimir_factura tras cobro exitoso.
    Requiere: caja abierta (Arqueo) + CajaTimbrado Activo y vigente.
    """
    pedido = get_object_or_404(Pedido, id=pedido_id, estado_pago='Pendiente')
    detalles = pedido.detalles.all().select_related('producto').annotate(
        subtotal_linea=F('cantidad') * F('precio_historico')
    )

    arqueo = Arqueo.objects.filter(usuario=request.user, estado='Abierto').first()

    if request.method == 'POST':
        if not arqueo:
            messages.error(request, 'Debés abrir la caja antes de cobrar.')
            return redirect('gestion_caja')

        caja_timbrado = CajaTimbrado.objects.filter(
            caja=arqueo.caja, estado='Activo'
        ).select_related('timbrado').first()

        if not caja_timbrado:
            messages.error(request, 'No hay un timbrado activo para esta caja. Configuralo en el admin.')
            return redirect('cobrar_pedido', pedido_id=pedido_id)

        # Validar timbrado vigente
        if caja_timbrado.timbrado.fecha_vencimiento < timezone.now().date():
            messages.error(request, 'El timbrado está vencido. Actualizalo desde el admin.')
            return redirect('cobrar_pedido', pedido_id=pedido_id)

        cliente_id = request.POST.get('cliente_id')
        metodo_pago = request.POST.get('metodo_pago', 'Efectivo')
        descuento = int(request.POST.get('descuento', 0) or 0)

        # Validar que el descuento no supere el total
        total_bruto = int(pedido.total_pedido)
        if descuento < 0 or descuento > total_bruto:
            messages.error(request, 'El descuento no puede ser mayor al total del pedido.')
            return redirect('cobrar_pedido', pedido_id=pedido_id)

        if cliente_id:
            cliente = get_object_or_404(Cliente, id=cliente_id)
        else:
            cliente, _ = Cliente.objects.get_or_create(
                ruc_ci='0',
                defaults={'nombre_razon_social': 'Sin Nombre / Ocasional'}
            )

        total = total_bruto - descuento

        # Calcular IVA desglosado por tasa según los productos del pedido
        subtotal_10 = subtotal_5 = subtotal_exento = 0
        for det in pedido.detalles.select_related('producto'):
            linea = int(det.cantidad * det.precio_historico)
            tasa  = det.producto.tasa_iva
            if tasa == 10:
                subtotal_10 += linea
            elif tasa == 5:
                subtotal_5  += linea
            else:
                subtotal_exento += linea

        # Proporcionar el descuento al total antes de calcular IVA
        factor = total / total_bruto if total_bruto else 1
        monto_iva_10  = int(round(subtotal_10  * factor / 11))
        monto_iva_5   = int(round(subtotal_5   * factor / 21))
        monto_exenta  = int(round(subtotal_exento * factor))

        # Número secuencial: arranca en rango_desde si no hay documentos previos
        ultimo_num = DocumentoTributario.objects.filter(
            timbrado=caja_timbrado.timbrado
        ).aggregate(max_num=Max('numero_secuencial'))['max_num']

        if ultimo_num is None:
            numero_secuencial = caja_timbrado.timbrado.rango_desde
        else:
            numero_secuencial = ultimo_num + 1

        # Validar que no se superó el rango del timbrado
        if numero_secuencial > caja_timbrado.timbrado.rango_hasta:
            messages.error(request, 'Se agotó el rango de numeración del timbrado. Configurá uno nuevo en el admin.')
            return redirect('cobrar_pedido', pedido_id=pedido_id)

        nro_factura = (
            f"{caja_timbrado.timbrado.serie}-"
            f"{caja_timbrado.punto_expedicion}-"
            f"{numero_secuencial:07d}"
        )

        documento = DocumentoTributario.objects.create(
            timbrado=caja_timbrado.timbrado,
            arqueo=arqueo,
            cliente=cliente,
            nro_factura=nro_factura,
            numero_secuencial=numero_secuencial,
            total_exenta=monto_exenta,
            total_iva_5=monto_iva_5,
            total_iva_10=monto_iva_10,
            monto_total=total,
            metodo_pago=metodo_pago,
        )

        PedidoDocumento.objects.create(pedido=pedido, documento=documento)

        arqueo.monto_cierre_sistema = arqueo.monto_cierre_sistema + total
        arqueo.save()

        pedido.estado_pago = 'Pagado'
        pedido.fecha_cierre = timezone.now()
        pedido.metodo_pago = metodo_pago
        pedido.descuento = descuento
        pedido.cliente = cliente
        pedido.save()

        pedido.mesa.estado = 'Sucia'
        pedido.mesa.save()

        messages.success(request, f'Cobro registrado. Factura N° {nro_factura}')
        return redirect('imprimir_factura', pedido_id=pedido.id)

    context = {
        'pedido': pedido,
        'detalles': detalles,
        'arqueo': arqueo,
        'metodos_pago': Pedido.METODOS_PAGO,
    }
    return render(request, 'pedidos/cobrar.html', context)


@login_required
def buscar_clientes(request):
    """
    Endpoint AJAX de búsqueda de clientes (typeahead en cobrar.html).

    Roles: todos los autenticados
    Método: GET — ?q=<texto> (mínimo 2 caracteres)
    Retorna: JsonResponse {"clientes": [{"id", "nombre", "ruc_ci"}]}
    Excluye al cliente genérico (RUC='0'). Máximo 10 resultados.
    """
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'clientes': []})

    clientes = Cliente.objects.filter(
        Q(nombre_razon_social__icontains=q) | Q(ruc_ci__icontains=q)
    ).exclude(ruc_ci='0')[:10]

    data = [{'id': c.id, 'nombre': c.nombre_razon_social, 'ruc_ci': c.ruc_ci,
             'categoria': c.categoria, 'descuento': c.descuento_porcentaje} for c in clientes]
    return JsonResponse({'clientes': data})


# ──────────────────────────────────────────
# FASE 1 — Acciones AJAX de Mesa
# ──────────────────────────────────────────

@login_required
def marcar_sucia(request, mesa_id):
    """
    Marca una mesa como Sucia vía AJAX (requiere limpieza antes de usar).

    Roles: todos los autenticados
    Método: POST (AJAX desde salon.html)
    Retorna: JsonResponse {"ok": true, "estado": "Sucia"}
    GET retorna 405 Method Not Allowed.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    mesa = get_object_or_404(Mesa, id=mesa_id)
    mesa.estado = 'Sucia'
    mesa.save()
    return JsonResponse({'ok': True, 'estado': 'Sucia'})


@login_required
@requiere_rol('Cajero', 'Administrador')
def bloquear_mesa(request, mesa_id):
    """
    Alterna el estado de una mesa entre Libre y Reservada vía AJAX.

    Roles: Cajero, Administrador
    Método: POST (AJAX desde salon.html)
    Retorna: JsonResponse {"ok": true, "estado": "Libre"|"Reservada"}
    Lógica: Libre → Reservada; Reservada → Libre.
    Mesas Ocupadas o Sucias no se modifican.
    GET retorna 405 Method Not Allowed.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    mesa = get_object_or_404(Mesa, id=mesa_id)
    if mesa.estado == 'Libre':
        mesa.estado = 'Reservada'
    elif mesa.estado == 'Reservada':
        mesa.estado = 'Libre'
    # Mesas Ocupadas o Sucias no se tocan
    mesa.save()
    return JsonResponse({'ok': True, 'estado': mesa.estado})


# ──────────────────────────────────────────
# FASE 6.3 — Actualizar cantidad en comanda
# ──────────────────────────────────────────

@login_required
def actualizar_cantidad_ajax(request, pedido_id, detalle_id):
    """
    Edita la cantidad de un ítem del pedido vía AJAX.

    Roles: todos los autenticados
    Método: POST (fetch desde comanda.html)
    Retorna: JsonResponse {"total": "...", "items": [...con campo subtotal]}
    Restricción: solo permite editar ítems cuyo último FlujoEstado sea 'Pendiente'.
    Ítems en Cocina, Listo o Entregado devuelven 400 Bad Request.
    Cantidades < 1 se normalizan a 1 automáticamente.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    pedido = get_object_or_404(Pedido, id=pedido_id)
    detalle = get_object_or_404(PedidoDetalle, id=detalle_id, pedido=pedido)

    # Solo se puede editar si el ítem está en estado Pendiente
    ultimo_estado = FlujoEstado.objects.filter(
        pedido_detalle=detalle
    ).order_by('-timestamp').values_list('estado', flat=True).first()

    if ultimo_estado and ultimo_estado not in ('Pendiente',):
        return JsonResponse(
            {'error': 'No se puede editar un ítem que ya está en cocina'},
            status=400
        )

    try:
        cantidad = int(request.POST.get('cantidad', 1))
        if cantidad < 1:
            cantidad = 1
    except (ValueError, TypeError):
        cantidad = 1

    old_cantidad  = detalle.cantidad
    detalle.cantidad = cantidad
    detalle.save()
    pedido.actualizar_total()

    # ── Ajuste de stock por delta ─────────────────────────
    stock_info = None
    producto = detalle.producto
    if producto.stock_actual is not None:
        delta = cantidad - old_cantidad          # positivo = se piden más unidades
        producto.stock_actual = max(0, producto.stock_actual - delta)
        if producto.stock_actual == 0:
            producto.disponible = False
        elif delta < 0 and not producto.disponible:
            # Se redujo la cantidad; si tenía stock 0 y ahora hay, reactivar
            producto.disponible = True
        producto.save(update_fields=['stock_actual', 'disponible'])
        stock_info = {
            'producto_id': producto.id,
            'stock':       producto.stock_actual,
            'disponible':  producto.disponible,
        }

    items = [{
        'id': d.id,
        'cantidad': d.cantidad,
        'nombre': d.producto.nombre,
        'precio': str(d.precio_historico),
        'subtotal': str(int(d.cantidad) * int(d.precio_historico)),
    } for d in pedido.detalles.all().order_by('id')]

    return JsonResponse({
        'total':      str(pedido.total_pedido),
        'items':      items,
        'stock_info': stock_info,
    })


# ──────────────────────────────────────────
# FASE 6.4 — Toggle disponibilidad producto
# ──────────────────────────────────────────

@login_required
@requiere_rol('Cajero', 'Administrador')
def toggle_disponible_ajax(request, producto_id):
    """
    Invierte el flag disponible de un producto vía AJAX.

    Roles: Cajero, Administrador
    Método: POST (fetch desde comanda.html y productos.html)
    Retorna: JsonResponse {"ok": true, "disponible": bool}
    El template comanda.html actualiza visualmente la tarjeta del producto
    (opacidad, badge "Agotado") sin recargar la página.
    GET retorna 405 Method Not Allowed.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    producto = get_object_or_404(Producto, id=producto_id)
    producto.disponible = not producto.disponible
    producto.save()
    return JsonResponse({'ok': True, 'disponible': producto.disponible})


# ──────────────────────────────────────────
# FASE 2 — Dashboard / KPIs
# ──────────────────────────────────────────

@login_required
@requiere_rol('Cajero', 'Administrador')
def dashboard(request):
    """
    Panel de KPIs del negocio con filtro por rango de fechas.

    Roles: Cajero, Administrador
    Método: GET — parámetros opcionales ?fecha_desde=&fecha_hasta=
    Retorna: render dashboard.html con los siguientes KPIs:
      - Total facturado, cantidad de tickets y ticket promedio
      - Desglose por método de pago (con JSON para Chart.js donut)
      - Margen bruto por producto (precio_venta - costo_insumo) × cantidad
      - Top 5 productos por cantidad vendida y por revenue (con JSON para barras)
      - Rotación de mesas: pedidos por mesa y tiempo promedio de permanencia
      - Tiempo promedio de preparación en cocina (Pendiente → Listo)
      - Arqueos cerrados en el rango
      - Ranking de mozos por total vendido (ventas_por_mozo)
    Sin parámetros de fecha: muestra solo el día de hoy.
    """
    hoy = timezone.now().date()

    # Rango de fechas desde GET params
    try:
        fecha_desde = date.fromisoformat(request.GET.get('fecha_desde', str(hoy)))
        fecha_hasta = date.fromisoformat(request.GET.get('fecha_hasta', str(hoy)))
    except ValueError:
        fecha_desde = fecha_hasta = hoy

    pedidos_qs = Pedido.objects.filter(
        estado_pago='Pagado',
        fecha_cierre__date__gte=fecha_desde,
        fecha_cierre__date__lte=fecha_hasta,
    )

    # KPI 1 — Ventas generales
    ventas = pedidos_qs.aggregate(
        total_facturado=Sum('total_pedido'),
        ticket_count=Count('id'),
    )
    total_facturado = ventas['total_facturado'] or 0
    ticket_count    = ventas['ticket_count'] or 0
    ticket_promedio = int(total_facturado / ticket_count) if ticket_count else 0

    # KPI 2 — Métodos de pago
    metodos = list(
        pedidos_qs.values('metodo_pago').annotate(
            total=Sum('total_pedido'),
            cantidad=Count('id'),
        ).order_by('-total')
    )
    # Para Chart.js
    metodos_json = json.dumps([
        {'label': m['metodo_pago'] or 'Sin método', 'value': int(m['total'] or 0)}
        for m in metodos
    ])

    # KPI 3 — Margen bruto por producto
    margen_qs = PedidoDetalle.objects.filter(
        pedido__in=pedidos_qs,
    ).values(
        'producto__nombre', 'producto__categoria__nombre'
    ).annotate(
        margen=Sum(
            ExpressionWrapper(
                (F('precio_historico') - F('producto__costo_insumo')) * F('cantidad'),
                output_field=DecimalField()
            )
        ),
        revenue=Sum(
            ExpressionWrapper(F('cantidad') * F('precio_historico'), output_field=DecimalField())
        ),
    ).order_by('-revenue')[:10]

    # KPI 4 — Top 5 productos por cantidad y por revenue
    top_cantidad = list(
        PedidoDetalle.objects.filter(pedido__in=pedidos_qs)
        .values('producto__nombre')
        .annotate(total_qty=Sum('cantidad'))
        .order_by('-total_qty')[:5]
    )
    top_revenue = list(
        PedidoDetalle.objects.filter(pedido__in=pedidos_qs)
        .values('producto__nombre')
        .annotate(total_rev=Sum(ExpressionWrapper(F('cantidad') * F('precio_historico'), output_field=DecimalField())))
        .order_by('-total_rev')[:5]
    )
    # Para Chart.js barras
    top_rev_json = json.dumps([
        {'label': t['producto__nombre'], 'value': int(t['total_rev'] or 0)}
        for t in top_revenue
    ])

    # KPI 5 — Rotación de mesas
    rotacion = list(
        pedidos_qs.values('mesa__numero_mesa').annotate(
            pedidos_mesa=Count('id'),
            tiempo_promedio=Avg(
                ExpressionWrapper(F('fecha_cierre') - F('fecha_apertura'), output_field=DurationField())
            ),
        ).order_by('-pedidos_mesa')
    )
    # Convertir timedelta a minutos legibles
    for r in rotacion:
        if r['tiempo_promedio']:
            mins = int(r['tiempo_promedio'].total_seconds() / 60)
            r['tiempo_promedio_min'] = mins
        else:
            r['tiempo_promedio_min'] = None

    # KPI 6 — Tiempo promedio cocina (Pendiente → Listo)
    ts_pendiente = FlujoEstado.objects.filter(
        pedido_detalle=OuterRef('pk'), estado='Pendiente'
    ).order_by('timestamp').values('timestamp')[:1]
    ts_listo = FlujoEstado.objects.filter(
        pedido_detalle=OuterRef('pk'), estado='Listo'
    ).order_by('timestamp').values('timestamp')[:1]

    cocina_agg = PedidoDetalle.objects.filter(
        pedido__in=pedidos_qs
    ).annotate(
        ts_p=Subquery(ts_pendiente),
        ts_l=Subquery(ts_listo),
    ).filter(ts_p__isnull=False, ts_l__isnull=False).annotate(
        tiempo_prep=ExpressionWrapper(F('ts_l') - F('ts_p'), output_field=DurationField())
    ).aggregate(avg_prep=Avg('tiempo_prep'))

    tiempo_cocina_min = None
    if cocina_agg['avg_prep']:
        tiempo_cocina_min = int(cocina_agg['avg_prep'].total_seconds() / 60)

    # KPI 7 — Arqueos recientes cerrados
    arqueos_recientes = list(
        Arqueo.objects.filter(
            estado='Cerrado',
            fecha_cierre__date__gte=fecha_desde,
            fecha_cierre__date__lte=fecha_hasta,
        ).select_related('caja', 'usuario').order_by('-fecha_cierre')[:10]
    )

    # KPI 8 — Ventas por mozo (Phase 9D)
    ventas_por_mozo = list(
        pedidos_qs.values(
            'mozo__empleado__nombre',
            'mozo__empleado__apellido',
            'mozo__username',
        ).annotate(
            total=Sum('total_pedido'),
            tickets=Count('id'),
        ).order_by('-total')
    )

    context = {
        'fecha_desde':      fecha_desde,
        'fecha_hasta':      fecha_hasta,
        'total_facturado':  total_facturado,
        'ticket_count':     ticket_count,
        'ticket_promedio':  ticket_promedio,
        'metodos':          metodos,
        'metodos_json':     metodos_json,
        'margen_productos': list(margen_qs),
        'top_cantidad':     top_cantidad,
        'top_revenue':      top_revenue,
        'top_rev_json':     top_rev_json,
        'rotacion':         rotacion,
        'tiempo_cocina_min': tiempo_cocina_min,
        'arqueos':          arqueos_recientes,
        'ventas_por_mozo':  ventas_por_mozo,
    }
    return render(request, 'pedidos/dashboard.html', context)


# ──────────────────────────────────────────
# FASE 3 — Historial de Pedidos + Anulación
# ──────────────────────────────────────────

@login_required
@requiere_rol('Cajero', 'Administrador')
def historial_pedidos(request):
    """
    Lista paginada de pedidos cerrados (Pagados y Anulados).

    Roles: Cajero, Administrador
    Método: GET — filtros opcionales: ?fecha_desde=&fecha_hasta=&mozo_id=&estado=&page=
    Retorna: render historial_pedidos.html con page_obj (30 pedidos/página),
             lista de mozos disponibles para el filtro, y parámetros de filtro actuales.
    """
    qs = Pedido.objects.filter(
        estado_pago__in=['Pagado', 'Anulado']
    ).select_related('mesa', 'mozo__empleado', 'cliente').order_by('-fecha_cierre')

    # Filtros GET
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    mozo_id     = request.GET.get('mozo_id', '')
    estado      = request.GET.get('estado', '')

    if fecha_desde:
        try:
            qs = qs.filter(fecha_cierre__date__gte=date.fromisoformat(fecha_desde))
        except ValueError:
            pass
    if fecha_hasta:
        try:
            qs = qs.filter(fecha_cierre__date__lte=date.fromisoformat(fecha_hasta))
        except ValueError:
            pass
    if mozo_id:
        qs = qs.filter(mozo_id=mozo_id)
    if estado:
        qs = qs.filter(estado_pago=estado)

    paginator = Paginator(qs, 30)
    page_obj  = paginator.get_page(request.GET.get('page'))

    mozos = Empleado.objects.select_related('usuario').filter(usuario__pedido__isnull=False).distinct()

    context = {
        'page_obj':     page_obj,
        'mozos':        mozos,
        'fecha_desde':  fecha_desde,
        'fecha_hasta':  fecha_hasta,
        'mozo_id':      mozo_id,
        'estado':       estado,
    }
    return render(request, 'pedidos/historial_pedidos.html', context)


@login_required
@requiere_rol('Cajero', 'Administrador')
def detalle_historial(request, pedido_id):
    """
    Detalle completo de un pedido cerrado (Pagado o Anulado).

    Roles: Cajero, Administrador
    Método: GET
    Retorna: render detalle_historial.html con ítems (subtotal por línea),
             el PedidoDocumento vinculado activo (factura), y el pedido completo.
    También muestra el botón "Reimprimir Factura" si hay vínculo activo.
    """
    pedido   = get_object_or_404(Pedido, id=pedido_id, estado_pago__in=['Pagado', 'Anulado'])
    detalles = pedido.detalles.all().select_related('producto').annotate(
        subtotal_linea=F('cantidad') * F('precio_historico')
    )
    vinculo  = PedidoDocumento.objects.filter(
        pedido=pedido, estado_vinculo='Activo'
    ).select_related('documento__timbrado', 'documento__cliente').first()

    context = {
        'pedido':   pedido,
        'detalles': detalles,
        'vinculo':  vinculo,
    }
    return render(request, 'pedidos/detalle_historial.html', context)


@login_required
@requiere_rol('Cajero', 'Administrador')
def anular_pedido(request, pedido_id):
    """
    Anula un pedido Pagado: revierte la factura y corrige el arqueo.

    Roles: Cajero, Administrador
    Método: POST (formulario en detalle_historial.html)
    Retorna: redirect a historial_pedidos
    Proceso:
      1. Marca cada DocumentoTributario vinculado como 'Anulado'
      2. Resta el monto del documento del monto_cierre_sistema del Arqueo
      3. Marca el PedidoDocumento como 'Corregido'
      4. Cambia el estado del Pedido a 'Anulado' y libera la mesa (estado Libre)
    Solo pedidos en estado 'Pagado' pueden anularse (404 para otros estados).
    GET retorna redirect a historial_pedidos sin acción.
    """
    if request.method != 'POST':
        return redirect('historial_pedidos')

    pedido = get_object_or_404(Pedido, id=pedido_id, estado_pago='Pagado')

    # ── Restaurar stock de todos los ítems del pedido ─────
    for detalle in pedido.detalles.select_related('producto').all():
        prod = detalle.producto
        if prod.stock_actual is not None:
            prod.stock_actual += detalle.cantidad
            if prod.stock_actual > 0:
                prod.disponible = True
            prod.save(update_fields=['stock_actual', 'disponible'])

    # Anular documentos vinculados
    vinculos = PedidoDocumento.objects.filter(pedido=pedido, estado_vinculo='Activo').select_related('documento__arqueo')
    for vinculo in vinculos:
        doc = vinculo.documento
        doc.estado = 'Anulado'
        doc.save()
        # Restar del arqueo (corrección contable)
        arqueo = doc.arqueo
        arqueo.monto_cierre_sistema = arqueo.monto_cierre_sistema - doc.monto_total
        arqueo.save()
        vinculo.estado_vinculo = 'Corregido'
        vinculo.save()

    pedido.estado_pago  = 'Anulado'
    pedido.mesa.estado  = 'Libre'
    pedido.mesa.save()
    pedido.save()

    messages.success(request, f'Pedido #{pedido_id} anulado correctamente.')
    return redirect('historial_pedidos')


# ──────────────────────────────────────────
# FASE 4 — Gestión de Reservaciones
# ──────────────────────────────────────────

@login_required
@requiere_rol('Mozo', 'Cajero', 'Administrador')
def lista_reservaciones(request):
    """
    Lista de reservaciones confirmadas para hoy o la próxima semana.

    Roles: Mozo, Cajero, Administrador
    Método: GET — parámetro opcional ?vista=hoy|semana (default: hoy)
    Retorna: render reservaciones.html con reservaciones ordenadas por fecha_reserva,
             parámetro vista actual y fecha de hoy para resaltar.
    """
    hoy   = timezone.now().date()
    vista = request.GET.get('vista', 'hoy')
    if vista == 'semana':
        hasta = hoy + timedelta(days=7)
        qs = Reservacion.objects.filter(
            fecha_reserva__date__gte=hoy,
            fecha_reserva__date__lte=hasta,
            estado='Confirmada',
        )
    else:
        qs = Reservacion.objects.filter(
            fecha_reserva__date=hoy,
            estado='Confirmada',
        )
    reservaciones = qs.select_related('mesa__sector', 'cliente', 'empleado__empleado').order_by('fecha_reserva')
    context = {'reservaciones': reservaciones, 'vista': vista, 'hoy': hoy}
    return render(request, 'pedidos/reservaciones.html', context)


@login_required
@requiere_rol('Mozo', 'Cajero', 'Administrador')
def crear_reservacion(request, mesa_id):
    """
    Crea una reservación para una mesa disponible, con detección de conflictos.

    Roles: Mozo, Cajero, Administrador
    Método: GET (formulario) | POST (procesamiento)
    GET: render crear_reservacion.html — solo si la mesa está Libre o Sucia.
    POST: valida la fecha, detecta conflictos de horario (±2 horas con otras reservas
          Confirmadas para la misma mesa), asigna cliente (o genérico si no se especifica),
          crea la Reservacion y cambia el estado de la mesa a 'Reservada'.
          Redirige al salón tras crear la reserva.
    Mesas Ocupadas o Reservadas: redirige al salón con mensaje de error.
    """
    mesa = get_object_or_404(Mesa, id=mesa_id)
    if mesa.estado not in ('Libre', 'Sucia'):
        messages.error(request, f'La mesa {mesa.numero_mesa} no está disponible para reservar.')
        return redirect('salon')

    if request.method == 'POST':
        fecha_str   = request.POST.get('fecha_reserva', '')
        cantidad    = max(1, int(request.POST.get('cantidad_personas', 1) or 1))
        observaciones = request.POST.get('observaciones', '').strip()
        cliente_id  = request.POST.get('cliente_id', '').strip()

        try:
            fecha_reserva = timezone.make_aware(datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M'))
        except ValueError:
            messages.error(request, 'Fecha y hora inválidas.')
            return render(request, 'pedidos/crear_reservacion.html', {'mesa': mesa})

        # Fase 8B — Validar conflicto de horario (±2 horas)
        ventana_inicio = fecha_reserva - timedelta(hours=2)
        ventana_fin    = fecha_reserva + timedelta(hours=2)
        conflicto = Reservacion.objects.filter(
            mesa=mesa, estado='Confirmada',
            fecha_reserva__gte=ventana_inicio,
            fecha_reserva__lte=ventana_fin,
        ).exists()
        if conflicto:
            messages.error(
                request,
                f'La Mesa {mesa.numero_mesa} ya tiene una reserva en ese horario (±2 hs).'
            )
            return render(request, 'pedidos/crear_reservacion.html', {'mesa': mesa})

        if cliente_id:
            cliente = get_object_or_404(Cliente, id=cliente_id)
        else:
            cliente, _ = Cliente.objects.get_or_create(
                ruc_ci='0',
                defaults={'nombre_razon_social': 'Sin Nombre / Ocasional'}
            )

        Reservacion.objects.create(
            mesa=mesa,
            cliente=cliente,
            empleado=request.user,
            fecha_reserva=fecha_reserva,
            cantidad_personas=cantidad,
            observaciones=observaciones,
        )
        mesa.estado = 'Reservada'
        mesa.save()

        messages.success(request, f'Reserva creada para Mesa {mesa.numero_mesa}.')
        return redirect('salon')

    return render(request, 'pedidos/crear_reservacion.html', {'mesa': mesa})


@login_required
@requiere_rol('Mozo', 'Cajero', 'Administrador')
def cancelar_reservacion(request, reservacion_id):
    """
    Cancela una reservación Confirmada y libera la mesa si no hay otras activas.

    Roles: Mozo, Cajero, Administrador
    Método: POST (formulario en reservaciones.html)
    Retorna: redirect a lista_reservaciones
    La mesa vuelve a estado 'Libre' solo si no quedan otras reservas Confirmadas
    para esa misma mesa. GET redirige sin acción.
    """
    if request.method != 'POST':
        return redirect('lista_reservaciones')

    reservacion = get_object_or_404(Reservacion, id=reservacion_id, estado='Confirmada')
    reservacion.estado = 'Cancelada'
    reservacion.save()

    # Liberar mesa solo si no quedan otras reservas confirmadas
    otras = Reservacion.objects.filter(
        mesa=reservacion.mesa, estado='Confirmada'
    ).exclude(id=reservacion.id)
    if not otras.exists():
        reservacion.mesa.estado = 'Libre'
        reservacion.mesa.save()

    messages.success(request, 'Reserva cancelada.')
    return redirect('lista_reservaciones')


@login_required
@requiere_rol('Mozo', 'Cajero', 'Administrador')
def activar_mesa_reservada(request, reservacion_id):
    """
    Convierte una reservación en pedido activo al momento de la llegada del cliente.

    Roles: Mozo, Cajero, Administrador
    Método: POST (botón en salon.html sobre mesa Reservada)
    Retorna: redirect a abrir_mesa — que crea el Pedido y redirige a la comanda
    La reservación pasa al estado 'Completada'. La mesa queda Ocupada.
    GET redirige al salón sin acción.
    """
    if request.method != 'POST':
        return redirect('salon')
    reservacion = get_object_or_404(Reservacion, id=reservacion_id, estado='Confirmada')
    reservacion.estado = 'Completada'
    reservacion.save()
    return redirect('abrir_mesa', mesa_id=reservacion.mesa.id)


# ──────────────────────────────────────────
# FASE 5 — Gestión de Clientes
# ──────────────────────────────────────────

@login_required
@requiere_rol('Cajero', 'Administrador')
def lista_clientes(request):
    """
    Lista paginada de clientes registrados con búsqueda por nombre o RUC/CI.

    Roles: Cajero, Administrador
    Método: GET — parámetros opcionales: ?q=<texto>&page=<n>
    Retorna: render clientes.html con page_obj (25 clientes/página) y el parámetro q.
    Excluye al cliente genérico (RUC='0'). Ordenados alfabéticamente.
    """
    q  = request.GET.get('q', '').strip()
    qs = Cliente.objects.exclude(ruc_ci='0').order_by('nombre_razon_social')
    if q:
        qs = qs.filter(Q(nombre_razon_social__icontains=q) | Q(ruc_ci__icontains=q))
    paginator = Paginator(qs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'clientes': page_obj, 'q': q}
    return render(request, 'pedidos/clientes.html', context)


@login_required
@requiere_rol('Cajero', 'Administrador')
def crear_cliente(request):
    """
    Formulario de alta de nuevo cliente.

    Roles: Cajero, Administrador
    Método: GET (formulario vacío) | POST (crear)
    Retorna GET: render cliente_form.html con accion='Crear'
    Retorna POST éxito: redirect a lista_clientes
    Retorna POST error: render cliente_form.html con mensaje de error y datos previos
    Validaciones: nombre y RUC/CI son obligatorios; RUC/CI único (IntegrityError → error amigable).
    Usa variables v_* en contexto para evitar bug de Django 6.0 con |default:.
    """
    if request.method == 'POST':
        nombre    = request.POST.get('nombre_razon_social', '').strip()
        ruc_ci    = request.POST.get('ruc_ci', '').strip()
        telefono  = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        categoria = request.POST.get('categoria', 'Casual')
        error     = None
        if not nombre or not ruc_ci:
            error = 'Nombre y RUC/CI son obligatorios.'
        else:
            try:
                Cliente.objects.create(
                    nombre_razon_social=nombre,
                    ruc_ci=ruc_ci,
                    telefono=telefono or None,
                    direccion=direccion or None,
                    categoria=categoria,
                )
                messages.success(request, f'Cliente "{nombre}" creado correctamente.')
                return redirect('lista_clientes')
            except IntegrityError:
                error = f'Ya existe un cliente con el RUC/CI "{ruc_ci}".'
        return render(request, 'pedidos/cliente_form.html', {
            'error': error, 'accion': 'Crear',
            'v_nombre': nombre, 'v_ruc': ruc_ci,
            'v_telefono': telefono, 'v_direccion': direccion,
            'v_categoria': categoria, 'categorias': Cliente.CATEGORIAS,
        })
    return render(request, 'pedidos/cliente_form.html', {
        'accion': 'Crear',
        'v_nombre': '', 'v_ruc': '', 'v_telefono': '', 'v_direccion': '',
        'v_categoria': 'Casual', 'categorias': Cliente.CATEGORIAS,
    })


@login_required
@requiere_rol('Cajero', 'Administrador')
def editar_cliente(request, cliente_id):
    """
    Formulario de edición de un cliente existente.

    Roles: Cajero, Administrador
    Método: GET (formulario con datos actuales) | POST (guardar cambios)
    Retorna GET: render cliente_form.html con accion='Editar' y datos del cliente
    Retorna POST éxito: redirect a lista_clientes
    Retorna POST error: render cliente_form.html con mensaje de error y datos enviados
    Validaciones: igual que crear_cliente (nombre+RUC obligatorios, RUC único).
    Usa variables v_* en contexto para evitar bug de Django 6.0 con |default:.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        nombre    = request.POST.get('nombre_razon_social', '').strip()
        ruc_ci    = request.POST.get('ruc_ci', '').strip()
        telefono  = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        categoria = request.POST.get('categoria', 'Casual')
        error     = None
        if not nombre or not ruc_ci:
            error = 'Nombre y RUC/CI son obligatorios.'
        else:
            try:
                cliente.nombre_razon_social = nombre
                cliente.ruc_ci    = ruc_ci
                cliente.telefono  = telefono or None
                cliente.direccion = direccion or None
                cliente.categoria = categoria
                cliente.save()
                messages.success(request, f'Cliente "{nombre}" actualizado.')
                return redirect('lista_clientes')
            except IntegrityError:
                error = f'Ya existe un cliente con el RUC/CI "{ruc_ci}".'
        return render(request, 'pedidos/cliente_form.html', {
            'error': error, 'accion': 'Editar',
            'v_nombre': nombre, 'v_ruc': ruc_ci,
            'v_telefono': telefono, 'v_direccion': direccion,
            'v_categoria': categoria, 'categorias': Cliente.CATEGORIAS,
        })
    return render(request, 'pedidos/cliente_form.html', {
        'accion': 'Editar',
        'v_nombre': cliente.nombre_razon_social,
        'v_ruc': cliente.ruc_ci,
        'v_telefono': cliente.telefono or '',
        'v_direccion': cliente.direccion or '',
        'v_categoria': cliente.categoria,
        'categorias': Cliente.CATEGORIAS,
    })


# ──────────────────────────────────────────
# FASE 7 — Gestión de Menú
# ──────────────────────────────────────────

@login_required
@requiere_rol('Cajero', 'Administrador')
def lista_productos(request):
    """
    Lista paginada del menú con filtros por nombre, categoría y disponibilidad.

    Roles: Cajero, Administrador
    Método: GET — parámetros opcionales: ?q=&categoria=&disponible=0|1&page=
    Retorna: render productos.html con page_obj (30 productos/página),
             lista de categorías para el filtro, y parámetros de filtro actuales.
    Ordenado por categoría → nombre. Incluye columna de margen % calculada en template.
    """
    q = request.GET.get('q', '').strip()
    cat_id = request.GET.get('categoria', '')
    disp = request.GET.get('disponible', '')

    qs = Producto.objects.select_related('categoria').order_by('categoria__nombre', 'nombre')
    if q:
        qs = qs.filter(nombre__icontains=q)
    if cat_id:
        qs = qs.filter(categoria_id=cat_id)
    if disp == '1':
        qs = qs.filter(disponible=True)
    elif disp == '0':
        qs = qs.filter(disponible=False)

    paginator = Paginator(qs, 30)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    categorias = Categoria.objects.all().order_by('nombre')
    context = {
        'page_obj': page_obj,
        'productos': page_obj,
        'categorias': categorias,
        'q': q,
        'cat_id': cat_id,
        'disp': disp,
    }
    return render(request, 'pedidos/productos.html', context)


@login_required
@requiere_rol('Cajero', 'Administrador')
def crear_producto(request):
    """
    Formulario de alta de nuevo producto del menú.

    Roles: Cajero, Administrador
    Método: GET (formulario vacío) | POST (crear)
    Retorna GET: render producto_form.html con accion='Crear' y lista de categorías
    Retorna POST éxito: redirect a lista_productos
    Retorna POST error: render producto_form.html con error y datos previos
    Validaciones: nombre, categoría y precio_venta son obligatorios; precio y costo
                  deben ser enteros (Guaraníes sin decimales).
    Soporta carga de imagen via request.FILES (Pillow requerido). Campo enctype multipart.
    Usa variables v_* en contexto para evitar bug de Django 6.0 con |default:.
    """
    categorias = Categoria.objects.all().order_by('nombre')
    if request.method == 'POST':
        nombre      = request.POST.get('nombre', '').strip()
        cat_id      = request.POST.get('categoria', '')
        precio      = request.POST.get('precio_venta', '').strip()
        costo       = request.POST.get('costo_insumo', '0').strip() or '0'
        disponible  = request.POST.get('disponible') == '1'
        imagen      = request.FILES.get('imagen')
        error = None
        if not nombre:
            error = 'El nombre del producto es obligatorio.'
        elif not cat_id:
            error = 'Seleccioná una categoría.'
        elif not precio:
            error = 'El precio de venta es obligatorio.'
        else:
            try:
                precio  = int(precio)
                costo   = int(costo)
                cat     = get_object_or_404(Categoria, id=cat_id)
                stock_str = request.POST.get('stock_actual', '').strip()
                stock_actual = None if not stock_str else max(0, int(stock_str))
                tasa_iva = int(request.POST.get('tasa_iva', 10))
                prod = Producto(nombre=nombre, categoria=cat,
                                precio_venta=precio, costo_insumo=costo,
                                disponible=disponible, stock_actual=stock_actual,
                                tasa_iva=tasa_iva)
                if imagen:
                    prod.imagen = imagen
                prod.save()
                messages.success(request, f'Producto "{nombre}" creado correctamente.')
                return redirect('lista_productos')
            except (ValueError, TypeError):
                error = 'Precio, costo y stock deben ser números enteros.'
        stock_str = request.POST.get('stock_actual', '')
        return render(request, 'pedidos/producto_form.html', {
            'accion': 'Crear', 'error': error, 'categorias': categorias,
            'tasas_iva': Producto.TASAS_IVA,
            'v_nombre': nombre, 'v_cat': cat_id, 'v_precio': precio,
            'v_costo': costo, 'v_disponible': disponible, 'v_stock': stock_str,
            'v_tasa_iva': int(request.POST.get('tasa_iva', 10)),
        })
    return render(request, 'pedidos/producto_form.html', {
        'accion': 'Crear', 'categorias': categorias,
        'tasas_iva': Producto.TASAS_IVA,
        'v_nombre': '', 'v_cat': '', 'v_precio': '', 'v_costo': '0',
        'v_disponible': True, 'v_stock': '', 'v_tasa_iva': 10,
    })


@login_required
@requiere_rol('Cajero', 'Administrador')
def editar_producto(request, producto_id):
    """
    Formulario de edición de un producto existente del menú.

    Roles: Cajero, Administrador
    Método: GET (formulario con datos actuales) | POST (guardar cambios)
    Retorna GET: render producto_form.html con accion='Editar', datos del producto y categorías
    Retorna POST éxito: redirect a lista_productos
    Retorna POST error: render producto_form.html con error y datos enviados
    Soporta reemplazo de imagen (si se sube nueva imagen vía FILES).
    Validaciones y formato iguales a crear_producto.
    Usa variables v_* en contexto para evitar bug de Django 6.0 con |default:.
    """
    prod = get_object_or_404(Producto, id=producto_id)
    categorias = Categoria.objects.all().order_by('nombre')
    if request.method == 'POST':
        nombre     = request.POST.get('nombre', '').strip()
        cat_id     = request.POST.get('categoria', '')
        precio     = request.POST.get('precio_venta', '').strip()
        costo      = request.POST.get('costo_insumo', '0').strip() or '0'
        disponible = request.POST.get('disponible') == '1'
        imagen     = request.FILES.get('imagen')
        error = None
        if not nombre:
            error = 'El nombre del producto es obligatorio.'
        elif not cat_id:
            error = 'Seleccioná una categoría.'
        elif not precio:
            error = 'El precio de venta es obligatorio.'
        else:
            try:
                stock_str = request.POST.get('stock_actual', '').strip()
                prod.nombre       = nombre
                prod.categoria    = get_object_or_404(Categoria, id=cat_id)
                prod.precio_venta = int(precio)
                prod.costo_insumo = int(costo)
                prod.disponible   = disponible
                prod.stock_actual = None if not stock_str else max(0, int(stock_str))
                prod.tasa_iva     = int(request.POST.get('tasa_iva', 10))
                if imagen:
                    prod.imagen = imagen
                prod.save()
                messages.success(request, f'Producto "{nombre}" actualizado.')
                return redirect('lista_productos')
            except (ValueError, TypeError):
                error = 'Precio, costo y stock deben ser números enteros.'
        stock_str = request.POST.get('stock_actual', '')
        return render(request, 'pedidos/producto_form.html', {
            'accion': 'Editar', 'error': error, 'categorias': categorias,
            'tasas_iva': Producto.TASAS_IVA,
            'producto': prod,
            'v_nombre': nombre, 'v_cat': cat_id, 'v_precio': precio,
            'v_costo': costo, 'v_disponible': disponible, 'v_stock': stock_str,
            'v_tasa_iva': int(request.POST.get('tasa_iva', 10)),
        })
    return render(request, 'pedidos/producto_form.html', {
        'accion': 'Editar', 'categorias': categorias,
        'tasas_iva': Producto.TASAS_IVA,
        'producto': prod,
        'v_nombre':    prod.nombre,
        'v_cat':       str(prod.categoria_id),
        'v_precio':    str(int(prod.precio_venta)),
        'v_costo':     str(int(prod.costo_insumo)),
        'v_disponible': prod.disponible,
        'v_stock':     '' if prod.stock_actual is None else str(prod.stock_actual),
        'v_tasa_iva':  prod.tasa_iva,
    })


@login_required
@requiere_rol('Cajero', 'Administrador')
def lista_categorias(request):
    """
    Gestión de categorías de menú en una sola página (inline CRUD).

    Roles: Cajero, Administrador
    Método: GET (lista + formularios) | POST (crear o editar)
    GET: render categorias.html con lista de categorías anotadas con total_productos.
         Si ?editar=<id>: precarga esa categoría en el formulario de edición.
    POST crear: crea nueva categoría; nombre único (IntegrityError → error amigable).
    POST editar: actualiza nombre de categoría existente.
    Siempre redirige con redirect() tras POST exitoso (PRG pattern).
    """
    error = None
    editar_cat = None

    if request.method == 'POST':
        accion = request.POST.get('accion', 'crear')
        nombre = request.POST.get('nombre', '').strip()

        if not nombre:
            error = 'El nombre de la categoría no puede estar vacío.'
        elif accion == 'crear':
            try:
                Categoria.objects.create(nombre=nombre)
                messages.success(request, f'Categoría "{nombre}" creada.')
                return redirect('lista_categorias')
            except IntegrityError:
                error = f'Ya existe una categoría con ese nombre.'
        elif accion == 'editar':
            cat_id = request.POST.get('cat_id')
            cat = get_object_or_404(Categoria, id=cat_id)
            cat.nombre = nombre
            cat.save()
            messages.success(request, f'Categoría actualizada a "{nombre}".')
            return redirect('lista_categorias')

    edit_id = request.GET.get('editar')
    if edit_id:
        editar_cat = Categoria.objects.filter(id=edit_id).first()

    categorias = Categoria.objects.annotate(
        total_productos=Count('producto')
    ).order_by('nombre')

    return render(request, 'pedidos/categorias.html', {
        'categorias': categorias,
        'error': error,
        'editar_cat': editar_cat,
    })


@login_required
@requiere_rol('Cajero', 'Administrador')
def reponer_stock(request, producto_id):
    """
    Actualiza el stock de un producto desde la lista de menú.

    Roles: Cajero, Administrador
    Método: POST (formulario en productos.html vía modal)
    Retorna: redirect a lista_productos
    Si el campo stock_actual se envía vacío → stock_actual=None (sin control).
    Si se envía un número → se establece ese valor exacto.
    Restaura automáticamente disponible=True si el nuevo stock > 0.
    Pone disponible=False si el nuevo stock == 0.
    """
    if request.method != 'POST':
        return redirect('lista_productos')
    producto  = get_object_or_404(Producto, id=producto_id)
    stock_str = request.POST.get('stock_actual', '').strip()
    try:
        if stock_str == '':
            producto.stock_actual = None      # sin control de stock
        else:
            producto.stock_actual = max(0, int(stock_str))
        # Sincronizar disponible con el nuevo stock
        if producto.stock_actual is None or producto.stock_actual > 0:
            producto.disponible = True
        else:
            producto.disponible = False
        producto.save(update_fields=['stock_actual', 'disponible'])
        label = 'ilimitado' if producto.stock_actual is None else str(producto.stock_actual)
        messages.success(request, f'Stock de "{producto.nombre}" actualizado a {label}.')
    except (ValueError, TypeError):
        messages.error(request, 'El stock debe ser un número entero positivo.')
    return redirect('lista_productos')


# ──────────────────────────────────────────
# FASE 8 — Factura Imprimible + Conflictos
# ──────────────────────────────────────────

@login_required
@requiere_rol('Cajero', 'Administrador')
def imprimir_factura(request, pedido_id):
    """
    Genera el layout imprimible de la factura (ticket térmico 80 mm / 320 px).

    Roles: Cajero, Administrador
    Método: GET
    Retorna: render factura_print.html sin navbar (hide_navbar=True) con:
      - Ítems del pedido con subtotal por línea
      - Documento tributario vinculado (número de factura, timbrado, cliente)
      - Datos del restaurante desde ConfiguracionRestaurante (singleton id=1)
      - IVA 10% desglosado en el pie de la factura
    El template incluye @media print CSS y botón window.print().
    Accesible desde cobrar_pedido (redirect automático) y desde detalle_historial (Reimprimir).
    """
    pedido = get_object_or_404(Pedido, id=pedido_id, estado_pago='Pagado')
    detalles = pedido.detalles.all().select_related('producto').annotate(
        subtotal_linea=F('cantidad') * F('precio_historico')
    )
    vinculo = PedidoDocumento.objects.filter(
        pedido=pedido, estado_vinculo='Activo'
    ).select_related('documento__timbrado', 'documento__cliente').first()

    # Obtener configuración del restaurante (singleton)
    try:
        from .models import ConfiguracionRestaurante
        config = ConfiguracionRestaurante.objects.get_or_create(id=1)[0]
    except Exception:
        config = None

    context = {
        'pedido': pedido,
        'detalles': detalles,
        'vinculo': vinculo,
        'config': config,
        'hide_navbar': True,
    }
    return render(request, 'pedidos/factura_print.html', context)


# ──────────────────────────────────────────
# FASE 9 — Config + Error Pages
# ──────────────────────────────────────────

def error_404(request, exception=None):
    """
    Manejador personalizado de errores 404 (página no encontrada).

    Registrado en core/urls.py como handler404.
    Solo se activa con DEBUG=False (en producción).
    Con DEBUG=True Django usa su propia página de debug en su lugar.
    Retorna: render 404.html con status 404 — Japandi-styled.
    """
    return render(request, 'pedidos/404.html', status=404)


def error_500(request):
    """
    Manejador personalizado de errores 500 (error interno del servidor).

    Registrado en core/urls.py como handler500.
    Solo se activa con DEBUG=False (en producción).
    Retorna: render 500.html con status 500 — Japandi-styled.
    """
    return render(request, 'pedidos/500.html', status=500)


@login_required
def guardar_nota_ajax(request, detalle_id):
    """
    Guarda la nota/observación de un PedidoDetalle.

    Roles: todos los autenticados
    Método: POST
    Retorna: JSON {ok}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    detalle = get_object_or_404(PedidoDetalle, id=detalle_id)
    detalle.observaciones = request.POST.get('nota', '').strip()
    detalle.save()
    return JsonResponse({'ok': True})


@login_required
def transferir_pedido(request, pedido_id):
    """
    Transfiere un pedido a otra mesa libre.

    Roles: todos los autenticados
    Método: POST
    Retorna: JSON {ok, error}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    pedido = get_object_or_404(Pedido, id=pedido_id)
    nueva_mesa_id = request.POST.get('mesa_id')

    if not nueva_mesa_id:
        return JsonResponse({'error': 'Mesa no especificada'}, status=400)

    nueva_mesa = get_object_or_404(Mesa, id=nueva_mesa_id)

    if nueva_mesa.estado != 'Libre':
        return JsonResponse({'error': f'La mesa {nueva_mesa.numero_mesa} no está libre'}, status=400)

    if nueva_mesa == pedido.mesa:
        return JsonResponse({'error': 'La mesa de destino es la misma'}, status=400)

    mesa_anterior = pedido.mesa
    mesa_anterior.estado = 'Libre'
    mesa_anterior.save()

    nueva_mesa.estado = 'Ocupada'
    nueva_mesa.save()

    pedido.mesa = nueva_mesa
    pedido.save()

    return JsonResponse({'ok': True, 'nueva_mesa': nueva_mesa.numero_mesa})


@login_required
@requiere_rol('Cajero', 'Administrador')
def reporte_iva(request):
    """
    Reporte mensual de IVA para declaración SET Paraguay.

    Roles: Cajero, Administrador
    Método: GET — ?mes=MM&anio=YYYY, exportar=1 para descargar Excel
    Retorna: render reporte_iva.html o HttpResponse Excel
    IVA 10% incluido = total / 11
    """
    hoy = date.today()
    mes  = int(request.GET.get('mes',  hoy.month))
    anio = int(request.GET.get('anio', hoy.year))

    documentos = (DocumentoTributario.objects
                  .filter(estado='Vigente',
                          pedidodocumento__pedido__fecha_cierre__year=anio,
                          pedidodocumento__pedido__fecha_cierre__month=mes,
                          pedidodocumento__estado_vinculo='Activo')
                  .select_related('cliente')
                  .prefetch_related('pedidodocumento_set__pedido')
                  .order_by('nro_factura'))

    # Calcular IVA por factura
    filas = []
    total_gravado = 0
    total_iva     = 0
    total_general = 0

    for doc in documentos:
        vinculo = doc.pedidodocumento_set.filter(estado_vinculo='Activo').first()
        fecha   = vinculo.pedido.fecha_cierre if vinculo else None
        cliente = doc.cliente
        monto   = int(doc.monto_total)
        iva     = int(monto / 11)
        gravado = monto - iva
        total_gravado += gravado
        total_iva     += iva
        total_general += monto
        filas.append({
            'nro_factura': doc.nro_factura,
            'fecha':       fecha,
            'cliente':     cliente.nombre_razon_social if cliente and cliente.ruc_ci != '0' else 'Consumidor Final',
            'ruc_ci':      cliente.ruc_ci if cliente and cliente.ruc_ci != '0' else '—',
            'gravado':     gravado,
            'iva':         iva,
            'total':       monto,
            'metodo':      doc.metodo_pago,
        })

    if request.GET.get('exportar') == '1':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f'IVA {mes:02d}-{anio}'
        cols = ['N° Factura', 'Fecha', 'Cliente', 'RUC/CI', 'Gravado (Gs.)', 'IVA 10% (Gs.)', 'Total (Gs.)', 'Método de Pago']
        _estilo_encabezado(ws, 1, cols)
        for f in filas:
            fecha_val = f['fecha'].astimezone().replace(tzinfo=None) if f['fecha'] else ''
            ws.append([f['nro_factura'], fecha_val, f['cliente'], f['ruc_ci'], f['gravado'], f['iva'], f['total'], f['metodo']])
        ws.append([])
        ws.append(['TOTALES', '', '', '', total_gravado, total_iva, total_general, ''])
        total_row = ws.max_row
        for col in range(1, 9):
            ws.cell(row=total_row, column=col).font = Font(bold=True)
        _ajustar_columnas(ws)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        nombre = f"iva_{mes:02d}_{anio}.xlsx"
        resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return resp

    meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    context = {
        'filas': filas,
        'mes': mes, 'anio': anio,
        'mes_nombre': meses[mes - 1],
        'total_gravado': total_gravado,
        'total_iva': total_iva,
        'total_general': total_general,
        'meses': [(i+1, m) for i, m in enumerate(meses)],
        'anios': range(anio - 2, anio + 1),
    }
    return render(request, 'pedidos/reporte_iva.html', context)


@login_required
@requiere_rol('Cajero', 'Administrador')
def reporte_z(request):
    """
    Reporte Z (cierre del día): resumen de ventas de una fecha con desglose
    por método de pago, IVA y listado de facturas.

    Roles: Cajero, Administrador
    Método: GET — ?fecha=YYYY-MM-DD, exportar=1 para Excel
    """
    hoy = date.today()
    fecha_str = request.GET.get('fecha', hoy.isoformat())
    try:
        fecha = date.fromisoformat(fecha_str)
    except ValueError:
        fecha = hoy

    docs = (DocumentoTributario.objects
            .filter(estado='Vigente',
                    pedidodocumento__pedido__fecha_cierre__date=fecha,
                    pedidodocumento__estado_vinculo='Activo')
            .select_related('cliente')
            .prefetch_related('pedidodocumento_set__pedido')
            .order_by('nro_factura'))

    filas = []
    total_general = 0
    total_iva     = 0
    metodos = {}

    for doc in docs:
        vinculo = doc.pedidodocumento_set.filter(estado_vinculo='Activo').first()
        fecha_doc = vinculo.pedido.fecha_cierre if vinculo else None
        cliente   = doc.cliente
        monto     = int(doc.monto_total)
        iva       = int(monto / 11)
        total_general += monto
        total_iva     += iva
        metodos[doc.metodo_pago] = metodos.get(doc.metodo_pago, 0) + monto
        filas.append({
            'nro_factura': doc.nro_factura,
            'hora':        fecha_doc,
            'cliente':     cliente.nombre_razon_social if cliente and cliente.ruc_ci != '0' else 'Consumidor Final',
            'iva':         iva,
            'total':       monto,
            'metodo':      doc.metodo_pago,
        })

    if request.GET.get('exportar') == '1':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f'Cierre {fecha.isoformat()}'
        # Resumen
        _estilo_encabezado(ws, 1, ['Indicador', 'Valor (Gs.)'])
        ws.append(['Total Facturado', total_general])
        ws.append(['IVA 10% (incluido)', total_iva])
        ws.append(['Cantidad de Tickets', len(filas)])
        ws.append([])
        for metodo, total in metodos.items():
            ws.append([metodo, total])
        ws.append([])
        # Detalle
        _estilo_encabezado(ws, ws.max_row + 1, ['N° Factura', 'Hora', 'Cliente', 'IVA 10%', 'Total', 'Método'])
        for f in filas:
            hora_val = f['hora'].astimezone().replace(tzinfo=None) if f['hora'] else ''
            ws.append([f['nro_factura'], hora_val, f['cliente'], f['iva'], f['total'], f['metodo']])
        _ajustar_columnas(ws)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        nombre = f"cierre_z_{fecha.isoformat()}.xlsx"
        resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return resp

    context = {
        'fecha': fecha,
        'filas': filas,
        'total_general': total_general,
        'total_iva': total_iva,
        'total_gravado': total_general - total_iva,
        'metodos': metodos,
        'tickets': len(filas),
    }
    return render(request, 'pedidos/reporte_cierre.html', context)


def _estilo_encabezado(ws, fila, columnas):
    """Aplica negrita, fondo gris y alineación centrada a la fila de encabezado."""
    fill = PatternFill('solid', fgColor='D9D9D9')
    for col, titulo in enumerate(columnas, 1):
        cell = ws.cell(row=fila, column=col, value=titulo)
        cell.font = Font(bold=True)
        cell.fill = fill
        cell.alignment = Alignment(horizontal='center')
    ws.row_dimensions[fila].height = 18


def _ajustar_columnas(ws):
    for col in ws.columns:
        max_len = max((len(str(c.value or '')) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)


@login_required
@requiere_rol('Cajero', 'Administrador')
def exportar_historial_excel(request):
    """
    Exporta el historial de pedidos (con los mismos filtros del historial) a .xlsx.

    Roles: Cajero, Administrador
    Método: GET — mismos parámetros que historial_pedidos
    """
    qs = Pedido.objects.filter(
        estado_pago__in=['Pagado', 'Anulado']
    ).select_related('mesa', 'mozo', 'cliente').order_by('-fecha_cierre')

    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    mozo_id     = request.GET.get('mozo_id', '')
    estado      = request.GET.get('estado', '')

    if fecha_desde:
        try:
            qs = qs.filter(fecha_cierre__date__gte=date.fromisoformat(fecha_desde))
        except ValueError:
            pass
    if fecha_hasta:
        try:
            qs = qs.filter(fecha_cierre__date__lte=date.fromisoformat(fecha_hasta))
        except ValueError:
            pass
    if mozo_id:
        qs = qs.filter(mozo_id=mozo_id)
    if estado:
        qs = qs.filter(estado_pago=estado)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Historial de Pedidos'

    cols = ['#', 'Fecha Cierre', 'Mesa', 'Mozo', 'Cliente', 'Método de Pago', 'Descuento (Gs.)', 'Total (Gs.)', 'Estado']
    _estilo_encabezado(ws, 1, cols)

    for pedido in qs:
        ws.append([
            pedido.id,
            pedido.fecha_cierre.astimezone().replace(tzinfo=None) if pedido.fecha_cierre else '',
            pedido.mesa.numero_mesa,
            pedido.mozo.get_full_name() or pedido.mozo.username,
            pedido.cliente.nombre_razon_social if pedido.cliente else 'Ocasional',
            pedido.metodo_pago or '',
            int(pedido.descuento or 0),
            int(pedido.total_pedido or 0),
            pedido.estado_pago,
        ])

    _ajustar_columnas(ws)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    nombre = f"historial_{date.today().isoformat()}.xlsx"
    resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return resp


@login_required
@requiere_rol('Cajero', 'Administrador')
def exportar_dashboard_excel(request):
    """
    Exporta los KPIs del dashboard a .xlsx con múltiples hojas.

    Roles: Cajero, Administrador
    Método: GET — mismos parámetros que dashboard (?fecha_desde=&fecha_hasta=)
    Hojas: Resumen, Top Productos, Ventas por Mozo, Rotación de Mesas
    """
    from django.db.models.functions import TruncDate

    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    qs_base = Pedido.objects.filter(estado_pago='Pagado')
    if fecha_desde:
        try:
            qs_base = qs_base.filter(fecha_cierre__date__gte=date.fromisoformat(fecha_desde))
        except ValueError:
            pass
    if fecha_hasta:
        try:
            qs_base = qs_base.filter(fecha_cierre__date__lte=date.fromisoformat(fecha_hasta))
        except ValueError:
            pass

    wb = openpyxl.Workbook()

    # ── Hoja 1: Resumen general ──────────────────────────────
    ws1 = wb.active
    ws1.title = 'Resumen'
    totales = qs_base.aggregate(facturado=Sum('total_pedido'), tickets=Count('id'))
    facturado = int(totales['facturado'] or 0)
    tickets   = totales['tickets'] or 0
    promedio  = facturado // tickets if tickets else 0

    _estilo_encabezado(ws1, 1, ['Indicador', 'Valor'])
    ws1.append(['Total Facturado (Gs.)', facturado])
    ws1.append(['Cantidad de Tickets', tickets])
    ws1.append(['Ticket Promedio (Gs.)', promedio])

    ventas_metodo = qs_base.values('metodo_pago').annotate(total=Sum('total_pedido')).order_by('-total')
    ws1.append([])
    ws1.append(['Método de Pago', 'Total (Gs.)'])
    for v in ventas_metodo:
        ws1.append([v['metodo_pago'] or '—', int(v['total'] or 0)])

    _ajustar_columnas(ws1)

    # ── Hoja 2: Top productos ────────────────────────────────
    ws2 = wb.create_sheet('Top Productos')
    _estilo_encabezado(ws2, 1, ['Producto', 'Categoría', 'Unidades Vendidas', 'Revenue (Gs.)'])
    top = (PedidoDetalle.objects
           .filter(pedido__in=qs_base)
           .values('producto__nombre', 'producto__categoria__nombre')
           .annotate(unidades=Sum('cantidad'), revenue=Sum(F('cantidad') * F('precio_historico')))
           .order_by('-revenue')[:20])
    for p in top:
        ws2.append([p['producto__nombre'], p['producto__categoria__nombre'], p['unidades'], int(p['revenue'] or 0)])
    _ajustar_columnas(ws2)

    # ── Hoja 3: Ventas por mozo ──────────────────────────────
    ws3 = wb.create_sheet('Ventas por Mozo')
    _estilo_encabezado(ws3, 1, ['Mozo', 'Tickets', 'Total Vendido (Gs.)'])
    mozos = (qs_base.values('mozo__username', 'mozo__first_name', 'mozo__last_name')
             .annotate(tickets=Count('id'), total=Sum('total_pedido'))
             .order_by('-total'))
    for m in mozos:
        nombre = f"{m['mozo__first_name']} {m['mozo__last_name']}".strip() or m['mozo__username']
        ws3.append([nombre, m['tickets'], int(m['total'] or 0)])
    _ajustar_columnas(ws3)

    # ── Hoja 4: Rotación de mesas ────────────────────────────
    ws4 = wb.create_sheet('Rotación de Mesas')
    _estilo_encabezado(ws4, 1, ['Mesa', 'Pedidos', 'Total Facturado (Gs.)'])
    mesas = (qs_base.values('mesa__numero_mesa')
             .annotate(pedidos=Count('id'), total=Sum('total_pedido'))
             .order_by('mesa__numero_mesa'))
    for m in mesas:
        ws4.append([m['mesa__numero_mesa'], m['pedidos'], int(m['total'] or 0)])
    _ajustar_columnas(ws4)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    nombre = f"dashboard_{date.today().isoformat()}.xlsx"
    resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return resp


@login_required
@requiere_rol('Administrador')
def configuracion(request):
    """
    Gestión de la configuración global del restaurante (singleton).

    Roles: Administrador (solo)
    Método: GET (formulario con datos actuales) | POST (guardar)
    Retorna GET: render configuracion.html con el objeto config (id=1)
    Retorna POST: guarda cambios y redirect a configuracion (PRG pattern)
    Campos editables: nombre del restaurante, RUC, dirección, teléfono, tasa_iva (5 o 10%).
    Usa ConfiguracionRestaurante.objects.get_or_create(id=1) — garantiza singleton.
    Los datos de config se usan en imprimir_factura para el encabezado del ticket.
    """
    from .models import ConfiguracionRestaurante
    config = ConfiguracionRestaurante.objects.get_or_create(id=1)[0]

    if request.method == 'POST':
        config.nombre    = request.POST.get('nombre', config.nombre).strip()
        config.ruc       = request.POST.get('ruc', config.ruc).strip()
        config.direccion = request.POST.get('direccion', config.direccion).strip()
        config.telefono  = request.POST.get('telefono', config.telefono).strip()
        try:
            tasa = int(request.POST.get('tasa_iva', config.tasa_iva))
            if tasa in (5, 10):
                config.tasa_iva = tasa
        except (ValueError, TypeError):
            pass
        config.save()
        messages.success(request, 'Configuración guardada correctamente.')
        return redirect('configuracion')

    return render(request, 'pedidos/configuracion.html', {'config': config})