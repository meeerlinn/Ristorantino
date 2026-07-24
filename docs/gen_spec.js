const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, TableOfContents,
  LevelFormat
} = require('docx');
const fs = require('fs');

// Colors
const C_DARK   = "1B2B3A"; // azul oscuro Japandi
const C_MID    = "2E6DA4"; // azul medio
const C_LIGHT  = "D5E8F0"; // azul claro (header cells)
const C_ACCENT = "C8A96E"; // dorado Japandi
const C_GRAY   = "F5F5F0"; // fondo gris cálido
const C_TEXT   = "2C2C2C"; // texto principal
const C_WHITE  = "FFFFFF";

// Borders reutilizables
const b1 = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: b1, bottom: b1, left: b1, right: b1 };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function hdrCell(text, w) {
  return new TableCell({
    borders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: C_DARK, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      children: [new TextRun({ text, bold: true, color: C_WHITE, size: 20, font: "Arial" })]
    })]
  });
}

function dataCell(text, w, shaded = false) {
  return new TableCell({
    borders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: shaded ? C_GRAY : C_WHITE, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      children: [new TextRun({ text, size: 19, color: C_TEXT, font: "Arial" })]
    })]
  });
}

function codeCell(text, w) {
  return new TableCell({
    borders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: "F0F0EA", type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      children: [new TextRun({ text, size: 18, font: "Courier New", color: "1A1A1A" })]
    })]
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C_ACCENT, space: 4 } },
    children: [new TextRun({ text, font: "Arial", size: 36, bold: true, color: C_DARK })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 80 },
    children: [new TextRun({ text, font: "Arial", size: 28, bold: true, color: C_MID })]
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 60 },
    children: [new TextRun({ text, font: "Arial", size: 24, bold: true, color: C_DARK })]
  });
}

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 80 },
    children: [new TextRun({ text, font: "Arial", size: 20, color: C_TEXT, ...opts })]
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, font: "Arial", size: 20, color: C_TEXT })]
  });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

// ─── Tablas de datos ────────────────────────────────────────────────────────

function tableModelos(title, rows) {
  // cols: Modelo | Campos clave | Descripción  widths: 2200 / 3200 / 3960
  const W = [2200, 3200, 3960];
  const totalW = W.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths: W,
    rows: [
      new TableRow({
        tableHeader: true,
        children: [hdrCell("Modelo", W[0]), hdrCell("Campos clave", W[1]), hdrCell("Descripcion", W[2])]
      }),
      ...rows.map((r, i) => new TableRow({
        children: [
          dataCell(r[0], W[0], i % 2 === 0),
          dataCell(r[1], W[1], i % 2 === 0),
          dataCell(r[2], W[2], i % 2 === 0),
        ]
      }))
    ]
  });
}

function tableVistas() {
  const W = [2400, 2000, 5000];
  const totalW = W.reduce((a, b) => a + b, 0);
  const rows = [
    ["salon_principal()", "GET /salon/", "Grilla de mesas por sector con modales para acciones rapidas"],
    ["abrir_mesa()", "POST /mesa/abrir/", "Abre una mesa, crea Pedido con cliente por defecto; redirige si ya esta ocupada"],
    ["tomar_pedido()", "GET/POST /pedido/<id>/", "Pantalla de ingreso de pedidos (comanda.html), layout dos columnas menu vs pedido"],
    ["agregar_producto_ajax()", "POST /pedido/agregar/", "Endpoint AJAX; incrementa cantidad si el item existe o crea nuevo PedidoDetalle; retorna JSON"],
    ["monitor_cocina()", "GET /cocina/", "Display de cocina; items ordenados por mas antiguos primero (FIFO)"],
    ["cambiar_estado_cocina()", "POST /cocina/estado/", "Avanza FlujoEstado para un item de pedido"],
  ];
  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths: W,
    rows: [
      new TableRow({
        tableHeader: true,
        children: [hdrCell("Vista / Funcion", W[0]), hdrCell("URL / Metodo", W[1]), hdrCell("Descripcion", W[2])]
      }),
      ...rows.map((r, i) => new TableRow({
        children: [
          codeCell(r[0], W[0]),
          dataCell(r[1], W[1], i % 2 === 0),
          dataCell(r[2], W[2], i % 2 === 0),
        ]
      }))
    ]
  });
}

function tableEstados() {
  const W = [2000, 2200, 2200, 3000];
  const totalW = W.reduce((a, b) => a + b, 0);
  const rows = [
    ["Pendiente", "Cocina", "Empleado de cocina acepta el item", "FlujoEstado creado al agregar item al pedido"],
    ["Cocina", "Listo", "El plato esta preparado y listo", "Se registra timestamp; visible en monitor"],
    ["Listo", "Entregado", "Mozo entrega el plato en la mesa", "Item sale del monitor de cocina"],
    ["Entregado", "(final)", "Estado terminal del item", "Se conserva para auditoria y KPIs"],
  ];
  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths: W,
    rows: [
      new TableRow({
        tableHeader: true,
        children: [hdrCell("Estado origen", W[0]), hdrCell("Estado destino", W[1]), hdrCell("Evento", W[2]), hdrCell("Notas", W[3])]
      }),
      ...rows.map((r, i) => new TableRow({
        children: r.map((v, j) => dataCell(v, W[j], i % 2 === 0))
      }))
    ]
  });
}

function tableMesa() {
  const W = [2200, 3400, 3800];
  const totalW = W.reduce((a, b) => a + b, 0);
  const rows = [
    ["Libre", "Mesa disponible para ser asignada", "Estado inicial; el boton 'Abrir Mesa' esta habilitado"],
    ["Ocupada", "Mesa con un pedido activo en curso", "Generado por abrir_mesa(); redirige si ya existe pedido"],
    ["Reservada", "Mesa con reserva pero sin pedido activo", "Gestionado manualmente o por modulo de reservas"],
    ["Sucia", "Mesa liberada pendiente de limpieza", "Transicion post-cierre de pedido; requiere accion del personal"],
  ];
  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths: W,
    rows: [
      new TableRow({
        tableHeader: true,
        children: [hdrCell("Estado", W[0]), hdrCell("Significado", W[1]), hdrCell("Comportamiento del sistema", W[2])]
      }),
      ...rows.map((r, i) => new TableRow({
        children: r.map((v, j) => dataCell(v, W[j], i % 2 === 0))
      }))
    ]
  });
}

function tableStack() {
  const W = [2600, 2800, 4000];
  const totalW = W.reduce((a, b) => a + b, 0);
  const rows = [
    ["Backend framework", "Django 6.0.3", "ORM, autenticacion, admin, rutas, plantillas"],
    ["Base de datos", "PostgreSQL 15+", "127.0.0.1:5432 / db: ristorantino / user: postgres"],
    ["Frontend CSS", "Bootstrap 5.3.0", "Grid responsivo, componentes, utilidades"],
    ["Tema visual", "CSS Japandi personalizado", "Variables CSS con paleta minimalista Japandi"],
    ["Servidor de desarrollo", "Django runserver", "http://localhost:8000"],
    ["Lenguaje", "Python 3.12+", "Entorno virtual en env\\ (Windows)"],
    ["Control de versiones", "Git", "Repositorio local"],
  ];
  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths: W,
    rows: [
      new TableRow({
        tableHeader: true,
        children: [hdrCell("Componente", W[0]), hdrCell("Tecnologia", W[1]), hdrCell("Detalle", W[2])]
      }),
      ...rows.map((r, i) => new TableRow({
        children: r.map((v, j) => dataCell(v, W[j], i % 2 === 0))
      }))
    ]
  });
}

// ─── Documento ───────────────────────────────────────────────────────────────

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      }
    ]
  },
  styles: {
    default: {
      document: { run: { font: "Arial", size: 20, color: C_TEXT } }
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: C_DARK },
        paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: C_MID },
        paragraph: { spacing: { before: 280, after: 80 }, outlineLevel: 1 }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: C_DARK },
        paragraph: { spacing: { before: 200, after: 60 }, outlineLevel: 2 }
      },
    ]
  },
  sections: [
    // ── PORTADA ──────────────────────────────────────────────────────────────
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
        }
      },
      children: [
        // Espacio superior
        new Paragraph({ spacing: { before: 1440, after: 0 }, children: [] }),

        // Linea decorativa superior
        new Paragraph({
          spacing: { before: 0, after: 240 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: C_ACCENT, space: 1 } },
          children: []
        }),

        // Titulo principal
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 480, after: 120 },
          children: [new TextRun({ text: "RISTORANTINO", font: "Arial", size: 80, bold: true, color: C_DARK })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 0, after: 480 },
          children: [new TextRun({ text: "Sistema de Gestion de Restaurante", font: "Arial", size: 36, color: C_MID })]
        }),

        // Subtitulo del documento
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 0, after: 720 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "DDDDDD", space: 4 } },
          children: [new TextRun({ text: "Especificacion Tecnica del Proyecto", font: "Arial", size: 28, bold: true, color: C_ACCENT, italics: true })]
        }),

        new Paragraph({ spacing: { before: 720, after: 0 }, children: [] }),

        // Metadatos
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 120, after: 40 },
          children: [new TextRun({ text: "Version 1.0", font: "Arial", size: 22, color: "666666" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 40, after: 40 },
          children: [new TextRun({ text: "Fecha: 29 de mayo de 2026", font: "Arial", size: 22, color: "666666" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 40, after: 40 },
          children: [new TextRun({ text: "Autor: SG Systems", font: "Arial", size: 22, color: "666666" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 40, after: 40 },
          children: [new TextRun({ text: "Contacto: elvis.lopez@sgsystems.com.py", font: "Arial", size: 22, color: "666666" })]
        }),

        new Paragraph({ spacing: { before: 720, after: 0 }, children: [] }),

        // Linea decorativa inferior
        new Paragraph({
          spacing: { before: 0, after: 0 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: C_ACCENT, space: 1 } },
          children: []
        }),

        pageBreak(),

        // ── TABLA DE CONTENIDOS ───────────────────────────────────────────────
        h1("Tabla de Contenidos"),
        new TableOfContents("Tabla de Contenidos", { hyperlink: true, headingStyleRange: "1-3" }),

        pageBreak(),

        // ── 1. INTRODUCCION ───────────────────────────────────────────────────
        h1("1. Introduccion"),
        h2("1.1 Descripcion General"),
        p("Ristorantino es un sistema de gestion integral para restaurantes desarrollado con Django. Cubre las operaciones diarias del salon: administracion de mesas, toma de pedidos en comanda digital, display de cocina en tiempo real y emision de documentos tributarios con trazabilidad fiscal completa."),
        p("El sistema esta disenado para personal de restaurante (mozos, cajeros, chef) con interfaces diferenciadas por rol, garantizando que cada empleado acceda unicamente a las funciones que le corresponden."),

        h2("1.2 Objetivos del Sistema"),
        bullet("Digitalizar la operativa del salon: apertura de mesas, toma de pedidos y cierre de cuenta."),
        bullet("Proporcionar un monitor de cocina con cola FIFO para optimizar los tiempos de preparacion."),
        bullet("Emitir documentos tributarios (facturas, recibos) con numero de timbrado y trazabilidad de caja."),
        bullet("Registrar KPIs de margen por producto mediante el seguimiento de precio de venta y costo de insumo."),
        bullet("Mantener un historial de arqueos de caja para conciliacion contable."),

        h2("1.3 Alcance"),
        p("El sistema abarca los siguientes modulos funcionales:"),
        bullet("Gestion de mesas y sectores del restaurante."),
        bullet("Ingreso y modificacion de pedidos (comanda digital)."),
        bullet("Flujo de cocina con cambio de estados por item."),
        bullet("Facturacion fiscal con timbrados y tipos de documento."),
        bullet("Administracion de caja y arqueos."),
        bullet("Panel de administracion Django para configuracion del sistema."),

        pageBreak(),

        // ── 2. STACK TECNOLOGICO ──────────────────────────────────────────────
        h1("2. Stack Tecnologico"),
        p("La siguiente tabla resume las tecnologias utilizadas en el proyecto:"),
        new Paragraph({ spacing: { before: 120, after: 120 }, children: [] }),
        tableStack(),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
        h2("2.1 Requisitos del Entorno"),
        bullet("Python 3.12 o superior instalado en el sistema."),
        bullet("PostgreSQL 15+ con una base de datos llamada 'ristorantino' creada previamente."),
        bullet("Node.js no es requerido (Bootstrap se sirve via CDN)."),
        bullet("Sistema operativo Windows (el entorno virtual usa Scripts\\ en lugar de bin\\)."),

        pageBreak(),

        // ── 3. ARQUITECTURA ───────────────────────────────────────────────────
        h1("3. Arquitectura del Sistema"),
        h2("3.1 Patron de Diseno"),
        p("El proyecto sigue el patron MVT (Model-View-Template) de Django, variante del MVC clasico:"),
        bullet("Model: Define la estructura de datos y la logica de negocio (modelos ORM en pedidos/models.py)."),
        bullet("View: Procesa peticiones HTTP y orquesta la logica (vistas en pedidos/views.py)."),
        bullet("Template: Genera el HTML final combinando datos con plantillas (pedidos/templates/)."),

        h2("3.2 Estructura de Directorios"),
        p("La siguiente estructura describe la organizacion del proyecto:"),
        new Paragraph({ spacing: { before: 120, after: 40 }, children: [] }),

        // Tabla de estructura de archivos
        (() => {
          const W = [3200, 6200];
          const totalW = W.reduce((a, b) => a + b, 0);
          const rows = [
            ["ristorantino/", "Raiz del proyecto"],
            ["  core/", "Configuracion global del proyecto Django"],
            ["    settings.py", "Parametros de BD, apps instaladas, templates, static"],
            ["    urls.py", "Enrutamiento principal (incluye pedidos.urls)"],
            ["    wsgi.py / asgi.py", "Entry points de servidor"],
            ["  pedidos/", "Aplicacion principal con toda la logica de negocio"],
            ["    models.py", "Definicion de todos los modelos ORM"],
            ["    views.py", "Vistas HTTP y endpoints AJAX"],
            ["    urls.py", "Rutas de la aplicacion pedidos"],
            ["    admin.py", "Registro de modelos en el panel de administracion"],
            ["    templates/", "Plantillas HTML de la aplicacion"],
            ["      base.html", "Layout base (Bootstrap 5.3 + tema Japandi)"],
            ["      salon.html", "Grilla de mesas con visualizacion de sillas"],
            ["      comanda.html", "Pantalla de toma de pedidos (dos columnas)"],
            ["  static/", "Archivos estaticos del proyecto"],
            ["    css/", "Hojas de estilo personalizadas (tema Japandi)"],
            ["    js/", "Scripts JavaScript del frontend"],
            ["    img/", "Imagenes y recursos graficos"],
            ["  env/", "Entorno virtual Python (no versionado)"],
            ["  requirements.txt", "Dependencias Python del proyecto"],
            ["  manage.py", "Utilidad de administracion de Django"],
          ];
          return new Table({
            width: { size: totalW, type: WidthType.DXA },
            columnWidths: W,
            rows: [
              new TableRow({ tableHeader: true, children: [hdrCell("Ruta", W[0]), hdrCell("Descripcion", W[1])] }),
              ...rows.map((r, i) => new TableRow({
                children: [codeCell(r[0], W[0]), dataCell(r[1], W[1], i % 2 === 0)]
              }))
            ]
          });
        })(),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
        h2("3.3 Configuracion de Base de Datos"),
        p("Las credenciales de conexion a PostgreSQL estan configuradas en core/settings.py:"),
        bullet("Motor: django.db.backends.postgresql"),
        bullet("Host: 127.0.0.1, Puerto: 5432"),
        bullet("Nombre de base de datos: ristorantino"),
        bullet("Usuario: postgres / Contrasena: admin"),
        p("Tambien existe un archivo db.sqlite3 en el directorio raiz para uso local sin PostgreSQL, aunque la configuracion apunta a Postgres por defecto."),

        pageBreak(),

        // ── 4. MODELO DE DATOS ────────────────────────────────────────────────
        h1("4. Modelo de Datos"),
        p("El modelo de datos esta organizado en cinco grupos funcionales que reflejan los distintos dominios del negocio restaurantero."),

        h2("4.1 Acceso y Personal"),
        tableModelos("Personal", [
          ["Rol", "nombre (str)", "Define el rol del empleado dentro del sistema. Valores tipicos: mozo, cajero, chef."],
          ["Empleado", "user (OneToOne -> User), rol (FK -> Rol)", "Extiende el modelo User de Django con un rol. El acceso se verifica con user.empleado.rol.nombre."],
        ]),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
        h2("4.2 Infraestructura y Menu"),
        tableModelos("Infraestructura", [
          ["Sector", "nombre (str)", "Agrupa mesas por zona del restaurante (Ej: salon principal, terraza, privado)."],
          ["Mesa", "numero, sector (FK), estado (choices)", "Unidad fisica del restaurante. Cuatro estados: Libre, Ocupada, Reservada, Sucia."],
          ["Categoria", "nombre (str)", "Clasificacion de productos del menu (Ej: Entradas, Platos principales, Bebidas)."],
          ["Producto", "nombre, categoria (FK), precio_venta, costo_insumo, activo", "Item del menu. Almacena precio_venta y costo_insumo para calcular KPIs de margen bruto."],
        ]),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
        h2("4.3 Pedidos"),
        tableModelos("Pedidos", [
          ["Cliente", "nombre, telefono, email", "Informacion del cliente. Un cliente por defecto se asigna al abrir una mesa sin datos."],
          ["Pedido", "mesa (FK), cliente (FK), estado, total, fecha_apertura", "Pedido activo en una mesa. El metodo actualizar_total() usa F-expressions de Django para sumar cantidad * precio_historico."],
          ["PedidoDetalle", "pedido (FK), producto (FK), cantidad, precio_historico", "Linea de detalle del pedido. precio_historico guarda un snapshot del precio al momento del pedido para evitar que cambios futuros en Producto afecten pedidos anteriores."],
        ]),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
        h2("4.4 Cocina"),
        tableModelos("Cocina", [
          ["FlujoEstado", "detalle (FK -> PedidoDetalle), estado (choices), timestamp_creacion, timestamp_cambio", "Rastrea cada item de pedido a traves de los estados de cocina con marca de tiempo. Permite cola FIFO ordenando por timestamp_creacion ascendente."],
        ]),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
        h2("4.5 Contabilidad y Documentos Tributarios"),
        tableModelos("Contabilidad", [
          ["TipoDocumento", "nombre, codigo (str)", "Define los tipos de comprobante fiscal (Factura, Recibo, Nota de credito, etc.)."],
          ["Timbrado", "numero, fecha_inicio, fecha_fin, activo", "Numero de timbrado habilitado por la autoridad fiscal. Controla la vigencia de la emision de documentos."],
          ["Caja", "nombre, saldo_inicial, activo", "Representa una caja registradora fisica. Puede asociarse a multiples timbrados."],
          ["CajaTimbrado", "caja (FK), timbrado (FK), numero_desde, numero_hasta, ultimo_numero", "Vincula una caja a un timbrado con el rango de numeracion autorizado."],
          ["Arqueo", "caja (FK), fecha, saldo_apertura, saldo_cierre, responsable (FK -> Empleado)", "Registro de conciliacion de caja al inicio y cierre del turno."],
          ["DocumentoTributario", "tipo (FK), caja_timbrado (FK), numero, fecha, total, cliente (FK)", "Comprobante fiscal emitido. Vincula el pedido al timbrado, numero correlativo y cliente para auditoria."],
          ["PedidoDocumento", "pedido (FK), documento (FK)", "Tabla puente que vincula un Pedido con su DocumentoTributario correspondiente."],
        ]),

        pageBreak(),

        // ── 5. ESTADOS DE MESA ────────────────────────────────────────────────
        h1("5. Estados de Mesa"),
        p("Cada mesa transita por los siguientes estados durante su ciclo de vida operativo:"),
        new Paragraph({ spacing: { before: 120, after: 120 }, children: [] }),
        tableMesa(),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
        p("El diagrama de transicion simplificado es el siguiente:"),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({
            text: "Libre  ->  [abrir_mesa()]  ->  Ocupada  ->  [cerrar pedido]  ->  Sucia  ->  [limpiar]  ->  Libre",
            font: "Courier New", size: 19, color: C_DARK
          })]
        }),
        p("La transicion a Reservada puede originarse desde Libre, gestionada por el modulo de reservas o por accion manual del administrador."),

        pageBreak(),

        // ── 6. FLUJO DE COCINA ────────────────────────────────────────────────
        h1("6. Flujo de Cocina"),
        h2("6.1 Estados del FlujoEstado"),
        p("Cada item (PedidoDetalle) genera un registro FlujoEstado que avanza secuencialmente. La vista monitor_cocina() muestra los items ordenados por timestamp_creacion ascendente (FIFO) para que los pedidos mas antiguos se atiendan primero."),
        new Paragraph({ spacing: { before: 120, after: 120 }, children: [] }),
        tableEstados(),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
        h2("6.2 Diagrama de Flujo"),
        new Paragraph({
          spacing: { before: 120, after: 60 },
          children: [new TextRun({ text: "[Item creado]", font: "Courier New", size: 18, color: C_DARK })]
        }),
        new Paragraph({
          spacing: { before: 0, after: 0 },
          children: [new TextRun({ text: "     |", font: "Courier New", size: 18, color: C_MID })]
        }),
        new Paragraph({
          spacing: { before: 0, after: 0 },
          children: [new TextRun({ text: "     v", font: "Courier New", size: 18, color: C_MID })]
        }),
        new Paragraph({
          spacing: { before: 0, after: 0 },
          children: [new TextRun({ text: " PENDIENTE  -->  COCINA  -->  LISTO  -->  ENTREGADO", font: "Courier New", size: 18, color: C_DARK })]
        }),
        new Paragraph({
          spacing: { before: 0, after: 120 },
          children: [new TextRun({ text: "             (chef)       (chef)    (mozo)", font: "Courier New", size: 18, color: "888888" })]
        }),

        h2("6.3 Logica de cambiar_estado_cocina()"),
        bullet("Recibe el ID del FlujoEstado y determina el siguiente estado en la secuencia."),
        bullet("Actualiza el campo estado y registra el timestamp_cambio con la hora actual."),
        bullet("Retorna una respuesta JSON con el nuevo estado para actualizar la UI sin recargar la pagina."),
        bullet("Los items en estado 'Entregado' desaparecen del monitor de cocina."),

        pageBreak(),

        // ── 7. VISTAS Y ENDPOINTS ─────────────────────────────────────────────
        h1("7. Vistas y Endpoints"),
        p("Las siguientes vistas componen la interfaz funcional del sistema. Todas residen en pedidos/views.py y estan enrutadas desde pedidos/urls.py."),
        new Paragraph({ spacing: { before: 120, after: 120 }, children: [] }),
        tableVistas(),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
        h2("7.1 Endpoint AJAX: agregar_producto_ajax()"),
        p("Este endpoint es el nucleo de la comanda digital. Su logica de negocio es:"),
        bullet("Recibe el ID del pedido y el ID del producto via POST."),
        bullet("Busca si ya existe un PedidoDetalle para ese producto en el pedido activo."),
        bullet("Si existe: incrementa el campo 'cantidad' en 1 y llama a actualizar_total()."),
        bullet("Si no existe: crea un nuevo PedidoDetalle con cantidad=1 y crea el FlujoEstado inicial en estado 'Pendiente'."),
        bullet("Retorna un objeto JSON con los datos actualizados del detalle para refrescar la UI sin recargar."),

        pageBreak(),

        // ── 8. FRONTEND ───────────────────────────────────────────────────────
        h1("8. Frontend y Plantillas"),
        h2("8.1 Layout Base (base.html)"),
        p("Todas las vistas heredan de base.html, que incluye:"),
        bullet("Bootstrap 5.3.0 via CDN para el sistema de grilla, componentes y utilidades."),
        bullet("Variables CSS personalizadas del tema Japandi (paleta minimalista con tonos neutros, madera y ceramica)."),
        bullet("Barra de navegacion con acceso rapido segun el rol del usuario autenticado."),
        bullet("Bloque de mensajes Django para notificaciones de acciones (alertas Bootstrap)."),

        h2("8.2 Salon Principal (salon.html)"),
        p("La vista del salon utiliza CSS Grid para renderizar las mesas con visualizacion de sillas:"),
        bullet("Cada mesa se representa como una tarjeta con color segun su estado (verde=Libre, rojo=Ocupada, amarillo=Reservada, gris=Sucia)."),
        bullet("Las sillas se dibujan alrededor de la mesa usando posicionamiento CSS absoluto."),
        bullet("Modales Bootstrap permiten acciones rapidas (abrir mesa, ver pedido) sin navegar a otra pagina."),

        h2("8.3 Comanda (comanda.html)"),
        p("La pantalla de toma de pedidos usa un layout de dos columnas:"),
        bullet("Columna izquierda: catalogo de productos agrupados por categoria, con boton de agregar."),
        bullet("Columna derecha: resumen del pedido actual con cantidades, precios historicos y total acumulado."),
        bullet("La interaccion usa fetch() de JavaScript para llamar a agregar_producto_ajax() y actualizar la columna derecha sin recargar la pagina."),

        pageBreak(),

        // ── 9. AUTENTICACION Y ROLES ──────────────────────────────────────────
        h1("9. Autenticacion y Control de Acceso"),
        h2("9.1 Modelo de Autenticacion"),
        p("El sistema extiende el modelo de autenticacion nativo de Django:"),
        bullet("Cada empleado tiene un User de Django con username y password para el login."),
        bullet("El modelo Empleado esta vinculado al User mediante una relacion OneToOne."),
        bullet("El rol del empleado se accede con la expresion: user.empleado.rol.nombre"),

        h2("9.2 Roles del Sistema"),
        (() => {
          const W = [2200, 3200, 4000];
          const totalW = W.reduce((a, b) => a + b, 0);
          const rows = [
            ["mozo", "Personal de salon", "Abrir mesas, tomar pedidos, marcar items como entregados"],
            ["cajero", "Personal de caja", "Emitir documentos tributarios, gestionar caja y arqueos"],
            ["chef", "Personal de cocina", "Ver monitor de cocina, cambiar estados de items (Pendiente->Cocina->Listo)"],
          ];
          return new Table({
            width: { size: totalW, type: WidthType.DXA },
            columnWidths: W,
            rows: [
              new TableRow({ tableHeader: true, children: [hdrCell("Rol", W[0]), hdrCell("Descripcion", W[1]), hdrCell("Acciones permitidas", W[2])] }),
              ...rows.map((r, i) => new TableRow({ children: r.map((v, j) => dataCell(v, W[j], i % 2 === 0)) }))
            ]
          });
        })(),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
        p("Las vistas aplican el decorador @login_required de Django y verifican el rol segun la logica de negocio de cada funcion."),

        pageBreak(),

        // ── 10. COMANDOS DE OPERACION ─────────────────────────────────────────
        h1("10. Comandos de Operacion"),
        h2("10.1 Configuracion Inicial"),
        (() => {
          const W = [3600, 5800];
          const totalW = W.reduce((a, b) => a + b, 0);
          const rows = [
            ["env\\Scripts\\activate", "Activa el entorno virtual Python (Windows)"],
            ["pip install -r requirements.txt", "Instala todas las dependencias del proyecto"],
            ["python manage.py makemigrations", "Genera archivos de migracion a partir de los modelos"],
            ["python manage.py migrate", "Aplica las migraciones a la base de datos PostgreSQL"],
            ["python manage.py showmigrations", "Muestra el estado de todas las migraciones"],
            ["python manage.py createsuperuser", "Crea un usuario administrador para el panel de Django"],
            ["python manage.py runserver", "Inicia el servidor de desarrollo en http://localhost:8000"],
            ["python manage.py shell", "Abre la shell interactiva de Django para pruebas"],
          ];
          return new Table({
            width: { size: totalW, type: WidthType.DXA },
            columnWidths: W,
            rows: [
              new TableRow({ tableHeader: true, children: [hdrCell("Comando", W[0]), hdrCell("Descripcion", W[1])] }),
              ...rows.map((r, i) => new TableRow({ children: [codeCell(r[0], W[0]), dataCell(r[1], W[1], i % 2 === 0)] }))
            ]
          });
        })(),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
        h2("10.2 Panel de Administracion"),
        p("Django Admin esta disponible en http://localhost:8000/admin/ para usuarios con is_staff=True. Desde alli se pueden gestionar todos los modelos: empleados, mesas, productos, categorias, timbrados, documentos tributarios y arqueos."),

        pageBreak(),

        // ── 11. GLOSARIO ──────────────────────────────────────────────────────
        h1("11. Glosario"),
        (() => {
          const W = [2800, 6600];
          const totalW = W.reduce((a, b) => a + b, 0);
          const rows = [
            ["Comanda", "Documento o pantalla donde el mozo registra los pedidos de una mesa."],
            ["FIFO", "First In, First Out. Los pedidos mas antiguos se atienden primero en la cola de cocina."],
            ["Timbrado", "Numero habilitado por la SET (Paraguay) para la emision de comprobantes fiscales."],
            ["Arqueo", "Conteo y conciliacion del dinero en caja al inicio o cierre del turno."],
            ["FlujoEstado", "Entidad que registra el estado actual y el historial de transiciones de un item de pedido."],
            ["precio_historico", "Snapshot del precio de venta al momento de crear el detalle del pedido. Inmutable ante cambios futuros en el catalogo."],
            ["F-expression", "Expresion de Django ORM que referencia valores de columna directamente en la base de datos, evitando cargar datos a Python."],
            ["MVT", "Model-View-Template. Patron arquitectonico de Django (variante de MVC)."],
            ["ORM", "Object-Relational Mapper. Capa de abstraccion de Django que mapea clases Python a tablas SQL."],
            ["Bootstrap", "Framework CSS para diseno responsivo. Version 5.3.0 usada via CDN."],
            ["Japandi", "Estilo decorativo que fusiona lo japones y escandinavo: minimalismo, tonos neutros, materiales naturales."],
          ];
          return new Table({
            width: { size: totalW, type: WidthType.DXA },
            columnWidths: W,
            rows: [
              new TableRow({ tableHeader: true, children: [hdrCell("Termino", W[0]), hdrCell("Definicion", W[1])] }),
              ...rows.map((r, i) => new TableRow({ children: r.map((v, j) => dataCell(v, W[j], i % 2 === 0)) }))
            ]
          });
        })(),

        new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }),
      ]
    }
  ]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:\\Proyecto\\docs\\especificacion_tecnica_ristorantino.docx", buffer);
  console.log("Documento generado correctamente.");
});
