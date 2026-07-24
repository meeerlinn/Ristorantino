"""
Diagrama 6.4 — Casos de Uso (Ristorantino)
Tres secciones coloreadas por rol dentro del boundary del sistema.
Actores debajo de su sección, muñecos mejorados, conexiones claras.
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

BLUE   = "#2563EB"; LBLUE   = "#DBEAFE"; LBLUE2  = "#EFF6FF"
ORANGE = "#D97706"; LORANGE = "#FEF3C7"; LORANGE2= "#FFFBEB"
GREEN  = "#059669"; LGREEN  = "#D1FAE5"
PURPLE = "#7C3AED"; LPURPLE = "#EDE9FE"; LPURPLE2= "#FAF5FF"
GRAY   = "#6B7280"; LGRAY   = "#F3F4F6"

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(24, 15))
ax.set_xlim(0, 26)
ax.set_ylim(0, 16)
ax.axis('off')
fig.patch.set_facecolor('white')

ax.text(13, 15.5, "Diagrama de Casos de Uso — Ristorantino",
        ha='center', va='center', fontsize=16, fontweight='bold',
        color=DARK, fontfamily=FONT)

# ══════════════════════════════════════════════════════════════════════════════
# SISTEMA BOUNDARY
# ══════════════════════════════════════════════════════════════════════════════
SYS_XL, SYS_XR = 3.0, 23.0
SYS_YB, SYS_YT = 3.8, 14.8
ax.add_patch(FancyBboxPatch(
    (SYS_XL, SYS_YB), SYS_XR - SYS_XL, SYS_YT - SYS_YB,
    boxstyle="round,pad=0.1,rounding_size=0.3",
    fc='#FAFAFA', ec='#94A3B8', lw=2, ls='--', zorder=1))
ax.text((SYS_XL + SYS_XR) / 2, SYS_YT - 0.3,
        "«Sistema» Ristorantino",
        ha='center', va='top', fontsize=10,
        color='#94A3B8', style='italic', fontfamily=FONT)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIONES (fondos por rol)
# ══════════════════════════════════════════════════════════════════════════════
SEC = {
    'mozo':   dict(cx=5.8,  xl=3.3,  xr=8.3,  color=BLUE,   light=LBLUE2),
    'chef':   dict(cx=13.0, xl=9.0,  xr=17.0, color=ORANGE, light=LORANGE2),
    'cajero': dict(cx=20.5, xl=17.3, xr=22.7, color=PURPLE, light=LPURPLE2),
}
SEC_YB, SEC_YT = 4.1, 14.5

for key, s in SEC.items():
    # Fondo de sección
    ax.add_patch(FancyBboxPatch(
        (s['xl'], SEC_YB), s['xr'] - s['xl'], SEC_YT - SEC_YB,
        boxstyle="round,pad=0.1,rounding_size=0.2",
        fc=s['light'], ec=s['color'], lw=1.5, alpha=0.6, zorder=2))
    # Etiqueta de sección
    ax.text(s['cx'], SEC_YT - 0.28, key.upper(),
            ha='center', va='top', fontsize=10, fontweight='bold',
            color=s['color'], fontfamily=FONT, zorder=3)

# ══════════════════════════════════════════════════════════════════════════════
# USE CASES
# ══════════════════════════════════════════════════════════════════════════════
UCW = 4.6   # ellipse width
UCH = 0.60  # ellipse height

def draw_uc(ax, cx, y, text, color, lc):
    ax.add_patch(mpatches.Ellipse(
        (cx, y), UCW, UCH,
        fc=lc, ec=color, lw=1.6, zorder=4))
    ax.text(cx, y, text, ha='center', va='center',
            fontsize=8, color=DARK, fontfamily=FONT, zorder=5)

# ── Mozo UCs ──────────────────────────────────────────────────────────────────
cx_m = SEC['mozo']['cx']
mozo_ucs_texts = [
    "Iniciar sesión",
    "Ver grilla de mesas",
    "Abrir mesa / pedido",
    "Agregar producto al pedido",
    "Agregar nota a ítem",
    "Modificar / eliminar ítem",
    "Crear / activar reserva",
    "Transferir pedido de mesa",
]
n_m = len(mozo_ucs_texts)
mozo_ys = [SEC_YT - 0.8 - i * ((SEC_YT - SEC_YB - 1.4) / (n_m - 1)) for i in range(n_m)]

for y, text in zip(mozo_ys, mozo_ucs_texts):
    draw_uc(ax, cx_m, y, text, BLUE, LBLUE)

# ── Chef UCs ──────────────────────────────────────────────────────────────────
cx_c = SEC['chef']['cx']
chef_ucs_texts = [
    "Ver monitor de cocina (KDS)",
    "Aceptar ítem (→ En Cocina)",
    "Marcar ítem como Listo",
    "Ver tiempo transcurrido (FIFO)",
    "Auto-refresco cada 20 seg.",
]
n_c = len(chef_ucs_texts)
chef_ys = [SEC_YT - 0.8 - i * ((SEC_YT - SEC_YB - 1.4) / (n_c - 1)) for i in range(n_c)]

for y, text in zip(chef_ys, chef_ucs_texts):
    draw_uc(ax, cx_c, y, text, ORANGE, LORANGE)

# ── Cajero UCs ────────────────────────────────────────────────────────────────
cx_ca = SEC['cajero']['cx']
cajero_ucs_texts = [
    "Abrir / cerrar caja (Arqueo)",
    "Cobrar pedido",
    "Emitir DocumentoTributario",
    "Aplicar descuento / IVA",
    "Buscar / registrar cliente",
    "Ver reportes (IVA / Rep. Z)",
    "Exportar historial a Excel",
]
n_ca = len(cajero_ucs_texts)
cajero_ys = [SEC_YT - 0.8 - i * ((SEC_YT - SEC_YB - 1.4) / (n_ca - 1)) for i in range(n_ca)]

for y, text in zip(cajero_ys, cajero_ucs_texts):
    draw_uc(ax, cx_ca, y, text, PURPLE, LPURPLE)

# ══════════════════════════════════════════════════════════════════════════════
# «include» entre Cobrar pedido y Emitir DocumentoTributario
# ══════════════════════════════════════════════════════════════════════════════
y_cobrar = cajero_ys[1]      # "Cobrar pedido"
y_emitir = cajero_ys[2]      # "Emitir DocumentoTributario"
ax.annotate('', xy=(cx_ca, y_emitir + UCH/2),
            xytext=(cx_ca, y_cobrar - UCH/2),
            arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.2,
                            linestyle='dashed'), zorder=6)
ax.text(cx_ca + 0.6, (y_cobrar + y_emitir) / 2,
        "«include»", ha='left', va='center',
        fontsize=7.5, color=GRAY, style='italic', fontfamily=FONT, zorder=6)

# ══════════════════════════════════════════════════════════════════════════════
# ACTORES — muñecos mejorados
# ══════════════════════════════════════════════════════════════════════════════
ACTOR_Y = 2.5   # y-center of actor figure body
HEAD_R  = 0.26
BODY_H  = 0.50
ARM_DX  = 0.42
ARM_DY  = -0.16
LEG_DX  = 0.28
LEG_H   = 0.48

def draw_actor(ax, cx, name, color):
    """Stick figure with improved proportions."""
    # Head
    head_cy = ACTOR_Y + BODY_H + HEAD_R + 0.05
    head = mpatches.Circle((cx, head_cy), HEAD_R,
                            fc=color, ec=color, zorder=6)
    ax.add_patch(head)
    # Body
    body_top = head_cy - HEAD_R
    body_bot = ACTOR_Y
    ax.plot([cx, cx], [body_bot, body_top],
            color=color, lw=2.2, solid_capstyle='round', zorder=6)
    # Arms (from mid-body, angled down)
    arm_y = body_bot + (body_top - body_bot) * 0.65
    ax.plot([cx - ARM_DX, cx + ARM_DX],
            [arm_y + ARM_DY, arm_y + ARM_DY],
            color=color, lw=2.2, solid_capstyle='round', zorder=6)
    # Legs (spread from hip)
    ax.plot([cx, cx - LEG_DX], [body_bot, body_bot - LEG_H],
            color=color, lw=2.2, solid_capstyle='round', zorder=6)
    ax.plot([cx, cx + LEG_DX], [body_bot, body_bot - LEG_H],
            color=color, lw=2.2, solid_capstyle='round', zorder=6)
    # Name
    ax.text(cx, ACTOR_Y - LEG_H - 0.15, name,
            ha='center', va='top', fontsize=11, fontweight='bold',
            color=color, fontfamily=FONT, zorder=6)
    # Return top-of-head y for connection line
    return head_cy + HEAD_R

draw_actor(ax, cx_m,  "Mozo",   BLUE)
draw_actor(ax, cx_c,  "Chef",   ORANGE)
draw_actor(ax, cx_ca, "Cajero", PURPLE)

# ══════════════════════════════════════════════════════════════════════════════
# CONEXIONES actor → casos de uso
# (línea desde cabeza del actor hasta cada caso de uso de su sección)
# ══════════════════════════════════════════════════════════════════════════════
HEAD_TOP_Y = ACTOR_Y + BODY_H + HEAD_R * 2 + 0.05   # ≈ top of head

def connect_actor_to_ucs(ax, cx, uc_ys, color):
    """
    Una línea vertical desde la cabeza del actor hasta cada UC.
    Como todos comparten x=cx, se dibuja una única línea larga
    (la más larga) y los UCs quedan como nodos encima (zorder mayor).
    """
    topmost_y = min(uc_ys)   # UC con y numérica más baja = más arriba
    spine_top = topmost_y - UCH / 2
    # Línea vertical única desde cabeza del actor hasta el UC más lejano
    ax.plot([cx, cx], [HEAD_TOP_Y, spine_top],
            color=color, lw=1.4, alpha=0.65,
            solid_capstyle='round', zorder=3)

connect_actor_to_ucs(ax, cx_m,  mozo_ys,   BLUE)
connect_actor_to_ucs(ax, cx_c,  chef_ys,   ORANGE)
connect_actor_to_ucs(ax, cx_ca, cajero_ys, PURPLE)

# ══════════════════════════════════════════════════════════════════════════════
# ADMINISTRADOR — actor externo (derecha), acceso total
# ══════════════════════════════════════════════════════════════════════════════
ADMIN_X = 24.7
ADMIN_Y_ACT = 8.0   # y-center of admin figure body

def draw_actor_ext(ax, cx, y_body, name, color):
    """Same stick figure but positioned at arbitrary y."""
    head_cy = y_body + BODY_H + HEAD_R + 0.05
    ax.add_patch(mpatches.Circle((cx, head_cy), HEAD_R,
                 fc=color, ec=color, zorder=6))
    body_top = head_cy - HEAD_R
    ax.plot([cx, cx], [y_body, body_top],
            color=color, lw=2.2, solid_capstyle='round', zorder=6)
    arm_y = y_body + (body_top - y_body) * 0.65
    ax.plot([cx - ARM_DX, cx + ARM_DX],
            [arm_y + ARM_DY, arm_y + ARM_DY],
            color=color, lw=2.2, solid_capstyle='round', zorder=6)
    ax.plot([cx, cx - LEG_DX], [y_body, y_body - LEG_H],
            color=color, lw=2.2, solid_capstyle='round', zorder=6)
    ax.plot([cx, cx + LEG_DX], [y_body, y_body - LEG_H],
            color=color, lw=2.2, solid_capstyle='round', zorder=6)
    ax.text(cx, y_body - LEG_H - 0.15, name,
            ha='center', va='top', fontsize=11, fontweight='bold',
            color=color, fontfamily=FONT, zorder=6)
    return head_cy + HEAD_R

admin_head_top = draw_actor_ext(ax, ADMIN_X, ADMIN_Y_ACT, "Administrador", GRAY)

# Dashed lines from Admin to representative UCs (one per section)
admin_targets = [
    (cx_m,  mozo_ys[0],   BLUE),    # Iniciar sesión
    (cx_c,  chef_ys[0],   ORANGE),  # Ver monitor de cocina
    (cx_ca, cajero_ys[0], PURPLE),  # Abrir/cerrar caja
    (cx_ca, cajero_ys[5], PURPLE),  # Ver reportes
]
for uc_cx, uc_y, color in admin_targets:
    ax.plot([ADMIN_X, uc_cx + UCW / 2],
            [ADMIN_Y_ACT + BODY_H + HEAD_R + 0.05,  uc_y],
            color=GRAY, lw=1.0, ls=':', alpha=0.7, zorder=3)

ax.text(ADMIN_X, ADMIN_Y_ACT + BODY_H + HEAD_R * 2 + 0.5,
        "acceso\ntotal", ha='center', va='bottom',
        fontsize=8, color=GRAY, style='italic', fontfamily=FONT)

# ══════════════════════════════════════════════════════════════════════════════
# LEYENDA
# ══════════════════════════════════════════════════════════════════════════════
legend_items = [
    mpatches.Patch(fc=LBLUE,   ec=BLUE,   label='Casos de uso — Mozo'),
    mpatches.Patch(fc=LORANGE, ec=ORANGE, label='Casos de uso — Chef'),
    mpatches.Patch(fc=LPURPLE, ec=PURPLE, label='Casos de uso — Cajero'),
    mpatches.Patch(fc=LGRAY,   ec=GRAY,   label='Administrador (acceso total)'),
]
ax.legend(handles=legend_items, loc='lower center', fontsize=9,
          framealpha=0.95, edgecolor='#D1D5DB', ncol=4,
          bbox_to_anchor=(0.5, 0.0), handlelength=1.5)

# ── Guardar ───────────────────────────────────────────────────────────────────
path = os.path.join(OUT, "diagrama_6_4_casos_uso.png")
fig.savefig(path, dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close(fig)
print(f"Guardado: {path}")
