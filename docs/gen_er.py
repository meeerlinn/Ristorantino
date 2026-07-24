"""
Diagrama ER de Ristorantino
Conectores ortogonales que solo viajan por los "buses" (espacios entre columnas/filas)
Canvas: 26 x 18.5 pulgadas
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

OUT  = r"C:\Proyecto\docs"
FONT = "DejaVu Sans"

# ── Colores ────────────────────────────────────────────────────────────────────
GRP = {
    'personal': dict(hdr="#374151", light="#F9FAFB", border="#6B7280"),
    'salon':    dict(hdr="#1E40AF", light="#EFF6FF", border="#3B82F6"),
    'menu':     dict(hdr="#065F46", light="#ECFDF5", border="#10B981"),
    'pedidos':  dict(hdr="#0E7490", light="#F0FDFA", border="#06B6D4"),
    'cocina':   dict(hdr="#92400E", light="#FFFBEB", border="#F59E0B"),
    'fiscal':   dict(hdr="#4C1D95", light="#F5F3FF", border="#8B5CF6"),
}
WHITE = "#FFFFFF"
PK_C  = "#1D4ED8"
FK_C  = "#B45309"
TYP_C = "#9CA3AF"
NRM_C = "#374151"
DARK  = "#1F2937"

HDR_H  = 0.44
ROW_H  = 0.295

def entity_height(n):
    return 0.49 + n * ROW_H

# ── Dibujar entidad ────────────────────────────────────────────────────────────
def draw_entity(ax, cx, cy, w, name, fields, grp):
    h   = entity_height(len(fields))
    xl  = cx - w / 2
    yb  = cy - h / 2
    c   = GRP[grp]

    ax.add_patch(FancyBboxPatch((xl+0.05, yb-0.05), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        fc="#D1D5DB", ec="none", zorder=2))
    ax.add_patch(FancyBboxPatch((xl, yb), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        fc=c['light'], ec=c['border'], lw=1.4, zorder=3))
    ax.add_patch(FancyBboxPatch((xl, yb + h - HDR_H), w, HDR_H,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        fc=c['hdr'], ec=c['hdr'], lw=0, zorder=4))
    ax.text(cx, yb + h - HDR_H/2, name,
            ha='center', va='center', fontsize=8.5,
            fontweight='bold', color=WHITE, zorder=5, fontfamily=FONT)
    ax.plot([xl, xl+w], [yb+h-HDR_H, yb+h-HDR_H],
            color=c['border'], lw=0.8, zorder=5)

    for i, (fname, ftype, kind) in enumerate(fields):
        fy = yb + h - HDR_H - (i + 0.5) * ROW_H
        if kind == 'pk':
            badge, ic = 'PK', PK_C
        elif kind == 'fk':
            badge, ic = 'FK', FK_C
        else:
            badge, ic = '  ', NRM_C
        ax.text(xl + 0.13, fy, badge,
                ha='left', va='center', fontsize=5.8, color=ic,
                fontweight='bold', fontfamily=FONT, zorder=5)
        ax.text(xl + 0.38, fy, fname,
                ha='left', va='center', fontsize=7, color=ic,
                fontfamily=FONT, zorder=5)
        ax.text(xl + w - 0.10, fy, ftype,
                ha='right', va='center', fontsize=6.5, color=TYP_C,
                fontfamily=FONT, zorder=5)
        if i < len(fields) - 1:
            ax.plot([xl+0.05, xl+w-0.05],
                    [yb+h-HDR_H-(i+1)*ROW_H]*2,
                    color="#E5E7EB", lw=0.5, zorder=4)

    return dict(xl=xl, xr=xl+w, yb=yb, yt=yb+h, cx=cx, cy=cy, w=w, h=h)


# campo-y: y del campo i (0=primer campo tras header)
def fy(e, i):
    return e['yt'] - HDR_H - (i + 0.5) * ROW_H


# ── Conector ortogonal ─────────────────────────────────────────────────────────
def conn(ax, pts, color, card_s=None, card_e=None, lw=1.3):
    """
    pts: lista de (x,y). Dibuja segmentos H o V entre puntos consecutivos.
    Pone flecha en el último punto.
    """
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]; x1, y1 = pts[i+1]
        ax.plot([x0, x1], [y0, y1], color=color, lw=lw,
                solid_capstyle='round', zorder=6)
    # flecha en destino
    x_last, y_last = pts[-1]
    x_prev, y_prev = pts[-2]
    ax.annotate('', xy=(x_last, y_last),
                xytext=(x_prev + (x_last-x_prev)*0.85,
                        y_prev + (y_last-y_prev)*0.85),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw),
                zorder=7)
    OFF = 0.20
    def label_at(p0, p1, text):
        dx, dy = p1[0]-p0[0], p1[1]-p0[1]
        d = (dx**2+dy**2)**0.5 or 1
        ox, oy = -dy/d*OFF, dx/d*OFF
        ax.text(p0[0]+ox, p0[1]+oy, text,
                ha='center', va='center', fontsize=7.5,
                color=color, fontweight='bold', zorder=8,
                fontfamily=FONT,
                bbox=dict(fc='white', ec='none', pad=0.8))
    if card_s:
        label_at(pts[0], pts[1], card_s)
    if card_e:
        label_at(pts[-1], pts[-2], card_e)


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# Columnas (cx):  1.6 | 5.2 | 8.8 | 12.7 | 17.0 | 21.2
# Buses verticales entre columnas: 3.4 | 6.85 | 10.65 | 14.85 | 19.0
# Bus izquierdo:  -0.1
# Bus superior:   17.4
# Bus inferior:   1.8
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(26, 18.5))
ax.set_xlim(-0.8, 26)
ax.set_ylim(1.3, 18.8)
ax.axis('off')
fig.patch.set_facecolor('white')

ax.text(12.5, 18.5,
        "Diagrama Entidad-Relación — Ristorantino",
        ha='center', va='center', fontsize=16, fontweight='bold',
        color=DARK, fontfamily=FONT)

# ── Entidades ─────────────────────────────────────────────────────────────────
E = {}

# COL 1  cx=1.6
E['usuarios'] = draw_entity(ax, 1.6, 16.0, 2.7, 'usuarios', [
    ('id',        'integer', 'pk'),
    ('rol_id',    'integer', 'fk'),
    ('username',  'varchar', 'normal'),
    ('password',  'varchar', 'normal'),
    ('is_active', 'boolean', 'normal'),
], 'personal')

E['mesas'] = draw_entity(ax, 1.6, 12.9, 2.7, 'mesas', [
    ('id',          'integer', 'pk'),
    ('sector_id',   'integer', 'fk'),
    ('numero_mesa', 'integer', 'normal'),
    ('capacidad',   'integer', 'normal'),
    ('estado',      'varchar', 'normal'),
], 'salon')

E['categorias'] = draw_entity(ax, 1.6, 10.5, 2.7, 'categorias', [
    ('id',     'integer', 'pk'),
    ('nombre', 'varchar', 'normal'),
], 'menu')

E['roles'] = draw_entity(ax, 1.6, 8.7, 2.7, 'roles', [
    ('id',     'integer', 'pk'),
    ('nombre', 'varchar', 'normal'),
    ('estado', 'boolean', 'normal'),
], 'personal')

E['sectores'] = draw_entity(ax, 1.6, 6.8, 2.7, 'sectores', [
    ('id',     'integer', 'pk'),
    ('nombre', 'varchar', 'normal'),
], 'salon')

E['caja_timbrado'] = draw_entity(ax, 1.6, 4.4, 2.8, 'caja_timbrado', [
    ('id',               'integer',   'pk'),
    ('caja_id',          'integer',   'fk'),
    ('timbrado_id',      'integer',   'fk'),
    ('punto_expedicion', 'varchar',   'normal'),
    ('estado',           'varchar',   'normal'),
    ('fecha_asignacion', 'timestamp', 'normal'),
], 'fiscal')

# COL 2  cx=5.2
E['empleados'] = draw_entity(ax, 5.2, 8.7, 2.7, 'empleados', [
    ('id',         'integer', 'pk'),
    ('usuario_id', 'integer', 'fk'),
    ('nombre',     'varchar', 'normal'),
    ('apellido',   'varchar', 'normal'),
    ('ci',         'varchar', 'normal'),
    ('cargo',      'varchar', 'normal'),
], 'personal')

# COL 3  cx=8.8
E['pedidos'] = draw_entity(ax, 8.8, 15.5, 3.0, 'pedidos', [
    ('id',             'integer',   'pk'),
    ('mesa_id',        'integer',   'fk'),
    ('mozo_id',        'integer',   'fk'),
    ('cliente_id',     'integer',   'fk'),
    ('fecha_apertura', 'timestamp', 'normal'),
    ('fecha_cierre',   'timestamp', 'normal'),
    ('estado_pago',    'varchar',   'normal'),
    ('total_pedido',   'decimal',   'normal'),
], 'pedidos')

E['productos'] = draw_entity(ax, 8.8, 11.8, 2.9, 'productos', [
    ('id',           'integer', 'pk'),
    ('categoria_id', 'integer', 'fk'),
    ('nombre',       'varchar', 'normal'),
    ('precio_venta', 'decimal', 'normal'),
    ('costo_insumo', 'decimal', 'normal'),
    ('disponible',   'boolean', 'normal'),
], 'menu')

E['clientes'] = draw_entity(ax, 8.8, 9.05, 2.9, 'clientes', [
    ('id',                  'integer', 'pk'),
    ('nombre_razon_social', 'varchar', 'normal'),
    ('ruc_ci',              'varchar', 'normal'),
    ('telefono',            'varchar', 'normal'),
    ('direccion',           'varchar', 'normal'),
], 'pedidos')

E['tipos_documentos'] = draw_entity(ax, 7.2, 6.3, 2.7, 'tipos_documentos', [
    ('id',     'integer', 'pk'),
    ('nombre', 'varchar', 'normal'),
    ('estado', 'boolean', 'normal'),
], 'fiscal')

# COL 4  cx=12.7
E['timbrados'] = draw_entity(ax, 12.7, 9.6, 3.0, 'timbrados', [
    ('id',                'integer', 'pk'),
    ('tipo_doc_id',       'integer', 'fk'),
    ('numero_timbrado',   'varchar', 'normal'),
    ('fecha_vencimiento', 'date',    'normal'),
    ('serie',             'varchar', 'normal'),
    ('rango_desde',       'integer', 'normal'),
    ('rango_hasta',       'integer', 'normal'),
    ('activo',            'boolean', 'normal'),
], 'fiscal')

E['arqueos'] = draw_entity(ax, 12.7, 4.55, 3.0, 'arqueos', [
    ('id',                   'integer',   'pk'),
    ('caja_id',              'integer',   'fk'),
    ('usuario_id',           'integer',   'fk'),
    ('fecha_apertura',       'timestamp', 'normal'),
    ('fecha_cierre',         'timestamp', 'normal'),
    ('monto_apertura',       'decimal',   'normal'),
    ('monto_cierre_sistema', 'decimal',   'normal'),
    ('monto_cierre_real',    'decimal',   'normal'),
    ('diferencia_arqueo',    'decimal',   'normal'),
    ('estado',               'varchar',   'normal'),
], 'fiscal')

# COL 5  cx=17.0
E['pedido_detalle'] = draw_entity(ax, 17.0, 15.5, 3.0, 'pedido_detalle', [
    ('id',               'integer', 'pk'),
    ('pedido_id',        'integer', 'fk'),
    ('producto_id',      'integer', 'fk'),
    ('cantidad',         'integer', 'normal'),
    ('precio_historico', 'decimal', 'normal'),
    ('observaciones',    'text',    'normal'),
], 'pedidos')

E['pedido_documento'] = draw_entity(ax, 17.0, 8.0, 3.0, 'pedido_documento', [
    ('id',            'integer', 'pk'),
    ('pedido_id',     'integer', 'fk'),
    ('documento_id',  'integer', 'fk'),
    ('estado_vinculo','varchar', 'normal'),
], 'pedidos')

E['documentos_tributarios'] = draw_entity(ax, 17.0, 4.35, 3.0, 'documentos_tributarios', [
    ('id',           'integer', 'pk'),
    ('timbrado_id',  'integer', 'fk'),
    ('arqueo_id',    'integer', 'fk'),
    ('cliente_id',   'integer', 'fk'),
    ('nro_factura',  'varchar', 'normal'),
    ('total_exenta', 'decimal', 'normal'),
    ('total_iva_5',  'decimal', 'normal'),
    ('total_iva_10', 'decimal', 'normal'),
    ('monto_total',  'decimal', 'normal'),
    ('estado',       'varchar', 'normal'),
], 'fiscal')

# COL 6  cx=21.2
E['flujo_estados'] = draw_entity(ax, 21.2, 15.5, 2.8, 'flujo_estados', [
    ('id',                'integer',   'pk'),
    ('pedido_detalle_id', 'integer',   'fk'),
    ('estado',            'varchar',   'normal'),
    ('timestamp',         'timestamp', 'normal'),
], 'cocina')

E['cajas'] = draw_entity(ax, 21.2, 9.4, 2.7, 'cajas', [
    ('id',        'integer', 'pk'),
    ('nombre',    'varchar', 'normal'),
    ('is_active', 'boolean', 'normal'),
], 'fiscal')

# ══════════════════════════════════════════════════════════════════════════════
# BUSES (x/y de "carriles" seguros entre columnas y filas)
# ══════════════════════════════════════════════════════════════════════════════
# Buses verticales (x)
BUS_L   = -0.30   # izquierdo de col 1
BUS_12  =  3.35   # entre col1 y col2
BUS_23  =  6.85   # entre col2 y col3
BUS_34  = 10.65   # entre col3 y col4   (principales)
BUS_34b = 10.40   # un carril más a la izquierda del bus 3-4
BUS_34c = 10.90   # carril más a la derecha del bus 3-4
BUS_45  = 14.85   # entre col4 y col5
BUS_45b = 14.60   # un carril más
BUS_56  = 19.15   # entre col5 y col6

# Buses horizontales (y)
BUS_TOP = 17.4    # por encima de todas las entidades (max yt ≈ 17.0)
BUS_BOT = 1.90    # por debajo de todas las entidades (min yb ≈ 2.4)

# ── COLORES por grupo de relación ─────────────────────────────────────────────
C_PER = GRP['personal']['border']
C_SAL = GRP['salon']['border']
C_MEN = GRP['menu']['border']
C_PED = GRP['pedidos']['border']
C_COC = GRP['cocina']['border']
C_FIS = GRP['fiscal']['border']

# ══════════════════════════════════════════════════════════════════════════════
# RELACIONES  (cada conn() solo recorre buses/espacios vacíos)
# ══════════════════════════════════════════════════════════════════════════════

# ─ 1. roles → usuarios.rol_id  [1:N]  — bus izquierdo
conn(ax, [
    (E['roles']['xl'],    E['roles']['cy']),
    (BUS_L,               E['roles']['cy']),
    (BUS_L,               fy(E['usuarios'], 1)),
    (E['usuarios']['xl'], fy(E['usuarios'], 1)),
], C_PER, card_s='1', card_e='N')

# ─ 2. sectores → mesas.sector_id  [1:N]  — bus izquierdo (carril más interior)
conn(ax, [
    (E['sectores']['xl'], E['sectores']['cy']),
    (BUS_L + 0.10,        E['sectores']['cy']),
    (BUS_L + 0.10,        fy(E['mesas'], 1)),
    (E['mesas']['xl'],    fy(E['mesas'], 1)),
], C_SAL, card_s='1', card_e='N')

# ─ 3. categorias → produtos.categoria_id  [1:N]  — bus 2-3
conn(ax, [
    (E['categorias']['xr'], E['categorias']['cy']),
    (BUS_23,                E['categorias']['cy']),
    (BUS_23,                fy(E['productos'], 1)),
    (E['productos']['xl'],  fy(E['productos'], 1)),
], C_MEN, card_s='1', card_e='N')

# ─ 4. usuarios → empleados.usuario_id  [1:1]  — bus 1-2
conn(ax, [
    (E['usuarios']['xr'], E['usuarios']['cy']),
    (BUS_12,              E['usuarios']['cy']),
    (BUS_12,              fy(E['empleados'], 1)),
    (E['empleados']['xl'],fy(E['empleados'], 1)),
], C_PER, card_s='1', card_e='1')

# ─ 5. mesas → pedidos.mesa_id  [1:N]  — bus 2-3
conn(ax, [
    (E['mesas']['xr'],   E['mesas']['cy']),
    (BUS_23,             E['mesas']['cy']),
    (BUS_23,             fy(E['pedidos'], 1)),
    (E['pedidos']['xl'], fy(E['pedidos'], 1)),
], C_SAL, card_s='1', card_e='N')

# ─ 6. usuarios → pedidos.mozo_id  [1:N]
#      Sale por la derecha, sube por bus 2-3 (carril +0.1)
conn(ax, [
    (E['usuarios']['xr'],  fy(E['usuarios'], 0)),
    (BUS_23 + 0.10,        fy(E['usuarios'], 0)),
    (BUS_23 + 0.10,        fy(E['pedidos'],  2)),
    (E['pedidos']['xl'],   fy(E['pedidos'],  2)),
], C_PED, card_s='1', card_e='N')

# ─ 7. clientes → pedidos.cliente_id  [1:N]
#      clientes y pedidos están en col3 pero con productos en medio
#      Sale por la derecha, sube por bus 3-4 (carril izquierdo)
conn(ax, [
    (E['clientes']['xr'],  fy(E['clientes'], 0)),
    (BUS_34b,              fy(E['clientes'], 0)),
    (BUS_34b,              fy(E['pedidos'],  3)),
    (E['pedidos']['xr'],   fy(E['pedidos'],  3)),
], C_PED, card_s='1', card_e='N')

# ─ 8. pedidos → pedido_detalle.pedido_id  [1:N]
#      Sube por bus_top, baja por BUS_45+0.15 (a la izquierda de pedido_detalle)
conn(ax, [
    (E['pedidos']['xr'],         fy(E['pedidos'], 0)),
    (BUS_34,                     fy(E['pedidos'], 0)),
    (BUS_34,                     BUS_TOP),
    (BUS_45 + 0.15,              BUS_TOP),
    (BUS_45 + 0.15,              fy(E['pedido_detalle'], 1)),
    (E['pedido_detalle']['xl'],  fy(E['pedido_detalle'], 1)),
], C_PED, card_s='1', card_e='N')

# ─ 9. produtos → pedido_detalle.producto_id  [1:N]
#      Sale por la derecha, sube por bus 3-4, va horizontal
conn(ax, [
    (E['productos']['xr'],       fy(E['productos'], 0)),
    (BUS_34,                     fy(E['productos'], 0)),
    (BUS_34,                     fy(E['pedido_detalle'], 2)),
    (E['pedido_detalle']['xl'],  fy(E['pedido_detalle'], 2)),
], C_MEN, card_s='1', card_e='N')

# ─ 10. pedido_detalle → flujo_estados.pedido_detalle_id  [1:N]
conn(ax, [
    (E['pedido_detalle']['xr'], fy(E['pedido_detalle'], 0)),
    (BUS_56,                    fy(E['pedido_detalle'], 0)),
    (BUS_56,                    fy(E['flujo_estados'],  1)),
    (E['flujo_estados']['xl'],  fy(E['flujo_estados'],  1)),
], C_COC, card_s='1', card_e='N')

# ─ 11. tipos_documentos → timbrados.tipo_doc_id  [1:N]
#       bus 3-4 derecho
conn(ax, [
    (E['tipos_documentos']['xr'], fy(E['tipos_documentos'], 0)),
    (BUS_34c,                     fy(E['tipos_documentos'], 0)),
    (BUS_34c,                     fy(E['timbrados'], 1)),
    (E['timbrados']['xl'],        fy(E['timbrados'], 1)),
], C_FIS, card_s='1', card_e='N')

# ─ 12. cajas → caja_timbrado.caja_id  [1:N]
#       sale por abajo de cajas → bus inferior → bus izquierdo → sube
conn(ax, [
    (E['cajas']['cx'],             E['cajas']['yb']),
    (E['cajas']['cx'],             BUS_BOT),
    (E['caja_timbrado']['xr'],     BUS_BOT),
    (E['caja_timbrado']['xr'],     fy(E['caja_timbrado'], 1)),
], C_FIS, card_s='1', card_e='N')

# ─ 13. timbrados → caja_timbrado.timbrado_id  [1:N]
#       baja por bus 3-4c → bus inferior (carril interior) → bus izq → sube
conn(ax, [
    (E['timbrados']['xl'],       E['timbrados']['cy']),
    (BUS_34c,                    E['timbrados']['cy']),
    (BUS_34c,                    BUS_BOT + 0.12),
    (E['caja_timbrado']['xr'],   BUS_BOT + 0.12),
    (E['caja_timbrado']['xr'],   fy(E['caja_timbrado'], 2)),
], C_FIS, card_s='1', card_e='N')

# ─ 14. cajas → arqueos.caja_id  [1:N]
#       sale por la izquierda de cajas → bus 4-5 → arqueos derecha
conn(ax, [
    (E['cajas']['xl'],    fy(E['cajas'], 0)),
    (BUS_45,              fy(E['cajas'], 0)),
    (BUS_45,              fy(E['arqueos'], 1)),
    (E['arqueos']['xr'],  fy(E['arqueos'], 1)),
], C_FIS, card_s='1', card_e='N')

# ─ 15. usuarios → arqueos.usuario_id  [1:N]
#       sube por bus_top, baja por bus 4-5
conn(ax, [
    (E['usuarios']['cx'],   E['usuarios']['yt']),
    (E['usuarios']['cx'],   BUS_TOP),
    (BUS_45,                BUS_TOP),
    (BUS_45,                fy(E['arqueos'], 2)),
    (E['arqueos']['xr'],    fy(E['arqueos'], 2)),
], C_PER, card_s='1', card_e='N')

# ─ 16. timbrados → documentos_tributarios.timbrado_id  [1:N]
#       bus 4-5 carril izquierdo
conn(ax, [
    (E['timbrados']['xr'],               fy(E['timbrados'], 0)),
    (BUS_45b,                            fy(E['timbrados'], 0)),
    (BUS_45b,                            fy(E['documentos_tributarios'], 1)),
    (E['documentos_tributarios']['xl'],  fy(E['documentos_tributarios'], 1)),
], C_FIS, card_s='1', card_e='N')

# ─ 17. arqueos → documentos_tributarios.arqueo_id  [1:N]
#       sale por la derecha de arqueos → bus 4-5b
conn(ax, [
    (E['arqueos']['xr'],                 fy(E['arqueos'], 0)),
    (BUS_45b - 0.08,                     fy(E['arqueos'], 0)),
    (BUS_45b - 0.08,                     fy(E['documentos_tributarios'], 2)),
    (E['documentos_tributarios']['xl'],  fy(E['documentos_tributarios'], 2)),
], C_FIS, card_s='1', card_e='N')

# ─ 18. clientes → documentos_tributarios.cliente_id  [1:N]
#       El tramo horizontal debe quedar por ENCIMA del header de arqueos (yt+0.18)
conn(ax, [
    (E['clientes']['cx'],               E['clientes']['yb']),
    (E['clientes']['cx'],               E['arqueos']['yt'] + 0.18),
    (BUS_45b - 0.16,                    E['arqueos']['yt'] + 0.18),
    (BUS_45b - 0.16,                    fy(E['documentos_tributarios'], 3)),
    (E['documentos_tributarios']['xl'], fy(E['documentos_tributarios'], 3)),
], C_PED, card_s='1', card_e='N')

# ─ 19. pedidos → pedido_documento.pedido_id  [1:1]
#       sale por derecha, baja por bus 3-4 → cruza
conn(ax, [
    (E['pedidos']['xr'],          fy(E['pedidos'], 0) - 0.30),
    (BUS_34 + 0.08,               fy(E['pedidos'], 0) - 0.30),
    (BUS_34 + 0.08,               fy(E['pedido_documento'], 1)),
    (E['pedido_documento']['xl'], fy(E['pedido_documento'], 1)),
], C_PED, card_s='1', card_e='1')

# ─ 20. documentos_tributarios → pedido_documento.documento_id  [1:1]
#       mismo col5, sube por bus 5-6
conn(ax, [
    (E['documentos_tributarios']['xr'], fy(E['documentos_tributarios'], 0)),
    (BUS_56 + 0.10,                     fy(E['documentos_tributarios'], 0)),
    (BUS_56 + 0.10,                     fy(E['pedido_documento'], 2)),
    (E['pedido_documento']['xr'],       fy(E['pedido_documento'], 2)),
], C_FIS, card_s='1', card_e='1')

# ══════════════════════════════════════════════════════════════════════════════
# LEYENDA
# ══════════════════════════════════════════════════════════════════════════════
legend_items = [
    (GRP['personal']['hdr'], 'Personal / Acceso'),
    (GRP['salon']['hdr'],    'Salón / Mesas'),
    (GRP['menu']['hdr'],     'Menú / Productos'),
    (GRP['pedidos']['hdr'],  'Pedidos'),
    (GRP['cocina']['hdr'],   'Cocina'),
    (GRP['fiscal']['hdr'],   'Contabilidad / Fiscal'),
]
patches = [mpatches.Patch(fc=c, ec=c, label=l) for c, l in legend_items]
patches.append(mpatches.Patch(fc='white', ec=PK_C, label='PK — Clave primaria'))
patches.append(mpatches.Patch(fc='white', ec=FK_C, label='FK — Clave foránea'))

ax.legend(handles=patches, loc='lower center', fontsize=8,
          framealpha=0.95, edgecolor='#D1D5DB', ncol=8,
          bbox_to_anchor=(0.5, -0.02), handlelength=1.5)

# ── Guardar ───────────────────────────────────────────────────────────────────
path = os.path.join(OUT, "diagrama_6_2_entidad_relacion.png")
fig.savefig(path, dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close(fig)
print(f"Guardado: {path}")
