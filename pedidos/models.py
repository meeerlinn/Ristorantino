from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, F

# ==========================================
# 1. MÓDULO DE ACCESO Y PERSONAL
# ==========================================

class Rol(models.Model):
    """
    Define los roles del sistema de acceso.
    Tabla: roles
    Valores esperados: 'Mozo', 'Cajero', 'Chef', 'Administrador'
    Usado por: Empleado → @requiere_rol(*roles)
    """
    nombre = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.nombre

class Empleado(models.Model):
    """
    Perfil de empleado vinculado 1:1 a un usuario Django.
    Tabla: empleados
    Acceso: request.user.empleado.rol.nombre
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='empleado')
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT)
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150)
    ci = models.CharField(max_length=20, unique=True)
    cargo = models.CharField(max_length=100)

    class Meta:
        db_table = 'empleados'

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.rol.nombre})"

# ==========================================
# 2. MÓDULO DE INFRAESTRUCTURA Y MENÚ
# ==========================================

class Sector(models.Model):
    """
    Zona física del restaurante (ej: 'Salón Principal', 'Barra', 'Terraza').
    Tabla: sectores
    Relación: Sector 1→N Mesa
    """
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'sectores'

    def __str__(self):
        return self.nombre

class Mesa(models.Model):
    """
    Mesa física del restaurante con estado operativo.
    Tabla: mesas
    Estados: Libre / Ocupada / Reservada / Sucia
    Relaciones: Mesa N→1 Sector | Mesa 1→N Pedido | Mesa 1→N Reservacion
    """
    ESTADOS_MESA = [
        ('Libre', 'Libre'),
        ('Ocupada', 'Ocupada'),
        ('Reservada', 'Reservada'),
        ('Sucia', 'Sucia/Limpieza'),
    ]

    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='mesas')
    numero_mesa = models.IntegerField(unique=True)
    capacidad = models.IntegerField()
    estado = models.CharField(max_length=50, choices=ESTADOS_MESA, default='Libre')

    class Meta:
        db_table = 'mesas'

    def __str__(self):
        return f"Mesa {self.numero_mesa} ({self.sector.nombre})"

class Categoria(models.Model):
    """
    Categoría del menú (ej: 'Entradas', 'Platos Principales', 'Bebidas').
    Tabla: categorias
    Relación: Categoria 1→N Producto
    """
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'categorias'

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    """
    Ítem del menú con precio y costo para calcular márgenes.
    Tabla: productos
    precio_venta y costo_insumo en Guaraníes (DecimalField sin decimales).
    imagen: subida a /media/productos/ (requiere Pillow instalado).
    disponible=False → no aparece disponible en la comanda para nuevos pedidos.
    stock_actual=None → sin control de stock (ilimitado).
    stock_actual=0    → agotado; se marca disponible=False automáticamente.
    stock_actual>0    → se descuenta al agregar al pedido y se restaura al anular.
    """
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    precio_venta = models.DecimalField(max_digits=15, decimal_places=0)
    costo_insumo = models.DecimalField(max_digits=15, decimal_places=0)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    disponible = models.BooleanField(default=True)
    stock_actual = models.IntegerField(
        null=True, blank=True, default=None,
        help_text='Unidades en stock. Vacío = sin límite (no se controla).'
    )
    TASAS_IVA = [
        (10, 'IVA 10%'),
        (5,  'IVA 5%'),
        (0,  'Exento'),
    ]
    tasa_iva = models.IntegerField(choices=TASAS_IVA, default=10)

    class Meta:
        db_table = 'productos'

    def __str__(self):
        return self.nombre

# ==========================================
# 3. MÓDULO DE CLIENTES Y OPERACIONES
# ==========================================

class Cliente(models.Model):
    """
    Cliente o razón social para facturación.
    Tabla: clientes
    ruc_ci es único; el valor '0' identifica al 'Cliente Ocasional' genérico.
    Relacionado con Pedido y DocumentoTributario para trazabilidad fiscal.
    """
    CATEGORIAS = [
        ('Casual',   'Casual'),
        ('Habitual', 'Habitual'),
        ('VIP',      'VIP'),
        ('Empleado', 'Empleado'),
    ]
    DESCUENTO_POR_CATEGORIA = {
        'Casual':   0,
        'Habitual': 5,
        'VIP':      10,
        'Empleado': 15,
    }

    nombre_razon_social = models.CharField(max_length=255)
    ruc_ci = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='Casual')

    @property
    def descuento_porcentaje(self):
        return self.DESCUENTO_POR_CATEGORIA.get(self.categoria, 0)

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return self.nombre_razon_social

class Pedido(models.Model):
    """
    Cabecera de un pedido en mesa.
    Tabla: pedidos
    Ciclo de vida: estado_pago Pendiente → Pagado (o Anulado).
    total_pedido se recalcula via actualizar_total() con F-expressions.
    descuento se aplica al cobrar; no modifica los precios de los detalles.
    Relaciones: Pedido N→1 Mesa | N→1 User(mozo) | N→1 Cliente
                Pedido 1→N PedidoDetalle | 1→1 DocumentoTributario (via PedidoDocumento)
    """
    ESTADOS_PAGO = [
        ('Pendiente', 'Pendiente'),
        ('Pagado', 'Pagado'),
        ('Anulado', 'Anulado'),
    ]

    METODOS_PAGO = [
        ('Efectivo', 'Efectivo'),
        ('Tarjeta', 'Tarjeta'),
        ('QR', 'QR'),
        ('Mixto', 'Mixto'),
    ]

    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE)
    mozo = models.ForeignKey(User, on_delete=models.PROTECT)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True, db_index=True)
    estado_pago = models.CharField(max_length=50, choices=ESTADOS_PAGO, default='Pendiente')
    total_pedido = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    metodo_pago = models.CharField(max_length=50, choices=METODOS_PAGO, null=True, blank=True)
    descuento = models.DecimalField(max_digits=18, decimal_places=0, default=0)

    class Meta:
        db_table = 'pedidos'
        indexes = [
            models.Index(fields=['fecha_apertura']),
        ]

    def __str__(self):
        return f"Pedido {self.id} - Mesa {self.mesa.numero_mesa}"

    def actualizar_total(self):
        """Calcula el total sumando (cantidad * precio) de todos sus detalles."""
        total = self.detalles.aggregate(
            total_calculado=Sum(F('cantidad') * F('precio_historico'))
        )['total_calculado']
        self.total_pedido = total or 0
        self.save()

class PedidoDetalle(models.Model):
    """
    Línea de ítem en un pedido (producto + cantidad + precio histórico).
    Tabla: pedido_detalle
    precio_historico: se captura automáticamente en save() si es None.
    Esto garantiza que cambios futuros al precio del producto no afecten
    pedidos ya existentes (requisito de auditoría fiscal).
    Relación: PedidoDetalle 1→N FlujoEstado (trail de estados de cocina)
    """
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_historico = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'pedido_detalle'

    def save(self, *args, **kwargs):
        if self.precio_historico is None:
            self.precio_historico = self.producto.precio_venta
        super().save(*args, **kwargs)

# ==========================================
# 4. MÓDULO DE MONITOREO (KPIs)
# ==========================================

class FlujoEstado(models.Model):
    """
    Registro inmutable de cambios de estado en la preparación de un ítem.
    Tabla: flujo_estados
    NUNCA se modifica un registro existente; solo se crean nuevos.
    El estado actual de un ítem es el estado del registro con timestamp más reciente.
    Permite: FIFO en cocina, tiempos de preparación, KPIs de rendimiento.
    Estados: Pendiente → Cocina → Listo → Entregado (o Anulado)
    """
    ESTADOS_PREPARACION = [
        ('Pendiente', 'Pendiente'),
        ('Cocina', 'En Cocina'),
        ('Listo', 'Listo para Entrega'),
        ('Entregado', 'Entregado'),
        ('Anulado', 'Anulado'),
    ]

    pedido_detalle = models.ForeignKey(PedidoDetalle, on_delete=models.CASCADE)
    estado = models.CharField(max_length=100, choices=ESTADOS_PREPARACION)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'flujo_estados'
        indexes = [
            models.Index(fields=['timestamp']),
        ]

# ==========================================
# 5. MÓDULO TRIBUTARIO Y CAJA
# ==========================================

class TipoDocumento(models.Model):
    """
    Tipo de documento fiscal (ej: 'Factura', 'Nota de Crédito').
    Tabla: tipos_documentos
    Administrado desde /admin/.
    """
    nombre = models.CharField(max_length=100) # Factura, Nota de Credito
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = 'tipos_documentos'

    def __str__(self):
        return self.nombre

class Timbrado(models.Model):
    """
    Sello fiscal emitido por la Subsecretaría de Estado de Tributación (SET) de Paraguay.
    Tabla: timbrados
    numero_timbrado: código único asignado por la SET.
    serie: código de establecimiento-punto, ej: '001-001'.
    rango_desde / rango_hasta: numeración secuencial habilitada.
    Administrado desde /admin/. Requiere configuración en CajaTimbrado.
    """
    tipo_doc = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT)
    numero_timbrado = models.CharField(max_length=50)
    fecha_vencimiento = models.DateField()
    serie = models.CharField(max_length=20) # Ej: 001-001
    rango_desde = models.IntegerField()
    rango_hasta = models.IntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'timbrados'

class Caja(models.Model):
    """
    Punto de caja físico (ej: 'Caja 1', 'Barra', 'Terraza').
    Tabla: cajas
    Cada Caja puede tener un Timbrado activo via CajaTimbrado.
    Un Cajero abre un Arqueo asociado a una Caja.
    """
    nombre = models.CharField(max_length=100) # Caja 1, Barra, Terraza
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'cajas'

    def __str__(self):
        return self.nombre

class CajaTimbrado(models.Model):
    """
    Asociación entre una Caja y un Timbrado fiscal.
    Tabla: caja_timbrado
    punto_expedicion: código del punto de emisión (ej: '001').
    Solo los registros con estado='Activo' se usan para generar facturas.
    Administrado desde /admin/.
    """
    ESTADOS_CT = [
        ('Activo', 'Activo'),
        ('Agotado', 'Agotado'),
        ('Vencido', 'Vencido'),
    ]

    caja = models.ForeignKey(Caja, on_delete=models.CASCADE)
    timbrado = models.ForeignKey(Timbrado, on_delete=models.CASCADE)
    punto_expedicion = models.CharField(max_length=10) # Ej: 001
    estado = models.CharField(max_length=50, choices=ESTADOS_CT, default='Activo')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'caja_timbrado'

class Arqueo(models.Model):
    """
    Sesión de caja (turno) de un cajero en una caja física.
    Tabla: arqueos
    monto_apertura: dinero en caja al abrir.
    monto_cierre_sistema: acumulado de ventas cobradas en el turno (auto).
    monto_cierre_real: monto físico contado al cerrar (ingresado por cajero).
    diferencia_arqueo: real - sistema (puede ser negativa = faltante).
    Solo puede haber un arqueo Abierto por usuario a la vez.
    """
    ESTADOS_ARQUEO = [
        ('Abierto', 'Abierto'),
        ('Cerrado', 'Cerrado'),
    ]

    caja = models.ForeignKey(Caja, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_apertura = models.DecimalField(max_digits=18, decimal_places=0)
    monto_cierre_sistema = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    monto_cierre_real = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    diferencia_arqueo = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    estado = models.CharField(max_length=50, choices=ESTADOS_ARQUEO, default='Abierto')

    class Meta:
        db_table = 'arqueos'

class DocumentoTributario(models.Model):
    """
    Factura fiscal generada al cobrar un pedido.
    Tabla: documentos_tributarios
    nro_factura: SERIE-PUNTO-0000001 (generado en cobrar_pedido).
    numero_secuencial: auto-incremento dentro del rango del timbrado.
    IVA: solo se usa total_iva_10 actualmente (tasa 10%); total_iva_5 y
         total_exenta están disponibles para casos especiales.
    Al anular: estado cambia a 'Anulado' y se corrige el arqueo.
    Relacionado con Pedido via PedidoDocumento (tabla puente).
    """
    ESTADOS_DOC = [
        ('Vigente', 'Vigente'),
        ('Anulado', 'Anulado'),
    ]

    METODOS_PAGO = [
        ('Efectivo', 'Efectivo'),
        ('Tarjeta', 'Tarjeta'),
        ('QR', 'QR'),
        ('Mixto', 'Mixto'),
    ]

    timbrado = models.ForeignKey(Timbrado, on_delete=models.PROTECT)
    arqueo = models.ForeignKey(Arqueo, on_delete=models.PROTECT)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    nro_factura = models.CharField(max_length=50)
    numero_secuencial = models.IntegerField(default=1)
    total_exenta = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    total_iva_5 = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    total_iva_10 = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    monto_total = models.DecimalField(max_digits=18, decimal_places=0)
    metodo_pago = models.CharField(max_length=50, choices=METODOS_PAGO, default='Efectivo')
    estado = models.CharField(max_length=50, choices=ESTADOS_DOC, default='Vigente')

    class Meta:
        db_table = 'documentos_tributarios'
        indexes = [
            models.Index(fields=['arqueo', 'estado']),
        ]

class PedidoDocumento(models.Model):
    """
    Tabla puente entre Pedido y DocumentoTributario.
    Tabla: pedido_documento
    estado_vinculo='Activo': factura vigente del pedido.
    estado_vinculo='Corregido': factura fue anulada (corrección contable).
    Permite trazar qué factura corresponde a qué pedido y viceversa.
    """
    ESTADOS_VINCULO = [
        ('Activo', 'Activo'),
        ('Corregido', 'Corregido'),
    ]

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    documento = models.ForeignKey(DocumentoTributario, on_delete=models.CASCADE)
    estado_vinculo = models.CharField(max_length=50, choices=ESTADOS_VINCULO, default='Activo')

    class Meta:
        db_table = 'pedido_documento'

# ==========================================
# 6. MÓDULO DE RESERVACIONES
# ==========================================

class Reservacion(models.Model):
    """
    Reserva de mesa para una fecha y hora específicas.
    Tabla: reservaciones
    Ordenamiento por defecto: fecha_reserva ASC.
    empleado: usuario que registró la reserva (no necesariamente el que atiende).
    Conflicto: se previene crear reservas con menos de 2 horas de diferencia
               para la misma mesa (validado en crear_reservacion view).
    Estados: Confirmada → Completada (al activar mesa) o Cancelada.
    """
    ESTADOS_RESERVA = [
        ('Confirmada', 'Confirmada'),
        ('Cancelada', 'Cancelada'),
        ('Completada', 'Completada'),
    ]

    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name='reservaciones')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    empleado = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha_reserva = models.DateTimeField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    cantidad_personas = models.IntegerField()
    observaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=50, choices=ESTADOS_RESERVA, default='Confirmada')

    class Meta:
        db_table = 'reservaciones'
        ordering = ['fecha_reserva']

    def __str__(self):
        return f"Reserva {self.id} — Mesa {self.mesa.numero_mesa} ({self.fecha_reserva:%d/%m/%Y %H:%M})"


# ==========================================
# 7. CONFIGURACIÓN DEL RESTAURANTE (singleton)
# ==========================================

class ConfiguracionRestaurante(models.Model):
    """
    Configuración global del restaurante. Singleton (siempre id=1).
    Tabla: config_restaurante
    Uso: ConfiguracionRestaurante.objects.get_or_create(id=1)[0]
    Los datos aparecen en el template factura_print.html.
    tasa_iva: 5 o 10 (porcentaje de IVA incluido en precios).
    """
    nombre    = models.CharField(max_length=200, default='Ristorantino')
    ruc       = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=300, blank=True)
    telefono  = models.CharField(max_length=50, blank=True)
    tasa_iva  = models.IntegerField(default=10)  # 5 o 10

    class Meta:
        db_table = 'config_restaurante'

    def __str__(self):
        return self.nombre
