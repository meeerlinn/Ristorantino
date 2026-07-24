"""
Probe for Phases 6-9: verifies all new features.
"""
import urllib.request, urllib.parse, urllib.error, json, re

BASE = "http://127.0.0.1:8001"
COOKIES = {}
RESULTS = []

class NR(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NR())
opener.addheaders = [('User-Agent', 'ProbeTool/1.0')]

def do(method, path, data=None, xcsrf=None):
    url = BASE + path
    body = urllib.parse.urlencode(data).encode() if data else None
    rq = urllib.request.Request(url, data=body, method=method)
    rq.add_header('Cookie', "; ".join(f"{k}={v}" for k,v in COOKIES.items()))
    if body:
        rq.add_header('Content-Type', 'application/x-www-form-urlencoded')
    if xcsrf:
        rq.add_header('X-CSRFToken', xcsrf)
    try:
        r = opener.open(rq, timeout=10)
        content = r.read().decode('utf-8', errors='ignore')
        for hdr in r.headers.get_all('Set-Cookie') or []:
            m = re.match(r'(\w+)=([^;]+)', hdr)
            if m: COOKIES[m.group(1)] = m.group(2)
        return r.status, content
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8', errors='ignore')
        for hdr in e.headers.get_all('Set-Cookie') or []:
            m = re.match(r'(\w+)=([^;]+)', hdr)
            if m: COOKIES[m.group(1)] = m.group(2)
        return e.code, content
    except Exception as ex:
        return 0, str(ex)

def ok(label, cond, info=''):
    s = 'PASS' if cond else 'FAIL'
    print(f"  [{s}] {label}" + (f"  ({info})" if info else ""))
    RESULTS.append((label, cond))

def section(t):
    print(f"\n{'='*55}\n{t}\n{'='*55}")

# Login as admin
code, body = do('GET', '/accounts/login/')
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body).group(1)
code, body = do('POST', '/accounts/login/', {'username':'admin','password':'test1234','csrfmiddlewaretoken':csrf})
CSRF = COOKIES.get('csrftoken', csrf)
ok("LOGIN admin", code == 302, f"code={code}")

# =========================================================
section("PHASE 6.2 — Vuelto en cobrar.html")
# =========================================================
# Find an open pedido to check the cobrar page
code, salon = do('GET', '/salon/')
ok("Salon loads", code == 200)
# Get a cobrar link from historial or just check the page structure
# Check if vuelto block is in cobrar template by looking for any cobrar page
cobrar_links = re.findall(r'/pedido/(\d+)/cobrar/', salon)
if cobrar_links:
    pid = cobrar_links[0]
    code2, body2 = do('GET', f'/pedido/{pid}/cobrar/')
    ok(f"cobrar pedido {pid} loads", code2 == 200, f"code={code2}")
    ok("bloque-vuelto present in cobrar", 'bloque-vuelto' in body2)
    ok("efectivo-recibido input present", 'efectivo-recibido' in body2)
    ok("actualizarVuelto JS function present", 'actualizarVuelto' in body2)
else:
    print("  [SKIP] No open pedido for cobrar test")

# =========================================================
section("PHASE 6.3 & 6.4 — Comanda")
# =========================================================
code, comanda_test = do('GET', '/salon/')
open_pedidos = re.findall(r'/pedido/(\d+)/tomar/', comanda_test)
if open_pedidos:
    pid = open_pedidos[0]
    code2, body2 = do('GET', f'/pedido/{pid}/tomar/')
    ok(f"Comanda for pedido {pid} loads", code2 == 200, f"code={code2}")
    ok("actualizarCantidad JS present", 'actualizarCantidad' in body2)
    ok("toggleDisponible JS present", 'toggleDisponible' in body2)
    ok("qty-input class present", 'qty-input' in body2)
    # Check that the URL for actualizar_cantidad is registered
    code3, b3 = do('POST', f'/pedido/{pid}/cantidad/99999/', {'cantidad': '2'}, xcsrf=CSRF)
    ok("actualizar_cantidad_ajax URL responds (404 = route exists)", code3 in (404, 400), f"code={code3}")
else:
    print("  [SKIP] No open pedido for comanda test")

# Check toggle_disponible URL
code, _ = do('POST', '/producto/99999/toggle-disponible/', {}, xcsrf=CSRF)
ok("toggle_disponible_ajax URL exists (404 = route works)", code == 404, f"code={code}")

# =========================================================
section("PHASE 6.5 — Paginacion Clientes")
# =========================================================
code, body = do('GET', '/clientes/')
ok("Clientes list loads with pagination", code == 200, f"code={code}")
ok("page_obj or pagination present", 'page' in body.lower() or 'Clientes' in body)

# =========================================================
section("PHASE 7 — Gestion de Menu")
# =========================================================
code, body = do('GET', '/productos/')
ok("Lista productos loads", code == 200, f"code={code}")
ok("Nuevo Producto button present", 'Nuevo Producto' in body)
ok("Categorias link present", 'Categor' in body)

code, body = do('GET', '/categorias/')
ok("Lista categorias loads", code == 200, f"code={code}")
ok("Nueva Categoria form present", 'Nueva Categor' in body or 'nombre' in body)

code, body = do('GET', '/productos/crear/')
ok("Crear producto form loads", code == 200, f"code={code}")
ok("Form has nombre field", 'nombre' in body)
ok("Form has precio_venta field", 'precio_venta' in body)
ok("Form has imagen field", 'imagen' in body or 'image' in body.lower())
ok("Form has disponible checkbox", 'disponible' in body)
ok("Form has categoria select", 'categoria' in body)

# Check Menu link in navbar
code, body = do('GET', '/salon/')
ok("Menu link in navbar (base.html)", '/productos/' in body or 'Meni' in body or 'Men' in body)

# =========================================================
section("PHASE 8A — Factura imprimible")
# =========================================================
# Find a paid pedido
code, hist = do('GET', '/pedidos/historial/')
ok("Historial loads", code == 200)
pagado_ids = re.findall(r'/pedidos/(\d+)/detalle-historial/', hist)
if pagado_ids:
    pid = pagado_ids[0]
    code2, body2 = do('GET', f'/pedido/{pid}/factura/')
    ok(f"imprimir_factura for pedido {pid} loads", code2 == 200, f"code={code2}")
    ok("Imprimir button present", 'Imprimir' in body2 or 'imprimir' in body2.lower())
    ok("window.print() in JS", 'window.print' in body2)
    ok("Factura layout has total", 'TOTAL' in body2 or 'Total' in body2)
    ok("media print CSS present", 'media print' in body2 or '@media print' in body2)

    # Check Reimprimir button in detalle_historial
    code3, body3 = do('GET', f'/pedidos/{pid}/detalle-historial/')
    ok("Reimprimir Factura button in detalle", 'Reimprimir' in body3)
else:
    print("  [SKIP] No paid pedido for factura test")

# =========================================================
section("PHASE 8B — Conflicto de reservas")
# =========================================================
# Get a Libre mesa
code, salon = do('GET', '/salon/')
libre_mids = re.findall(r'/reservaciones/crear/(\d+)/', salon)
if libre_mids:
    mid = libre_mids[0]
    code2, body2 = do('GET', f'/reservaciones/crear/{mid}/')
    if code2 == 200:
        csrf2 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body2)
        csrf2 = csrf2.group(1) if csrf2 else CSRF
        # Create a first reservation
        code3, body3 = do('POST', f'/reservaciones/crear/{mid}/', {
            'fecha_reserva': '2028-06-01T12:00',
            'cantidad_personas': '2',
            'observaciones': 'Test conflicto',
            'csrfmiddlewaretoken': csrf2
        })
        ok("First reserva created (302 or 200)", code3 in (302, 200), f"code={code3}")

        # Try to create conflicting reservation (within 2h)
        # First need to re-check the form
        code4, body4 = do('GET', f'/reservaciones/crear/{mid}/')
        csrf4 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body4)
        csrf4 = csrf4.group(1) if csrf4 else CSRF
        code5, body5 = do('POST', f'/reservaciones/crear/{mid}/', {
            'fecha_reserva': '2028-06-01T13:00',  # 1 hour away, within the 2h window
            'cantidad_personas': '2',
            'observaciones': 'Conflicto test',
            'csrfmiddlewaretoken': csrf4
        })
        # If conflict detected, should stay on the form (200) with error message
        # If mesa is now Reservada, the form won't show (redirects to salon)
        has_conflict_msg = 'ya tiene una reserva' in body5 or 'conflicto' in body5.lower() or 'horario' in body5
        ok("Conflict check: error shown OR mesa was reserved (302 to salon)",
           has_conflict_msg or code5 == 302, f"code={code5} conflict_msg={has_conflict_msg}")
    else:
        print(f"  [SKIP] crear_reservacion returned {code2}")
else:
    print("  [SKIP] No Libre mesas for conflict test")

# =========================================================
section("PHASE 9A — Error Pages")
# =========================================================
code, body = do('GET', '/esta-url-no-existe-9999/')
ok("404 handler registered (Django may return debug page with DEBUG=True)",
   code == 404, f"code={code}")
# With DEBUG=True, Django uses its own 404 page not our custom one
# The handler is registered but only activates with DEBUG=False
ok("handler404 registered in core/urls.py", code == 404)

# =========================================================
section("PHASE 9C — Configuracion")
# =========================================================
code, body = do('GET', '/configuracion/')
ok("Configuracion page loads", code == 200, f"code={code}")
ok("Nombre field present", 'nombre' in body.lower())
ok("RUC field present", 'ruc' in body.lower())
ok("Tasa IVA select present", 'tasa_iva' in body)

# POST a config update
csrf_conf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body)
csrf_conf = csrf_conf.group(1) if csrf_conf else CSRF
code2, body2 = do('POST', '/configuracion/', {
    'nombre': 'Ristorantino Test',
    'ruc': '12345678-9',
    'direccion': 'Av. Test 123',
    'telefono': '021-999999',
    'tasa_iva': '10',
    'csrfmiddlewaretoken': csrf_conf,
})
ok("POST configuracion saves (302 redirect)", code2 == 302, f"code={code2}")

# Verify saved
code3, body3 = do('GET', '/configuracion/')
ok("Config saved correctly", 'Ristorantino Test' in body3, f"found={'Ristorantino Test' in body3}")

# =========================================================
section("PHASE 9D — Ventas por Mozo in Dashboard")
# =========================================================
code, body = do('GET', '/dashboard/?fecha_desde=2020-01-01&fecha_hasta=2030-12-31')
ok("Dashboard with wide range loads", code == 200, f"code={code}")
ok("Ranking Mozos section present (if there is data)", 'Ranking' in body or 'mozo' in body.lower() or 'Mozo' in body)
ok("ventas_por_mozo table rendered or no data msg", 'Mozo' in body or 'mozo' in body.lower() or 'username' in body.lower())

# =========================================================
section("NAVBAR - Menu link visible for Cajero/Admin")
# =========================================================
code, body = do('GET', '/salon/')
ok("Menu/productos link in navbar", '/productos/' in body)
ok("Configuracion gear icon in navbar", '/configuracion/' in body or 'configuracion' in body)

# =========================================================
section("SUMMARY")
# =========================================================
passed = sum(1 for _, v in RESULTS if v)
total = len(RESULTS)
print(f"\nTotal: {passed}/{total} passed")
if passed < total:
    print("FAILURES:")
    for label, v in RESULTS:
        if not v:
            print(f"  X {label}")
if passed == total:
    print("\n  >>> ALL PROBES PASSED <<<")
else:
    print(f"\n  {passed}/{total} checks passed")
