# Captura screenshots de todas las pantallas de Ristorantino.
from playwright.sync_api import sync_playwright
import time, os

DEST = r"C:/Users/Merlin/Desktop/Ristorantino capturas/claude"
BASE = "http://localhost:8000"
os.makedirs(DEST, exist_ok=True)

PANTALLAS = [
    ("01_login",             f"{BASE}/accounts/login/",      None),
    ("02_salon",             f"{BASE}/salon/",               None),
    ("03_comanda",           f"{BASE}/mesa/2/abrir/",        None),
    ("04_cocina",            f"{BASE}/cocina/",              None),
    ("05_caja",              f"{BASE}/caja/",                None),
    ("06_cobrar",            f"{BASE}/pedido/4/cobrar/",     None),
    ("07_clientes",          f"{BASE}/clientes/",            None),
    ("08_crear_cliente",     f"{BASE}/clientes/crear/",      None),
    ("09_menu_productos",    f"{BASE}/productos/",           None),
    ("10_crear_producto",    f"{BASE}/productos/crear/",     None),
    ("11_reservaciones",     f"{BASE}/reservaciones/",       None),
    ("13_historial",         f"{BASE}/pedidos/historial/",   None),
    ("14_dashboard",         f"{BASE}/dashboard/",           None),
    ("15_reporte_iva",       f"{BASE}/reporte/iva/",         None),
    ("16_cierre_dia",        f"{BASE}/reporte/z/",           None),
    ("17_configuracion",     f"{BASE}/configuracion/",       None),
    ("18_categorias",        f"{BASE}/categorias/",          None),
    ("19_admin",             f"{BASE}/admin/",               None),
]

def login(page):
    page.goto(f"{BASE}/accounts/login/")
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "ristorantino")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE}/salon/")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    print("Iniciando sesión...")
    login(page)

    for nombre, url, _ in PANTALLAS:
        print(f"  Capturando: {nombre}")
        page.goto(url)
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        path = os.path.join(DEST, f"{nombre}.png")
        page.screenshot(path=path, full_page=True)
        print(f"    -> {path}")

    browser.close()
    print("\nListo. Capturas guardadas en:")
    print(DEST)
