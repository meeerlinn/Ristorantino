"""
Genera los 4 diagramas del Capítulo 6 de la tesis Ristorantino.
Estilo consistente con el diagrama de red LAN existente:
- Fondo blanco, bordes grises suaves
- Cajas redondeadas con colores por categoría
- Tipografía DejaVu Sans (disponible en matplotlib)
- Sin encimamiento de líneas
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

OUT = r"C:\Proyecto\docs"

# ── Paleta ────────────────────────────────────────────────────────────────────
BLUE    = "#2563EB"   # cliente / mozo
ORANGE  = "#D97706"  # cocina / chef
GREEN   = "#059669"  # servidor / backend
PURPLE  = "#7C3AED"  # cajero / caja
GRAY    = "#6B7280"  # neutral / bd
TEAL    = "#0891B2"  # procesos / flujo
LBLUE   = "#DBEAFE"  # fill cliente
LORANGE = "#FEF3C7"  # fill cocina
LGREEN  = "#D1FAE5"  # fill servidor
LPURPLE = "#EDE9FE"  # fill cajero
LGRAY   = "#F3F4F6"  # fill neutral
LTEAL   = "#CFFAFE"  # fill procesos
WHITE   = "#FFFFFF"
DARK    = "#1F2937"

def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=180, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"Guardado: {path}")

def rounded_box(ax, x, y, w, h, text, sub=None,
                fc=LGRAY, ec=GRAY, lw=1.5, fontsize=10, bold=True,
                radius=0.04):
    """Dibuja una caja redondeada con título y subtítulo opcional."""
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle=f"round,pad=0.01,rounding_size={radius}",
                         facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3)
    ax.add_patch(box)
    if sub:
        ax.text(x, y + h*0.12, text, ha='center', va='center',
                fontsize=fontsize, fontweight='bold' if bold else 'normal',
                color=DARK, zorder=4, wrap=True)
        ax.text(x, y - h*0.22, sub, ha='center', va='center',
                fontsize=fontsize - 1.5, color=GRAY, zorder=4)
    else:
        ax.text(x, y, text, ha='center', va='center',
                fontsize=fontsize, fontweight='bold' if bold else 'normal',
                color=DARK, zorder=4)

def arrow(ax, x1, y1, x2, y2, color=GRAY, lw=1.5, style='->', dashed=False):
    """Flecha recta entre dos puntos."""
    ls = '--' if dashed else '-'
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=lw, linestyle=ls),
                zorder=2)

def line(ax, x1, y1, x2, y2, color=GRAY, lw=1.5, dashed=False):
    ls = '--' if dashed else '-'
    ax.plot([x1, x2], [y1, y2], color=color, lw=lw, ls=ls, zorder=2)

def label_mid(ax, x1, y1, x2, y2, text, fontsize=8, offset=(0, 0.04)):
    mx, my = (x1+x2)/2 + offset[0], (y1+y2)/2 + offset[1]
    ax.text(mx, my, text, ha='center', va='center',
            fontsize=fontsize, color=GRAY,
            bbox=dict(fc='white', ec='none', pad=1))

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAMA 6.1 — ARQUITECTURA DEL SISTEMA
# ══════════════════════════════════════════════════════════════════════════════
def diagrama_arquitectura():
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    ax.text(6.5, 7.6, "Arquitectura del Sistema — Ristorantino",
            ha='center', va='center', fontsize=14, fontweight='bold', color=DARK)

    # ── Capa 1: Clientes (izquierda)
    ax.text(1.7, 7.1, "Capa de Presentación", ha='center', va='center',
            fontsize=9, color=BLUE, fontweight='bold')
    for i, (lbl, sub, y) in enumerate([
        ("Tablet\nMozo",   "Comanda digital",    5.8),
        ("Monitor\nChef",  "Monitor de cocina",  4.3),
        ("PC\nCajero",     "Caja / Facturación", 2.8),
        ("PC\nAdmin",      "Panel Django",       1.3),
    ]):
        colors = [(LBLUE, BLUE), (LORANGE, ORANGE),
                  (LPURPLE, PURPLE), (LGRAY, GRAY)]
        fc, ec = colors[i]
        rounded_box(ax, 1.7, y, 2.0, 0.9, lbl, sub,
                    fc=fc, ec=ec, fontsize=9)

    # ── Capa 2: Django MVT (centro)
    ax.text(6.5, 7.1, "Capa de Lógica (Django MVT)", ha='center', va='center',
            fontsize=9, color=GREEN, fontweight='bold')

    # Router / URLs
    rounded_box(ax, 6.5, 5.8, 2.4, 0.7, "urls.py", "Enrutamiento de peticiones",
                fc=LGREEN, ec=GREEN, fontsize=9)

    # Views
    rounded_box(ax, 5.1, 4.3, 2.2, 0.7, "views.py", "Lógica de negocio",
                fc=LGREEN, ec=GREEN, fontsize=9)

    # Templates
    rounded_box(ax, 7.9, 4.3, 2.2, 0.7, "templates/", "HTML + Bootstrap 5.3",
                fc=LGREEN, ec=GREEN, fontsize=9)

    # Models
    rounded_box(ax, 6.5, 2.9, 2.4, 0.7, "models.py", "ORM — Modelos de datos",
                fc=LGREEN, ec=GREEN, fontsize=9)

    # Static
    rounded_box(ax, 6.5, 1.8, 2.2, 0.7, "static/", "CSS / JS / Imágenes",
                fc=LGRAY, ec=GRAY, fontsize=9)

    # ── Capa 3: Base de datos (derecha)
    ax.text(11.3, 7.1, "Capa de Datos", ha='center', va='center',
            fontsize=9, color=GRAY, fontweight='bold')
    rounded_box(ax, 11.3, 4.3, 2.2, 2.4,
                "PostgreSQL", "127.0.0.1:5432\ndb: ristorantino",
                fc=LGRAY, ec=GRAY, fontsize=9)

        # ── Bus HTTP central: línea vertical en x=3.3, con ramas a cada cliente
    # y una flecha principal al urls.py — evita el encimamiento
    BUS_X = 3.3
    CLIENT_YS = [5.8, 4.3, 2.8, 1.3]
    # Línea bus vertical
    line(ax, BUS_X, 5.8, BUS_X, 1.3, color=BLUE, lw=1.5)
    # Ramales desde bus a cada cliente (flechas entrantes y salientes)
    for y in CLIENT_YS:
        line(ax, 2.7, y, BUS_X, y, color=BLUE, lw=1.2)
    # Flecha del bus al urls.py (una sola, limpia)
    arrow(ax, BUS_X, 5.8, 5.2, 5.8, color=BLUE, lw=1.8)
    label_mid(ax, BUS_X+0.1, 5.8, 4.8, 5.8, "HTTP GET/POST", fontsize=7.5, offset=(0, 0.18))
    # Respuesta del urls.py al bus (dashed)
    arrow(ax, 5.2, 5.5, BUS_X, 5.5, color=BLUE, lw=1.0, dashed=True)
    # Ramales de respuesta bus → clientes (dashed)
    for y in CLIENT_YS:
        line(ax, BUS_X, y, 2.7, y, color="#93C5FD", lw=0.9)

    # urls → views
    arrow(ax, 5.3, 5.6, 5.1, 4.65, color=GREEN, lw=1.5)
    # urls → templates
    arrow(ax, 7.7, 5.6, 7.9, 4.65, color=GREEN, lw=1.5)
    # views ↔ templates (render)
    arrow(ax, 6.2, 4.3, 7.0, 4.3, color=GREEN, lw=1.3)
    arrow(ax, 7.0, 4.1, 6.2, 4.1, color=GREEN, lw=1.0, dashed=True)

    # views ↔ models
    arrow(ax, 5.1, 3.95, 5.6, 3.25, color=GREEN, lw=1.5)
    arrow(ax, 5.8, 3.25, 5.3, 3.95, color=GREEN, lw=1.0, dashed=True)

    # models ↔ PostgreSQL
    arrow(ax, 7.7, 2.9, 10.2, 4.0, color=GRAY, lw=1.8)
    arrow(ax, 10.2, 3.8, 7.7, 2.7, color=GRAY, lw=1.3, dashed=True)
    label_mid(ax, 7.7, 2.9, 10.2, 4.0, "ORM / SQL", fontsize=8, offset=(0.1, 0.15))

    # ── Leyenda
    patches = [
        mpatches.Patch(fc=LBLUE,   ec=BLUE,   label='Dispositivos cliente'),
        mpatches.Patch(fc=LGREEN,  ec=GREEN,  label='Lógica Django (MVT)'),
        mpatches.Patch(fc=LGRAY,   ec=GRAY,   label='Base de datos / Estáticos'),
        mpatches.Patch(fc=WHITE,   ec=BLUE,   label='─── Petición HTTP'),
        mpatches.Patch(fc=WHITE,   ec=GREEN,  label='─── Respuesta / Render'),
    ]
    ax.legend(handles=patches, loc='lower left', fontsize=8,
              framealpha=0.9, edgecolor='#E5E7EB',
              ncol=5, bbox_to_anchor=(0, -0.04))

    save(fig, "diagrama_6_1_arquitectura.png")


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAMA 6.2 — ENTIDAD-RELACIÓN
# ══════════════════════════════════════════════════════════════════════════════
def diagrama_er():
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 10)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    ax.text(7.5, 9.65, "Diagrama Entidad-Relación — Ristorantino",
            ha='center', va='center', fontsize=14, fontweight='bold', color=DARK)

    # Helper: entity box (header + fields list)
    def entity(ax, x, y, w, h, name, fields, fc, ec):
        # Header
        header = FancyBboxPatch((x, y + h - 0.45), w, 0.45,
                                boxstyle="round,pad=0.005,rounding_size=0.03",
                                facecolor=ec, edgecolor=ec, linewidth=0, zorder=3)
        ax.add_patch(header)
        # Body
        body = FancyBboxPatch((x, y), w, h - 0.45,
                              boxstyle="round,pad=0.005,rounding_size=0.03",
                              facecolor=fc, edgecolor=ec, linewidth=1.5, zorder=3)
        ax.add_patch(body)
        # Outline on top
        outline = FancyBboxPatch((x, y), w, h,
                                 boxstyle="round,pad=0.005,rounding_size=0.03",
                                 facecolor='none', edgecolor=ec, linewidth=1.5, zorder=4)
        ax.add_patch(outline)
        ax.text(x + w/2, y + h - 0.22, name, ha='center', va='center',
                fontsize=9, fontweight='bold', color='white', zorder=5)
        for i, f in enumerate(fields):
            italic = f.startswith('PK') or f.startswith('FK')
            color = ec if f.startswith('PK') else (ORANGE if f.startswith('FK') else '#374151')
            ax.text(x + 0.12, y + h - 0.65 - i * 0.30, f,
                    ha='left', va='center', fontsize=7.5,
                    color=color, style='italic' if italic else 'normal', zorder=5)

    # ── Entidades por grupo

    # PERSONAL
    entity(ax, 0.2, 7.2, 2.2, 1.6, "Rol",
           ["PK id", "nombre (mozo/chef/cajero)"], LGRAY, GRAY)
    entity(ax, 0.2, 4.8, 2.2, 2.1, "Empleado",
           ["PK id", "FK user_id → User", "FK rol_id → Rol"], LGRAY, GRAY)

    # SALON
    entity(ax, 3.0, 7.5, 2.2, 1.3, "Sector",
           ["PK id", "nombre"], LBLUE, BLUE)
    entity(ax, 3.0, 5.2, 2.2, 2.0, "Mesa",
           ["PK id", "FK sector_id", "numero_mesa", "estado"], LBLUE, BLUE)

    # MENU
    entity(ax, 6.0, 7.5, 2.4, 1.3, "Categoria",
           ["PK id", "nombre"], LGREEN, GREEN)
    entity(ax, 6.0, 4.6, 2.4, 2.6, "Producto",
           ["PK id", "FK categoria_id", "nombre", "precio_venta",
            "costo_insumo", "tasa_iva", "activo"], LGREEN, GREEN)

    # PEDIDOS
    entity(ax, 9.1, 7.5, 2.4, 1.3, "Cliente",
           ["PK id", "ruc_ci", "nombre_razon_social"], LTEAL, TEAL)
    entity(ax, 9.1, 4.2, 2.4, 3.0, "Pedido",
           ["PK id", "FK mesa_id", "FK cliente_id", "FK mozo_id → User",
            "estado_pago", "total_pedido", "fecha_apertura"], LTEAL, TEAL)
    entity(ax, 9.1, 1.5, 2.4, 2.4, "PedidoDetalle",
           ["PK id", "FK pedido_id", "FK producto_id",
            "cantidad", "precio_historico"], LTEAL, TEAL)

    # COCINA
    entity(ax, 12.3, 4.2, 2.4, 2.7, "FlujoEstado",
           ["PK id", "FK detalle_id → PedidoDetalle",
            "estado (Pendiente/Cocina/Listo)",
            "timestamp_creacion", "timestamp_cambio"], LORANGE, ORANGE)

    # CONTABILIDAD
    entity(ax, 0.2, 1.5, 2.2, 3.0, "DocumentoTributario",
           ["PK id", "FK timbrado_id", "FK cliente_id",
            "FK arqueo_id", "nro_factura", "monto_total",
            "metodo_pago"], LPURPLE, PURPLE)
    entity(ax, 3.0, 1.5, 2.4, 3.0, "Arqueo",
           ["PK id", "FK caja_id", "FK usuario_id",
            "monto_apertura", "monto_cierre_real",
            "diferencia_arqueo", "estado"], LPURPLE, PURPLE)
    entity(ax, 6.0, 1.5, 2.2, 2.2, "Timbrado",
           ["PK id", "numero", "serie",
            "fecha_vencimiento", "rango_desde", "activo"], LPURPLE, PURPLE)

    # PedidoDocumento (bridge) — entre Pedido y DocumentoTributario
    entity(ax, 6.0, 3.1, 2.2, 1.6, "PedidoDocumento",
           ["PK id", "FK pedido_id → Pedido",
            "FK documento_id → DocTrib."], LPURPLE, PURPLE)

    # ── Relaciones (líneas)
    # Rol — Empleado
    line(ax, 1.3, 6.1, 1.3, 6.85, color=GRAY)
    ax.text(1.35, 6.45, "1:N", fontsize=7, color=GRAY)

    # Sector — Mesa
    line(ax, 4.1, 6.45, 4.1, 7.5, color=BLUE)
    ax.text(4.15, 7.0, "1:N", fontsize=7, color=BLUE)

    # Categoria — Producto
    line(ax, 7.2, 6.3, 7.2, 7.5, color=GREEN)
    ax.text(7.25, 7.0, "1:N", fontsize=7, color=GREEN)

    # Mesa — Pedido
    line(ax, 4.2, 5.8, 9.1, 5.8, color=TEAL)
    line(ax, 9.1, 5.8, 9.1, 7.2, color=TEAL)
    ax.text(6.5, 5.9, "1:N", fontsize=7, color=TEAL)

    # Cliente — Pedido
    line(ax, 10.3, 4.2, 10.3, 7.5, color=TEAL)
    ax.text(10.35, 6.0, "1:N", fontsize=7, color=TEAL)

    # Producto — PedidoDetalle
    line(ax, 7.2, 4.6, 7.2, 3.3)
    line(ax, 7.2, 3.3, 9.1, 3.3, color=GREEN)
    line(ax, 9.1, 3.3, 9.1, 3.9, color=GREEN)
    ax.text(8.1, 3.4, "N:1", fontsize=7, color=GREEN)

    # Pedido — PedidoDetalle
    line(ax, 10.3, 4.2, 10.3, 3.9, color=TEAL)
    ax.text(10.35, 4.05, "1:N", fontsize=7, color=TEAL)

    # PedidoDetalle — FlujoEstado
    line(ax, 11.5, 2.4, 12.3, 4.4, color=ORANGE)
    ax.text(11.9, 3.3, "1:N", fontsize=7, color=ORANGE)

    # Arqueo — DocumentoTributario
    line(ax, 2.4, 2.6, 3.0, 2.6, color=PURPLE)
    ax.text(2.65, 2.7, "1:N", fontsize=7, color=PURPLE)

    # Timbrado — DocumentoTributario
    line(ax, 2.4, 2.2, 6.0, 2.2, color=PURPLE)
    ax.text(4.2, 2.35, "N:1", fontsize=7, color=PURPLE)

    # Pedido — PedidoDocumento
    line(ax, 10.3, 4.2, 10.3, 3.1, color=PURPLE, lw=1.2)
    line(ax, 10.3, 3.1, 8.2, 3.3, color=PURPLE, lw=1.2)
    ax.text(9.4, 3.5, "1:1", fontsize=7, color=PURPLE)

    # PedidoDocumento — DocumentoTributario
    line(ax, 6.0, 2.5, 2.4, 2.4, color=PURPLE, lw=1.2)
    ax.text(4.2, 2.6, "N:1", fontsize=7, color=PURPLE)

    # ── Leyenda por grupos
    patches = [
        mpatches.Patch(fc=LGRAY,   ec=GRAY,   label='Personal / Acceso'),
        mpatches.Patch(fc=LBLUE,   ec=BLUE,   label='Salón / Mesas'),
        mpatches.Patch(fc=LGREEN,  ec=GREEN,  label='Menú / Productos'),
        mpatches.Patch(fc=LTEAL,   ec=TEAL,   label='Pedidos'),
        mpatches.Patch(fc=LORANGE, ec=ORANGE, label='Cocina'),
        mpatches.Patch(fc=LPURPLE, ec=PURPLE, label='Contabilidad / Fiscal'),
    ]
    ax.legend(handles=patches, loc='lower center', fontsize=8,
              framealpha=0.9, edgecolor='#E5E7EB',
              ncol=6, bbox_to_anchor=(0.5, -0.04))

    save(fig, "diagrama_6_2_entidad_relacion.png")


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAMA 6.3 — FLUJO DE PROCESOS
# Tres subdiagramas: (A) Toma de pedido, (B) Flujo cocina, (C) Cobro
# ══════════════════════════════════════════════════════════════════════════════
def diagrama_flujo():
    fig, axes = plt.subplots(1, 3, figsize=(18, 10))
    fig.patch.set_facecolor('white')
    fig.suptitle("Diagramas de Flujo de Procesos — Ristorantino",
                 fontsize=14, fontweight='bold', color=DARK, y=0.97)

    titles = [
        ("A — Toma de Pedido\n(Mozo)", BLUE),
        ("B — Flujo de Cocina\n(Chef)", ORANGE),
        ("C — Cobro y Facturación\n(Cajero)", PURPLE),
    ]

    for ax, (title, color) in zip(axes, titles):
        ax.set_xlim(-1, 11)
        ax.set_ylim(-1, 12)
        ax.axis('off')
        ax.set_facecolor('white')
        ax.text(5, 11.5, title, ha='center', va='center',
                fontsize=11, fontweight='bold', color=color)

    def flow_box(ax, x, y, text, style='rect', fc=None, ec=None, w=7, h=0.85):
        """Rectángulo o rombo para pasos del flujo."""
        if fc is None: fc = LGRAY
        if ec is None: ec = GRAY
        if style == 'oval':  # Inicio/Fin
            ellipse = mpatches.Ellipse((x, y), w*0.9, h*1.1,
                                       facecolor=ec, edgecolor=ec, zorder=3)
            ax.add_patch(ellipse)
            ax.text(x, y, text, ha='center', va='center',
                    fontsize=8.5, fontweight='bold', color='white', zorder=4)
        elif style == 'diamond':  # Decisión
            dx, dy = w*0.45, h*0.7
            diamond = plt.Polygon([[x, y+dy], [x+dx, y], [x, y-dy], [x-dx, y]],
                                  facecolor=fc, edgecolor=ec, linewidth=1.5, zorder=3)
            ax.add_patch(diamond)
            ax.text(x, y, text, ha='center', va='center',
                    fontsize=7.5, color=DARK, zorder=4, wrap=True)
        else:  # Proceso
            box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                                 boxstyle="round,pad=0.01,rounding_size=0.15",
                                 facecolor=fc, edgecolor=ec, linewidth=1.5, zorder=3)
            ax.add_patch(box)
            ax.text(x, y, text, ha='center', va='center',
                    fontsize=8, color=DARK, zorder=4)

    def farrow(ax, x1, y1, x2, y2, color=GRAY, label=None, lside='right'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5), zorder=2)
        if label:
            mx = (x1+x2)/2 + (0.5 if lside == 'right' else -0.5)
            my = (y1+y2)/2
            ax.text(mx, my, label, ha='center', va='center',
                    fontsize=7.5, color=color,
                    bbox=dict(fc='white', ec='none', pad=1))

    # ── FLUJO A: Toma de pedido ────────────────────────────────────────────
    ax = axes[0]
    steps_a = [
        (5, 10.8,  "INICIO",                         'oval',    BLUE,    BLUE),
        (5, 9.7,   "Mozo ingresa al salón",           'rect',    LBLUE,   BLUE),
        (5, 8.7,   "Selecciona mesa LIBRE",           'rect',    LBLUE,   BLUE),
        (5, 7.6,   "¿Mesa disponible?",               'diamond', LORANGE, ORANGE),
        (5, 6.5,   "Abre la mesa\n(crea Pedido)",     'rect',    LBLUE,   BLUE),
        (5, 5.4,   "Agrega productos\n(comanda)",     'rect',    LBLUE,   BLUE),
        (5, 4.3,   "¿Agrega observación\nal ítem?",  'diamond', LORANGE, ORANGE),
        (5, 3.2,   "Guarda nota en\nPedidoDetalle",  'rect',    LGREEN,  GREEN),
        (5, 2.1,   "Confirma pedido\ny vuelve al salón", 'rect', LBLUE,  BLUE),
        (5, 1.0,   "FIN",                             'oval',    BLUE,    BLUE),
    ]
    for x, y, text, style, fc, ec in steps_a:
        flow_box(ax, x, y, text, style=style, fc=fc, ec=ec)

    # Flechas verticales principales
    ys_a = [10.5, 10.1, 9.25, 8.25, 7.2, 6.95, 6.02, 5.02, 3.75, 3.62, 2.52, 1.42]
    pairs_a = [(10.5,10.1),(10.1,9.25),(9.25,8.25),(8.25+0.3,7.55),(7.2,6.95),
               (6.95,6.05),(6.05,5.05),(5.05,4.62),(4.62,3.75),(3.35,2.52),(2.52,1.42)]
    for y1, y2 in pairs_a:
        farrow(ax, 5, y1, 5, y2, color=BLUE)

    # No en ¿Mesa disponible? → vuelve a elegir
    farrow(ax, 7.5, 7.6, 7.5, 9.7, color=ORANGE)
    ax.text(8.5, 8.65, "No\n(elige otra)", ha='center', va='center',
            fontsize=7.5, color=ORANGE)
    line(ax, 5+3.5*0.45, 7.6, 7.5, 7.6, color=ORANGE)

    # Sí en ¿Mesa disponible?
    ax.text(3.8, 7.1, "Sí", ha='center', fontsize=7.5, color=BLUE)

    # No en ¿Observación?
    ax.text(3.5, 3.85, "No", ha='center', fontsize=7.5, color=ORANGE)
    farrow(ax, 5 - 3.5*0.45, 4.3, 2.5, 4.3, color=ORANGE, label='')
    farrow(ax, 2.5, 4.3, 2.5, 2.1, color=ORANGE)
    farrow(ax, 2.5, 2.1, 5 - 3.5, 2.1, color=ORANGE)

    # Sí en ¿Observación?
    ax.text(6.2, 3.85, "Sí", ha='center', fontsize=7.5, color=GREEN)

    # ── FLUJO B: Cocina ──────────────────────────────────────────────────────
    ax = axes[1]
    steps_b = [
        (5, 10.8, "INICIO",                         'oval',    ORANGE, ORANGE),
        (5, 9.7,  "Chef abre monitor\nde cocina",   'rect',    LORANGE, ORANGE),
        (5, 8.6,  "¿Hay ítems\nPENDIENTES?",       'diamond', LORANGE, ORANGE),
        (5, 7.5,  "Lee ítem: mesa, producto,\ncantidad, observación", 'rect', LORANGE, ORANGE),
        (5, 6.4,  "Clic 'Empezar'\n→ Estado: EN COCINA", 'rect', LGREEN, GREEN),
        (5, 5.3,  "Prepara el plato\n(observaciones aplicadas)", 'rect', LORANGE, ORANGE),
        (5, 4.2,  "¿Plato listo?",                 'diamond', LORANGE, ORANGE),
        (5, 3.1,  "Clic 'Listo'\n→ Estado: LISTO", 'rect',    LGREEN, GREEN),
        (5, 2.0,  "Ítem sale del monitor\n→ Mozo lleva el plato", 'rect', LGRAY, GRAY),
        (5, 0.9,  "¿Más ítems\npendientes?",        'diamond', LORANGE, ORANGE),
    ]
    for x, y, text, style, fc, ec in steps_b:
        flow_box(ax, x, y, text, style=style, fc=fc, ec=ec)

    pairs_b = [(10.5,10.1),(10.1,9.25),(9.25,8.9),(8.3,8.08),
               (7.98,6.98),(6.98,5.9),(5.9,4.78),(4.65,3.65),
               (3.65,2.52),(2.52,1.35)]
    for y1, y2 in pairs_b:
        farrow(ax, 5, y1, 5, y2, color=ORANGE)

    # No en ¿Hay ítems?
    farrow(ax, 7.5, 8.6, 7.5, 9.7, color=GRAY)
    line(ax, 5+3.5*0.45, 8.6, 7.5, 8.6, color=GRAY)
    ax.text(8.7, 9.1, "No\n(espera)", ha='center', fontsize=7.5, color=GRAY)
    ax.text(3.8, 8.2, "Sí", ha='center', fontsize=7.5, color=ORANGE)

    # No en ¿Plato listo? (sigue cocinando)
    ax.text(3.5, 3.7, "Sí", ha='center', fontsize=7.5, color=GREEN)
    ax.text(7.2, 3.7, "No", ha='center', fontsize=7.5, color=ORANGE)
    farrow(ax, 5+3.5*0.45, 4.2, 8.0, 4.2, color=ORANGE)
    farrow(ax, 8.0, 4.2, 8.0, 5.3, color=ORANGE)
    farrow(ax, 8.0, 5.3, 5+3.5, 5.3, color=ORANGE)

    # ¿Más ítems? → Sí vuelve al inicio
    farrow(ax, 5+3.5*0.45, 0.9, 9.5, 0.9, color=ORANGE)
    farrow(ax, 9.5, 0.9, 9.5, 9.7, color=ORANGE)
    farrow(ax, 9.5, 9.7, 5+3.5, 9.7, color=ORANGE)
    ax.text(9.9, 5.0, "Sí", ha='center', fontsize=7.5, color=ORANGE, rotation=90)

    # No en ¿Más ítems? → Fin (abajo, fuera)
    ax.text(3.5, 0.5, "No", ha='center', fontsize=7.5, color=GRAY)
    farrow(ax, 5-3.5*0.45, 0.9, 1.5, 0.9, color=GRAY)
    ax.text(1.0, 0.5, "FIN", ha='center', va='center', fontsize=8.5,
            fontweight='bold', color='white',
            bbox=dict(boxstyle='round,pad=0.3', fc=ORANGE, ec=ORANGE))

    # ── FLUJO C: Cobro ──────────────────────────────────────────────────────
    ax = axes[2]
    steps_c = [
        (5, 10.8, "INICIO",                             'oval',    PURPLE, PURPLE),
        (5, 9.7,  "Cajero abre la caja\n(Arqueo activo)", 'rect', LPURPLE, PURPLE),
        (5, 8.6,  "¿Caja abierta?",                    'diamond', LPURPLE, PURPLE),
        (5, 7.5,  "Selecciona pedido\na cobrar",        'rect',    LPURPLE, PURPLE),
        (5, 6.4,  "Verifica ítems\ny total del pedido", 'rect',    LPURPLE, PURPLE),
        (5, 5.3,  "Busca / identifica\ncliente",        'rect',    LPURPLE, PURPLE),
        (5, 4.2,  "Ingresa descuento\ny método de pago",'rect',    LPURPLE, PURPLE),
        (5, 3.1,  "Confirma cobro\n→ Genera DocumentoTributario", 'rect', LGREEN, GREEN),
        (5, 2.0,  "Actualiza Arqueo\n+ Mesa → SUCIA",  'rect',    LGREEN,  GREEN),
        (5, 0.9,  "Imprime / guarda\nfactura",          'rect',    LGRAY,   GRAY),
    ]
    for x, y, text, style, fc, ec in steps_c:
        flow_box(ax, x, y, text, style=style, fc=fc, ec=ec)

    pairs_c = [(10.5,10.1),(10.1,9.25),(9.25,8.9),(8.3,8.08),
               (7.98,6.98),(6.98,5.9),(5.9,4.78),(4.65,3.65),
               (3.65,2.52),(2.52,1.35)]
    for y1, y2 in pairs_c:
        farrow(ax, 5, y1, 5, y2, color=PURPLE)

    # No en ¿Caja abierta? → Ir a abrir caja
    farrow(ax, 5+3.5*0.45, 8.6, 8.5, 8.6, color=GRAY)
    farrow(ax, 8.5, 8.6, 8.5, 9.7, color=GRAY)
    farrow(ax, 8.5, 9.7, 5+3.5, 9.7, color=GRAY)
    ax.text(9.3, 9.2, "No → Abrir\ncaja primero", ha='center', fontsize=7, color=GRAY)

    # FIN abajo
    farrow(ax, 5, 0.52, 5, 0.1, color=PURPLE)
    ax.text(5, -0.25, "FIN", ha='center', va='center', fontsize=8.5,
            fontweight='bold', color='white',
            bbox=dict(boxstyle='round,pad=0.3', fc=PURPLE, ec=PURPLE))

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    save(fig, "diagrama_6_3_flujo_procesos.png")


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAMA 6.4 — CASOS DE USO
# ══════════════════════════════════════════════════════════════════════════════
def diagrama_casos_uso():
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 10)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    ax.text(7.5, 9.65, "Diagrama de Casos de Uso — Ristorantino",
            ha='center', va='center', fontsize=14, fontweight='bold', color=DARK)

    # Sistema boundary
    sys_box = FancyBboxPatch((2.2, 0.3), 10.6, 9.0,
                              boxstyle="round,pad=0.05,rounding_size=0.1",
                              facecolor='#F9FAFB', edgecolor='#9CA3AF',
                              linewidth=2, linestyle='--', zorder=1)
    ax.add_patch(sys_box)
    ax.text(7.5, 9.15, "«Sistema» Ristorantino", ha='center', va='center',
            fontsize=10, color='#6B7280', style='italic')

    # ── Actor helper
    def actor(ax, x, y, name, color, icon='●'):
        # Figura palito simplificada con círculo
        ax.plot(x, y + 0.6, 'o', markersize=14, color=color, zorder=5)
        ax.plot([x, x], [y + 0.2, y - 0.3], color=color, lw=2, zorder=5)
        ax.plot([x - 0.35, x + 0.35], [y + 0.0, y + 0.0], color=color, lw=2, zorder=5)
        ax.plot([x, x - 0.3], [y - 0.3, y - 0.75], color=color, lw=2, zorder=5)
        ax.plot([x, x + 0.3], [y - 0.3, y - 0.75], color=color, lw=2, zorder=5)
        ax.text(x, y - 1.0, name, ha='center', va='top',
                fontsize=9, fontweight='bold', color=color)

    # ── Caso de uso helper
    def use_case(ax, x, y, text, color, w=2.6, h=0.5):
        ell = mpatches.Ellipse((x, y), w, h,
                                facecolor='white', edgecolor=color,
                                linewidth=1.8, zorder=3)
        ax.add_patch(ell)
        ax.text(x, y, text, ha='center', va='center',
                fontsize=7.5, color=DARK, zorder=4)

    # ── Actores (fuera del sistema boundary)
    actor(ax, 0.9, 7.5, "Mozo",  BLUE)
    actor(ax, 0.9, 4.2, "Chef",  ORANGE)
    actor(ax, 0.9, 1.4, "Cajero", PURPLE)
    actor(ax, 14.1, 5.0, "Administrador", GRAY)

    # ── Casos de uso — MOZO (columna izq, y 1.9..8.2)
    mozo_ucs = [
        (4.3, 8.2, "Iniciar sesión"),
        (4.3, 7.3, "Ver grilla de mesas"),
        (4.3, 6.4, "Abrir mesa"),
        (4.3, 5.5, "Agregar producto al pedido"),
        (4.3, 4.6, "Agregar nota a ítem"),
        (4.3, 3.7, "Modificar / eliminar ítem"),
        (4.3, 2.8, "Crear / activar reservación"),
        (4.3, 1.9, "Transferir pedido de mesa"),
    ]
    # Bus vertical para Mozo en x=2.1
    MOZO_BUS = 2.1
    MOZO_Y   = 7.5
    line(ax, MOZO_BUS, mozo_ucs[0][1], MOZO_BUS, mozo_ucs[-1][1], color=BLUE, lw=1.0)
    line(ax, 1.2, MOZO_Y, MOZO_BUS, MOZO_Y, color=BLUE, lw=1.2)
    for x, y, text in mozo_ucs:
        use_case(ax, x, y, text, BLUE)
        ax.plot([MOZO_BUS, x - 1.3], [y, y], color=BLUE, lw=0.9, zorder=2)

    # ── Casos de uso — CHEF (columna centro)
    chef_ucs = [
        (7.5, 7.6, "Ver monitor de cocina (KDS)"),
        (7.5, 6.5, "Aceptar ítem (→ En Cocina)"),
        (7.5, 5.4, "Marcar ítem como Listo"),
        (7.5, 4.3, "Ver tiempo transcurrido FIFO"),
        (7.5, 3.2, "Auto-refresco cada 20 seg."),
    ]
    CHEF_BUS = 2.1
    CHEF_Y   = 4.2
    line(ax, CHEF_BUS, chef_ucs[0][1], CHEF_BUS, chef_ucs[-1][1], color=ORANGE, lw=1.0)
    line(ax, 1.2, CHEF_Y, CHEF_BUS, CHEF_Y, color=ORANGE, lw=1.2)
    for x, y, text in chef_ucs:
        use_case(ax, x, y, text, ORANGE)
        ax.plot([CHEF_BUS, x - 1.3], [y, y], color=ORANGE, lw=0.9, zorder=2)

    # ── Casos de uso — CAJERO (columna der-centro)
    cajero_ucs = [
        (11.0, 8.2, "Abrir / cerrar caja (Arqueo)"),
        (11.0, 7.2, "Cobrar pedido"),
        (11.0, 6.2, "Emitir DocumentoTributario"),
        (11.0, 5.2, "Aplicar descuento / IVA"),
        (11.0, 4.2, "Buscar / registrar cliente"),
        (11.0, 3.2, "Ver reportes (IVA / Reporte Z)"),
        (11.0, 2.2, "Exportar historial a Excel"),
    ]
    CAJERO_BUS = 2.1
    CAJERO_Y   = 1.4
    line(ax, CAJERO_BUS, cajero_ucs[0][1], CAJERO_BUS, cajero_ucs[-1][1], color=PURPLE, lw=1.0)
    line(ax, 1.2, CAJERO_Y, CAJERO_BUS, CAJERO_Y, color=PURPLE, lw=1.2)
    for x, y, text in cajero_ucs:
        use_case(ax, x, y, text, PURPLE)
        ax.plot([CAJERO_BUS, x - 1.3], [y, y], color=PURPLE, lw=0.9, zorder=2)

    # ── Administrador — líneas desde el lado derecho hacia UCs representativas
    admin_ucs = [(4.3, 8.2), (7.5, 7.6), (11.0, 8.2), (11.0, 3.2)]
    ADMIN_BUS_X = 12.8
    line(ax, ADMIN_BUS_X, admin_ucs[0][1], ADMIN_BUS_X, admin_ucs[-1][1], color=GRAY, lw=1.0, dashed=True)
    line(ax, 13.7, 5.0, ADMIN_BUS_X, 5.0, color=GRAY, lw=1.2, dashed=True)
    for x, y in admin_ucs:
        ax.plot([ADMIN_BUS_X, x + 1.3], [y, y], color=GRAY, lw=0.8, ls=':', zorder=2)

    # ── «include» entre casos de uso relacionados
    # Cobrar incluye generar documento
    ax.annotate('', xy=(11.0, 6.5), xytext=(11.0, 6.9),
                arrowprops=dict(arrowstyle='->', color=GRAY, lw=1, linestyle='--'))
    ax.text(11.6, 6.7, "«include»", fontsize=6.5, color=GRAY, style='italic')

    # ── Nota sistema boundary
    ax.text(2.5, 0.55, "«boundary» Sistema Ristorantino", ha='left',
            fontsize=7.5, color='#9CA3AF', style='italic')

    # ── Leyenda
    patches = [
        mpatches.Patch(fc='white', ec=BLUE,   label='Casos de uso — Mozo'),
        mpatches.Patch(fc='white', ec=ORANGE, label='Casos de uso — Chef'),
        mpatches.Patch(fc='white', ec=PURPLE, label='Casos de uso — Cajero'),
        mpatches.Patch(fc='white', ec=GRAY,   label='Administrador (acceso total)'),
    ]
    ax.legend(handles=patches, loc='lower center', fontsize=8,
              framealpha=0.9, edgecolor='#E5E7EB',
              ncol=4, bbox_to_anchor=(0.5, -0.04))

    save(fig, "diagrama_6_4_casos_uso.png")


# ── Run all
diagrama_arquitectura()
diagrama_er()
diagrama_flujo()
diagrama_casos_uso()
print("\nTodos los diagramas generados en C:\\Proyecto\\docs\\")
