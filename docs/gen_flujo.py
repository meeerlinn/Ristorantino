"""
Diagrama 6.3 — Flujo de Procesos (Ristorantino)
Tres paneles: A=Mozo, B=Chef, C=Cajero
Posiciones calculadas programáticamente, sin hardcoding de flechas.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

OUT  = r"C:\Proyecto\docs"
FONT = "DejaVu Sans"
DARK = "#1F2937"

BLUE   = "#2563EB"; LBLUE   = "#DBEAFE"
ORANGE = "#D97706"; LORANGE = "#FEF3C7"
GREEN  = "#059669"; LGREEN  = "#D1FAE5"
PURPLE = "#7C3AED"; LPURPLE = "#EDE9FE"
GRAY   = "#6B7280"; LGRAY   = "#F3F4F6"

# ── Layout ────────────────────────────────────────────────────────────────────
CX    = 4.0    # center-x of all boxes
BW    = 5.0    # rect/oval width  → xl=1.5, xr=6.5
BH    = 0.68   # rect/oval height
DX    = 2.1    # diamond half-width  → left tip=1.9, right tip=6.1
DY    = 0.52   # diamond half-height
BUS_R = 7.35   # right-side routing bus
BUS_L = 0.55   # left-side routing bus
SH    = 1.10   # vertical step spacing (center to center)

# Connection points
def bot(y, typ):
    return y - DY if typ == 'diamond' else y - BH / 2

def top_pt(y, typ):
    return y + DY if typ == 'diamond' else y + BH / 2


# ── Drawing helpers ───────────────────────────────────────────────────────────
def draw_step(ax, y, text, typ, mc, lc):
    if typ == 'oval':
        ax.add_patch(mpatches.Ellipse(
            (CX, y), BW * 0.72, BH * 1.05,
            fc=mc, ec=mc, zorder=3))
        ax.text(CX, y, text, ha='center', va='center',
                fontsize=9, fontweight='bold', color='white',
                fontfamily=FONT, zorder=4)

    elif typ == 'diamond':
        ax.add_patch(plt.Polygon(
            [[CX, y+DY], [CX+DX, y], [CX, y-DY], [CX-DX, y]],
            fc=lc, ec=mc, lw=1.6, zorder=3))
        ax.text(CX, y, text, ha='center', va='center',
                fontsize=7.5, color=DARK, fontfamily=FONT, zorder=4)

    else:  # rect
        ax.add_patch(FancyBboxPatch(
            (CX - BW/2, y - BH/2), BW, BH,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            fc=lc, ec=mc, lw=1.6, zorder=3))
        ax.text(CX, y, text, ha='center', va='center',
                fontsize=8, color=DARK, fontfamily=FONT, zorder=4)


def arrow_down(ax, y_from, y_to, color):
    """Vertical downward arrow at CX."""
    ax.annotate('', xy=(CX, y_to), xytext=(CX, y_from),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5),
                zorder=2)


def ortho_arrow(ax, pts, color):
    """
    Multi-segment orthogonal arrow (only H/V segments).
    Draws lines for all segments; arrowhead only at the last point.
    """
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]; x1, y1 = pts[i + 1]
        ax.plot([x0, x1], [y0, y1], color=color, lw=1.5,
                solid_capstyle='round', zorder=2)
    # arrowhead at destination
    xp, yp = pts[-2]; xe, ye = pts[-1]
    ax.annotate('', xy=(xe, ye),
                xytext=(xp + (xe-xp)*0.55, yp + (ye-yp)*0.55),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5),
                zorder=3)


def lbl(ax, x, y, text, color, ha='center', va='center'):
    ax.text(x, y, text, ha=ha, va=va,
            fontsize=7.5, color=color, fontfamily=FONT, zorder=5,
            bbox=dict(fc='white', ec='none', pad=1.5))


# ── Figure ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(22, 13))
fig.patch.set_facecolor('white')
fig.suptitle("Diagramas de Flujo de Procesos — Ristorantino",
             fontsize=14, fontweight='bold', color=DARK, y=0.99)

for ax in axes:
    ax.set_xlim(-0.3, 8.8)
    ax.set_ylim(-0.6, 12.5)
    ax.axis('off')
    ax.set_facecolor('white')

panel_titles = [
    ("A — Toma de Pedido\n(Mozo)",       BLUE),
    ("B — Flujo de Cocina\n(Chef)",       ORANGE),
    ("C — Cobro y Facturación\n(Cajero)", PURPLE),
]
for ax, (title, color) in zip(axes, panel_titles):
    ax.text(CX, 12.2, title, ha='center', va='center',
            fontsize=11, fontweight='bold', color=color, fontfamily=FONT)

# ══════════════════════════════════════════════════════════════════════════════
# PANEL A — TOMA DE PEDIDO (MOZO)
# 10 pasos, SH=1.10, y[0]=11.3 … y[9]=1.3
# ══════════════════════════════════════════════════════════════════════════════
ax = axes[0]
ya = [11.3 - i * SH for i in range(10)]
# ya: 11.3, 10.2, 9.1, 8.0, 6.9, 5.8, 4.7, 3.6, 2.5, 1.4

steps_a = [
    # (y, text, typ, main_color, light_color)
    (ya[0], "INICIO",                              'oval',    BLUE,   BLUE),
    (ya[1], "Mozo ingresa al salón",               'rect',    BLUE,   LBLUE),
    (ya[2], "Selecciona mesa LIBRE",               'rect',    BLUE,   LBLUE),
    (ya[3], "¿Mesa disponible?",                   'diamond', ORANGE, LORANGE),
    (ya[4], "Abre la mesa\n(crea Pedido)",         'rect',    BLUE,   LBLUE),
    (ya[5], "Agrega productos\n(comanda)",         'rect',    BLUE,   LBLUE),
    (ya[6], "¿Agrega observación\nal ítem?",       'diamond', ORANGE, LORANGE),
    (ya[7], "Guarda nota en\nPedidoDetalle",       'rect',    GREEN,  LGREEN),
    (ya[8], "Confirma pedido\ny vuelve al salón",  'rect',    BLUE,   LBLUE),
    (ya[9], "FIN",                                 'oval',    BLUE,   BLUE),
]

for y, text, typ, mc, lc in steps_a:
    draw_step(ax, y, text, typ, mc, lc)

# Main vertical arrows
typs_a = [s[2] for s in steps_a]
for i in range(len(steps_a) - 1):
    arrow_down(ax, bot(ya[i], typs_a[i]), top_pt(ya[i+1], typs_a[i+1]), BLUE)

# Branch A1: ¿Mesa disponible? No → right bus → back to Selecciona mesa LIBRE
ortho_arrow(ax, [
    (CX + DX,    ya[3]),        # right tip of diamond
    (BUS_R,      ya[3]),        # go right to bus
    (BUS_R,      ya[2]),        # go up to step 2
    (CX + BW/2,  ya[2]),        # enter step 2 from right
], ORANGE)
lbl(ax, BUS_R + 0.38, (ya[2] + ya[3]) / 2, "No\n(elige\notra)", ORANGE, ha='left')
lbl(ax, CX - 0.45, (bot(ya[3], 'diamond') + top_pt(ya[4], 'rect')) / 2, "Sí", BLUE)

# Branch A2: ¿Agrega observación? No → left bus → bypass to Confirma pedido
ortho_arrow(ax, [
    (CX - DX,    ya[6]),        # left tip of diamond
    (BUS_L,      ya[6]),        # go left to bus
    (BUS_L,      ya[8]),        # go down past step 7
    (CX - BW/2,  ya[8]),        # enter step 8 from left
], ORANGE)
lbl(ax, BUS_L - 0.38, ya[6], "No", ORANGE, ha='right')
lbl(ax, CX + 0.45, (bot(ya[6], 'diamond') + top_pt(ya[7], 'rect')) / 2, "Sí", GREEN)

# ══════════════════════════════════════════════════════════════════════════════
# PANEL B — FLUJO DE COCINA (CHEF)
# 11 pasos, y[0]=11.3 … y[10]=0.3
# ══════════════════════════════════════════════════════════════════════════════
ax = axes[1]
yb = [11.3 - i * SH for i in range(11)]
# yb: 11.3, 10.2, 9.1, 8.0, 6.9, 5.8, 4.7, 3.6, 2.5, 1.4, 0.3

steps_b = [
    (yb[0],  "INICIO",                                     'oval',    ORANGE, ORANGE),
    (yb[1],  "Chef abre monitor\nde cocina",               'rect',    ORANGE, LORANGE),
    (yb[2],  "¿Hay ítems\nPENDIENTES?",                   'diamond', ORANGE, LORANGE),
    (yb[3],  "Lee ítem: mesa, producto,\ncantidad, obs.",  'rect',    ORANGE, LORANGE),
    (yb[4],  "Clic 'Empezar'\n→ Estado: EN COCINA",       'rect',    GREEN,  LGREEN),
    (yb[5],  "Prepara el plato\n(obs. aplicadas)",         'rect',    ORANGE, LORANGE),
    (yb[6],  "¿Plato listo?",                              'diamond', ORANGE, LORANGE),
    (yb[7],  "Clic 'Listo'\n→ Estado: LISTO",             'rect',    GREEN,  LGREEN),
    (yb[8],  "Ítem sale del monitor\n→ Mozo lleva el plato", 'rect', GRAY,   LGRAY),
    (yb[9],  "¿Más ítems\npendientes?",                    'diamond', ORANGE, LORANGE),
    (yb[10], "FIN",                                        'oval',    ORANGE, ORANGE),
]

for y, text, typ, mc, lc in steps_b:
    draw_step(ax, y, text, typ, mc, lc)

typs_b = [s[2] for s in steps_b]
for i in range(len(steps_b) - 1):
    arrow_down(ax, bot(yb[i], typs_b[i]), top_pt(yb[i+1], typs_b[i+1]), ORANGE)

# Branch B1: ¿Hay ítems? No → right bus → back to Chef abre monitor
ortho_arrow(ax, [
    (CX + DX,   yb[2]),
    (BUS_R,     yb[2]),
    (BUS_R,     yb[1]),
    (CX + BW/2, yb[1]),
], GRAY)
lbl(ax, BUS_R + 0.38, (yb[1] + yb[2]) / 2, "No\n(espera)", GRAY, ha='left')
lbl(ax, CX - 0.45, (bot(yb[2], 'diamond') + top_pt(yb[3], 'rect')) / 2, "Sí", ORANGE)

# Branch B2: ¿Plato listo? No → right bus → back to Prepara el plato
ortho_arrow(ax, [
    (CX + DX,   yb[6]),
    (BUS_R,     yb[6]),
    (BUS_R,     yb[5]),
    (CX + BW/2, yb[5]),
], ORANGE)
lbl(ax, BUS_R + 0.38, (yb[5] + yb[6]) / 2, "No\n(sigue\ncocinando)", ORANGE, ha='left')
lbl(ax, CX - 0.45, (bot(yb[6], 'diamond') + top_pt(yb[7], 'rect')) / 2, "Sí", GREEN)

# Branch B3: ¿Más ítems? Sí → left bus → back to ¿Hay ítems?
ortho_arrow(ax, [
    (CX - DX,  yb[9]),
    (BUS_L,    yb[9]),
    (BUS_L,    yb[2]),
    (CX - DX,  yb[2]),          # left tip of diamond 2
], ORANGE)
lbl(ax, BUS_L - 0.38, (yb[2] + yb[9]) / 2, "Sí", ORANGE, ha='right')

# "No" label for ¿Más ítems? going down to FIN
lbl(ax, CX - 0.45, (bot(yb[9], 'diamond') + top_pt(yb[10], 'oval')) / 2, "No", ORANGE)

# ══════════════════════════════════════════════════════════════════════════════
# PANEL C — COBRO Y FACTURACIÓN (CAJERO)
# 11 pasos
# ══════════════════════════════════════════════════════════════════════════════
ax = axes[2]
yc = [11.3 - i * SH for i in range(11)]

steps_c = [
    (yc[0],  "INICIO",                                        'oval',    PURPLE, PURPLE),
    (yc[1],  "Cajero abre la caja\n(Arqueo activo)",          'rect',    PURPLE, LPURPLE),
    (yc[2],  "¿Caja abierta?",                                'diamond', PURPLE, LPURPLE),
    (yc[3],  "Selecciona pedido\na cobrar",                   'rect',    PURPLE, LPURPLE),
    (yc[4],  "Verifica ítems\ny total del pedido",            'rect',    PURPLE, LPURPLE),
    (yc[5],  "Busca / identifica\ncliente",                   'rect',    PURPLE, LPURPLE),
    (yc[6],  "Ingresa descuento\ny método de pago",           'rect',    PURPLE, LPURPLE),
    (yc[7],  "Confirma cobro\n→ Genera DocumentoTributario",  'rect',    GREEN,  LGREEN),
    (yc[8],  "Actualiza Arqueo\n+ Mesa → SUCIA",              'rect',    GREEN,  LGREEN),
    (yc[9],  "Imprime / guarda\nfactura",                     'rect',    GRAY,   LGRAY),
    (yc[10], "FIN",                                           'oval',    PURPLE, PURPLE),
]

for y, text, typ, mc, lc in steps_c:
    draw_step(ax, y, text, typ, mc, lc)

typs_c = [s[2] for s in steps_c]
for i in range(len(steps_c) - 1):
    arrow_down(ax, bot(yc[i], typs_c[i]), top_pt(yc[i+1], typs_c[i+1]), PURPLE)

# Branch C1: ¿Caja abierta? No → right bus → back to Cajero abre la caja
ortho_arrow(ax, [
    (CX + DX,   yc[2]),
    (BUS_R,     yc[2]),
    (BUS_R,     yc[1]),
    (CX + BW/2, yc[1]),
], GRAY)
lbl(ax, BUS_R + 0.38, (yc[1] + yc[2]) / 2, "No →\nAbrir caja\nprimero", GRAY, ha='left')
lbl(ax, CX - 0.45, (bot(yc[2], 'diamond') + top_pt(yc[3], 'rect')) / 2, "Sí", PURPLE)

# ── Save ──────────────────────────────────────────────────────────────────────
plt.tight_layout(rect=[0, 0, 1, 0.97])
path = os.path.join(OUT, "diagrama_6_3_flujo_procesos.png")
fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close(fig)
print(f"Guardado: {path}")
