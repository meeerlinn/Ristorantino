# 🍽️ Ristorantino

> Sistema de gestión para restaurantes — Tesis Profesional 2026

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.0.3-092E20?style=flat&logo=django&logoColor=white)](https://djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=flat&logo=bootstrap&logoColor=white)](https://getbootstrap.com)

---

## ✨ Funcionalidades

| Módulo | Descripción |
|--------|-------------|
| 🪑 **Salón** | Grilla de mesas en tiempo real con estados: Libre, Ocupada, Reservada, Sucia |
| 📋 **Comanda** | Toma de pedidos con catálogo de productos, filtros y notas por ítem |
| 👨‍🍳 **Cocina (KDS)** | Monitor de cocina con cola FIFO y auto-refresco cada 20 segundos |
| 💰 **Caja** | Arqueo de caja, apertura/cierre y control de jornada |
| 🧾 **Facturación** | Emisión de documentos tributarios con IVA 10%/5%/Exento |
| 📅 **Reservas** | Gestión de reservaciones por mesa con activación desde el salón |
| 👥 **Clientes** | Directorio con categorías (Casual, Habitual, VIP, Empleado) |
| 📊 **Dashboard** | KPIs, top productos, distribución de pagos y ticket promedio |
| 📄 **Reporte IVA** | Informe mensual exportable a Excel |
| 🗓️ **Cierre del Día** | Reporte Z diario imprimible con desglose por método de pago |

---

## 🛠️ Tecnologías

- **Backend:** Django 6.0.3 (MVT)
- **Base de datos:** PostgreSQL 18
- **Frontend:** Bootstrap 5.3 + CSS Japandi personalizado
- **Autenticación:** Django Auth con roles (Mozo, Cajero, Chef)

---

## 🚀 Instalación

### Prerrequisitos

- Python 3.12+
- PostgreSQL 18
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/meeerlinn/Ristorantino.git
cd Ristorantino

# 2. Crear y activar entorno virtual
python -m venv env

# Windows
env\Scripts\activate

# Linux/Mac
source env/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
# Editar .env con tus credenciales de PostgreSQL

# 5. Crear la base de datos en PostgreSQL
createdb -U postgres ristorantino

# 6. Aplicar migraciones
python manage.py migrate

# 7. Crear superusuario
python manage.py createsuperuser

# 8. Levantar el servidor
python manage.py runserver
```

Abrí el navegador en **http://localhost:8000/salon/**

---

## ⚙️ Variables de entorno

Copiá `.env.example` a `.env` y completá los valores:

```env
DJANGO_SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
DB_NAME=ristorantino
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

---

## 🗂️ Estructura del proyecto

```
Ristorantino/
├── core/               # Configuración Django (settings, urls)
├── pedidos/            # App principal
│   ├── models.py       # Modelos: Mesa, Pedido, Producto, Caja...
│   ├── views.py        # Vistas y endpoints AJAX
│   ├── urls.py         # Rutas
│   ├── templates/      # HTML con Bootstrap 5
│   └── migrations/     # Migraciones de base de datos
├── static/             # CSS, JS, imágenes
├── docs/               # Diagramas y documentación técnica
├── .env.example        # Plantilla de variables de entorno
└── requirements.txt    # Dependencias Python
```

---

## 📐 Modelo de datos

El sistema maneja 18 tablas organizadas en 6 grupos funcionales:

- **Acceso:** `Rol`, `Empleado`
- **Infraestructura:** `Sector`, `Mesa`
- **Menú:** `Categoria`, `Producto`
- **Pedidos:** `Cliente`, `Pedido`, `PedidoDetalle`
- **Cocina:** `FlujoEstado`
- **Fiscal:** `TipoDocumento`, `Timbrado`, `Caja`, `CajaTimbrado`, `Arqueo`, `DocumentoTributario`, `PedidoDocumento`, `ConfigRestaurante`

---

## 📸 Pantallas

<table>
  <tr>
    <td align="center"><b>Salón Principal</b></td>
    <td align="center"><b>Comanda</b></td>
    <td align="center"><b>Monitor de Cocina</b></td>
  </tr>
  <tr>
    <td>Grilla de mesas con estados visuales por color</td>
    <td>Toma de pedidos con catálogo y resumen lateral</td>
    <td>Cola FIFO de ítems para el chef con temporizador</td>
  </tr>
</table>

---

## 👨‍💻 Autor

**Elvis López** — [@meeerlinn](https://github.com/meeerlinn)

Tesis Profesional — Paraguay, 2026

---

> *Desarrollado con Django + amor por la gastronomía paraguaya* 🇵🇾
