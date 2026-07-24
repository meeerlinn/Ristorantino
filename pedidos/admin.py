from django.contrib import admin
from .models import (
    Rol, Empleado, Sector, Mesa, Categoria, Producto, Cliente, Caja,
    Pedido, PedidoDetalle, FlujoEstado, TipoDocumento, Timbrado, CajaTimbrado,
    Arqueo, DocumentoTributario, PedidoDocumento, Reservacion
)

# Admin para Producto
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_venta', 'disponible')
    list_filter = ('categoria', 'disponible')
    search_fields = ('nombre',)

# Admin para Mesa
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero_mesa', 'sector', 'capacidad', 'estado')
    list_filter = ('sector', 'estado')
    search_fields = ('numero_mesa',)

# Admin para Pedido
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'mesa', 'mozo', 'cliente', 'fecha_apertura', 'estado_pago', 'total_pedido')
    list_filter = ('estado_pago', 'mesa__sector', 'mozo')
    search_fields = ('id', 'mesa__numero_mesa', 'cliente__nombre_razon_social')
    date_hierarchy = 'fecha_apertura'

# Registramos los modelos básicos para empezar a cargar datos
admin.site.register(Rol)
admin.site.register(Empleado)
admin.site.register(Sector)
admin.site.register(Mesa, MesaAdmin)
admin.site.register(Categoria)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Cliente)
admin.site.register(Caja)
admin.site.register(Pedido, PedidoAdmin)
admin.site.register(PedidoDetalle)
admin.site.register(FlujoEstado)
admin.site.register(TipoDocumento)
admin.site.register(Timbrado)
admin.site.register(CajaTimbrado)
admin.site.register(Arqueo)
admin.site.register(DocumentoTributario)
admin.site.register(PedidoDocumento)
admin.site.register(Reservacion)