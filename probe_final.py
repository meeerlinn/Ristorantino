"""
Final verification probe — Ristorantino 5 phases
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
    print(f"\n{'='*50}\n{t}\n{'='*50}")

# Login as admin
code, body = do('GET', '/accounts/login/')
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body).group(1)
code, body = do('POST', '/accounts/login/', {'username':'admin','password':'test1234','csrfmiddlewaretoken':csrf})
CSRF = COOKIES.get('csrftoken', csrf)
ok("LOGIN admin", code == 302, f"code={code}")

# =============================================================
section("PHASE 1 — SALON & AJAX")
# =============================================================
code, body = do('GET', '/salon/')
ok("Salon loads", code == 200)
ok("marcarSucia JS defined", 'marcarSucia' in body)
ok("bloquearMesa JS defined", 'bloquearMesa' in body)
ok("CSRF token in JS", 'const CSRF' in body or "CSRF = '" in body)
ok("Reservar Mesa link (mesa 1 is Libre)", '/reservaciones/crear/' in body or 'Reservar Mesa' in body)

# POST marcar_sucia (AJAX)
code, jbody = do('POST', '/mesa/4/marcar-sucia/',
                 {'csrfmiddlewaretoken': CSRF}, xcsrf=CSRF)
try:
    j = json.loads(jbody)
    ok("POST marcar_sucia -> JSON {ok:True}", j.get('ok') is True, f"resp={j}")
except:
    ok("POST marcar_sucia -> JSON {ok:True}", False, f"code={code}")

# GET marcar_sucia should return 405
code, jbody = do('GET', '/mesa/1/marcar-sucia/')
try:
    j = json.loads(jbody)
    ok("GET marcar_sucia -> 405", code == 405, f"code={code}")
except:
    ok("GET marcar_sucia -> 405", code == 405, f"code={code}")

# POST bloquear_mesa (toggle Libre ↔ Reservada)
code, jbody = do('POST', '/mesa/2/bloquear/',
                 {'csrfmiddlewaretoken': CSRF}, xcsrf=CSRF)
try:
    j = json.loads(jbody)
    ok("POST bloquear_mesa -> JSON {ok:True}", j.get('ok') is True, f"resp={j}")
except:
    ok("POST bloquear_mesa -> JSON {ok:True}", False, f"code={code} body={jbody[:80]}")

# =============================================================
section("PHASE 2 — DASHBOARD")
# =============================================================
code, body = do('GET', '/dashboard/')
ok("Dashboard loads", code == 200, f"code={code}")
ok("KPI total facturado visible", 'Total facturado' in body or 'kpi-total' in body)
ok("Chart.js CDN script tag", 'chart.umd.min.js' in body.lower() or 'cdn.jsdelivr.net/npm/chart.js' in body)
ok("Canvas chartMetodos (doughnut)", 'chartMetodos' in body)
ok("Canvas chartTopRevenue (bar)", 'chartTopRevenue' in body)
ok("Date filter form (fecha_desde)", 'fecha_desde' in body)

code, body = do('GET', '/dashboard/?fecha_desde=2020-01-01&fecha_hasta=2030-12-31')
ok("Dashboard with wide date range (no 500)", code == 200, f"code={code}")

# =============================================================
section("PHASE 3 — HISTORIAL + ANULACION")
# =============================================================
code, body = do('GET', '/pedidos/historial/')
ok("Historial loads", code == 200, f"code={code}")
ok("Columna Fecha Cierre present", 'Fecha' in body and 'Cierre' in body)
ok("Filter form present", 'fecha_desde' in body)
ok("Mozo filter present", 'mozo' in body.lower() or 'Mozo' in body)

# Find Ver links (pattern: /pedidos/<id>/detalle-historial/)
ver_links = re.findall(r'/pedidos/(\d+)/detalle-historial/', body)
ok("Ver (detalle) links present", len(ver_links) > 0, f"found={ver_links}")
ok("Anular button present", 'Anular' in body)

if ver_links:
    pid = ver_links[0]
    code2, body2 = do('GET', f'/pedidos/{pid}/detalle-historial/')
    ok(f"Detalle pedido #{pid} loads", code2 == 200, f"code={code2}")
    ok("Factura nro visible in detalle", 'nro_factura' in body2 or 'Nro' in body2 or 'Factura' in body2)
    ok("IVA section in detalle", 'IVA' in body2 or 'iva' in body2.lower())
    ok("Anular Pedido button in detalle", 'Anular' in body2)
else:
    for lbl in ["Detalle pedido loads","Factura nro","IVA section","Anular button in detalle"]:
        ok(lbl, False, "skipped—no paid pedido found")

# =============================================================
section("PHASE 4 — RESERVACIONES")
# =============================================================
code, body = do('GET', '/reservaciones/')
ok("Reservaciones list loads", code == 200, f"code={code}")
ok("Hoy/Semana toggle present", 'hoy' in body.lower() and 'semana' in body.lower())
ok("Reservacion visible", 'Cliente Test' in body)
ok("Activar button present", 'Activar' in body or 'activar' in body.lower())
ok("Cancelar button present", 'Cancelar' in body or 'cancelar' in body.lower())

code, body = do('GET', '/reservaciones/?vista=semana')
ok("Semana view loads", code == 200)

# Find crear_reservacion links (only for Libre mesas)
code, salon_body = do('GET', '/salon/')
libre_mids = re.findall(r'/reservaciones/crear/(\d+)/', salon_body)
ok("Reservar Mesa link in salon (Libre mesa)", len(libre_mids) > 0, f"mesas={libre_mids}")

if libre_mids:
    mid = libre_mids[0]
    code2, body2 = do('GET', f'/reservaciones/crear/{mid}/')
    ok(f"crear_reservacion form for mesa {mid} loads", code2 == 200, f"code={code2}")
    ok("fecha_reserva input in form", 'fecha_reserva' in body2)
    ok("AJAX buscar clientes JS present", 'buscar' in body2 or 'clientes/buscar' in body2)
else:
    for lbl in ["crear_reservacion loads","fecha_reserva input","AJAX buscar"]:
        ok(lbl, False, "skipped—no Libre mesa found")

# =============================================================
section("PHASE 5 — CLIENTES")
# =============================================================
code, body = do('GET', '/clientes/')
ok("Clientes list loads", code == 200, f"code={code}")
ok("Cliente Test Verificacion visible", 'Cliente Test' in body)
ok("RUC 1234567-8 visible", '1234567' in body)
ok("Editar button present", 'Editar' in body)
ok("Nuevo Cliente button present", 'Nuevo Cliente' in body)

code, body = do('GET', '/clientes/?q=Test')
ok("Search 'Test' returns results", 'Cliente Test' in body)

code, body = do('GET', '/clientes/?q=zzznomatch999')
ok("Search no-match shows message", 'No se encontraron' in body or 'no hay' in body.lower())

# crear_cliente form (was 500, now fixed)
code, body = do('GET', '/clientes/crear/')
ok("crear_cliente form loads (200)", code == 200, f"code={code}")
has_fields = all(f in body for f in ['nombre_razon_social','ruc_ci','telefono','direccion'])
ok("Form has all 4 fields", has_fields)

if code == 200:
    csrf2 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body)
    csrf2 = csrf2.group(1) if csrf2 else CSRF
    # Duplicate RUC
    code2, body2 = do('POST', '/clientes/crear/', {
        'nombre_razon_social': 'Dupe Test',
        'ruc_ci': '1234567-8',
        'csrfmiddlewaretoken': csrf2
    })
    has_err = ('ya existe' in body2.lower() or 'duplicado' in body2.lower() or
               'RUC' in body2 or code2 == 200)
    ok("Duplicate RUC shows error", code2 == 200 and 'ya existe' in body2.lower(),
       f"code={code2} err_in_body={'ya existe' in body2.lower()}")
else:
    ok("Duplicate RUC shows error", False, "skipped—form didn't load")

# Editar cliente
clientes_code, clientes_body = do('GET', '/clientes/')
edit_links = re.findall(r'/clientes/(\d+)/editar/', clientes_body)
if edit_links:
    cid = edit_links[0]
    code3, body3 = do('GET', f'/clientes/{cid}/editar/')
    ok(f"editar_cliente form for cliente {cid} loads", code3 == 200, f"code={code3}")
    ok("editar_cliente shows existing data", 'Cliente Test' in body3 or '1234567' in body3)
else:
    for lbl in ["editar_cliente loads", "editar shows data"]:
        ok(lbl, False, "skipped—no edit links found")

# =============================================================
section("ROLE BLOCKING PROBES")
# =============================================================
# Login as Mozo (gdavalos)
COOKIES.pop('sessionid', None)
code, body = do('GET', '/accounts/login/')
csrf_g = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body).group(1)
code, body = do('POST', '/accounts/login/', {
    'username': 'gdavalos', 'password': 'test1234',
    'csrfmiddlewaretoken': csrf_g
})
ok("Mozo (gdavalos) login", code == 302, f"code={code}")

code, _ = do('GET', '/dashboard/')
ok("Mozo blocked from Dashboard", code in (302, 403), f"code={code}")

code, _ = do('GET', '/pedidos/historial/')
ok("Mozo blocked from Historial", code in (302, 403), f"code={code}")

code, _ = do('GET', '/clientes/')
ok("Mozo blocked from Clientes", code in (302, 403), f"code={code}")

code, _ = do('GET', '/reservaciones/')
ok("Mozo CAN access Reservaciones", code == 200, f"code={code}")

code, _ = do('GET', '/salon/')
ok("Mozo CAN access Salon", code == 200, f"code={code}")

# =============================================================
section("SUMMARY")
# =============================================================
passed = sum(1 for _, v in RESULTS if v)
total = len(RESULTS)
print(f"\nTotal: {passed}/{total} passed")
if passed < total:
    print("FAILURES:")
    for label, v in RESULTS:
        if not v:
            print(f"  ✗ {label}")
if passed == total:
    print("\n  >>> ALL PROBES PASSED — VERIFICATION COMPLETE <<<")
else:
    print(f"\n  {passed}/{total} checks passed")


