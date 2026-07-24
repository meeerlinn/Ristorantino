from django.db.models import Max
from django.utils import timezone


def alertas_timbrado(request):
    """
    Context processor: inyecta alertas de timbrado en todos los templates.

    Solo se ejecuta para usuarios Cajero/Administrador/superusuario autenticados.
    Devuelve 'alertas_timbrado': lista de dicts con nivel, titulo, mensaje.

    Niveles:
      'danger'  — timbrado vencido, vence en ≤7 días, o numeración agotada
      'warning' — vence en 8–30 días, o quedan ≤50 números
    """
    if not request.user.is_authenticated:
        return {}

    es_cajero = request.user.is_superuser or (
        hasattr(request.user, 'empleado') and
        request.user.empleado.rol.nombre in ('Cajero', 'Administrador')
    )
    if not es_cajero:
        return {}

    from .models import CajaTimbrado, DocumentoTributario

    hoy = timezone.now().date()
    alertas = []

    caja_timbrados = (
        CajaTimbrado.objects
        .filter(estado='Activo')
        .select_related('timbrado', 'caja')
    )

    for ct in caja_timbrados:
        t    = ct.timbrado
        dias = (t.fecha_vencimiento - hoy).days

        # ── Alerta de vencimiento ─────────────────────────────
        if dias < 0:
            alertas.append({
                'nivel':   'danger',
                'icono':   '🔴',
                'titulo':  f'Timbrado {t.numero_timbrado} VENCIDO',
                'mensaje': (
                    f'{ct.caja.nombre} — Venció hace {abs(dias)} día{"s" if abs(dias) != 1 else ""}. '
                    f'No se pueden emitir facturas hasta renovarlo.'
                ),
            })
        elif dias <= 7:
            alertas.append({
                'nivel':   'danger',
                'icono':   '🔴',
                'titulo':  f'Timbrado vence en {dias} día{"s" if dias != 1 else ""}',
                'mensaje': (
                    f'{ct.caja.nombre} — Timbrado {t.numero_timbrado} vence el '
                    f'{t.fecha_vencimiento.strftime("%d/%m/%Y")}. Renovar urgente.'
                ),
            })
        elif dias <= 30:
            alertas.append({
                'nivel':   'warning',
                'icono':   '🟡',
                'titulo':  f'Timbrado vence en {dias} días',
                'mensaje': (
                    f'{ct.caja.nombre} — Timbrado {t.numero_timbrado} vence el '
                    f'{t.fecha_vencimiento.strftime("%d/%m/%Y")}.'
                ),
            })

        # ── Alerta de numeración ──────────────────────────────
        ultimo_num = (
            DocumentoTributario.objects
            .filter(timbrado=t)
            .aggregate(max_num=Max('numero_secuencial'))['max_num']
        )
        if ultimo_num is not None:
            restantes = t.rango_hasta - ultimo_num
            if restantes <= 0:
                alertas.append({
                    'nivel':   'danger',
                    'icono':   '🔴',
                    'titulo':  'Numeración de factura agotada',
                    'mensaje': (
                        f'{ct.caja.nombre} — Se agotó el rango del timbrado '
                        f'{t.numero_timbrado} (hasta {t.rango_hasta:,}).'
                    ),
                })
            elif restantes <= 50:
                alertas.append({
                    'nivel':   'warning',
                    'icono':   '🟡',
                    'titulo':  f'Quedan {restantes} números de factura',
                    'mensaje': (
                        f'{ct.caja.nombre} — Timbrado {t.numero_timbrado}: '
                        f'rango hasta {t.rango_hasta:,}.'
                    ),
                })

    return {'alertas_timbrado': alertas}
