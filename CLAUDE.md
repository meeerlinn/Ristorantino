# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Ristorantino** is a Django-based restaurant management system for dining operations: table management, order entry, kitchen display, and fiscal invoicing. Built with Django 6.0.3, PostgreSQL, Bootstrap 5.3.0, and a custom Japandi CSS theme.

## Commands

```bash
# Activate virtual environment (Windows)
env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Database migrations
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Run development server (http://localhost:8000)
python manage.py runserver

# Django shell
python manage.py shell
```

No test suite is configured in this project.

## Architecture

### App Structure
- **`core/`** — Django project config (settings.py, urls.py)
- **`pedidos/`** — All business logic: models, views, urls, templates, admin
- **`static/`** — CSS, JS, images

### Data Model

**Access & Personnel**: `Rol`, `Empleado` — employees linked to Django `User` with a role name (mozo, cajero, chef). Role checks use `user.empleado.rol.nombre`.

**Infrastructure & Menu**: `Sector`, `Mesa` (4 states: Libre/Ocupada/Reservada/Sucia), `Categoria`, `Producto` (stores both `precio_venta` and `costo_insumo` for margin KPIs).

**Orders**: `Cliente`, `Pedido`, `PedidoDetalle` — `PedidoDetalle` snapshots `precio_historico` at order time. `Pedido.actualizar_total()` uses Django F-expressions to sum `cantidad * precio_historico`.

**Kitchen**: `FlujoEstado` — tracks each order item through states (Pendiente → Cocina → Listo → Entregado) with timestamps for FIFO kitchen queue.

**Accounting**: `TipoDocumento`, `Timbrado`, `Caja`, `CajaTimbrado`, `Arqueo`, `DocumentoTributario`, `PedidoDocumento` — full fiscal audit trail linking orders to receipts and cash reconciliation.

### Key Views (`pedidos/views.py`)

| View | Purpose |
|------|---------|
| `salon_principal()` | Table grid by sector; modals for quick actions |
| `abrir_mesa()` | Opens a table → creates `Pedido` with default client; redirects if already occupied |
| `tomar_pedido()` | Order entry screen (comanda.html); two-column layout of menu vs. current order |
| `agregar_producto_ajax()` | AJAX endpoint; increments quantity if item exists, creates new `PedidoDetalle` otherwise; returns JSON |
| `monitor_cocina()` | Kitchen display; items sorted oldest-first (FIFO) |
| `cambiar_estado_cocina()` | Advances `FlujoEstado` for an item |

### Database Configuration
PostgreSQL credentials are hardcoded in `core/settings.py` (postgres/admin @ 127.0.0.1:5432, db: ristorantino). A `db.sqlite3` exists locally but settings point to Postgres.

### Frontend
Templates live in `pedidos/templates/`. Base layout in `base.html` (Bootstrap 5.3 + Japandi CSS variables). `salon.html` uses CSS grid with chair visualizations; `comanda.html` is two-column product/order layout.
