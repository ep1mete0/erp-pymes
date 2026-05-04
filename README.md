# Prometheus Labs — ERP Inteligente para Minimarkets

> Propuesta de Producto Mínimo Viable (PMV)
>
> **Proyecto:** ERP para supermercado local
> **Cliente objetivo:** Minimarket con productos chilenos e importados
> **Estado:** Etapa de levantamiento de requerimientos

---

# 1. Visión del proyecto

Desarrollar una plataforma de gestión diseñada específicamente para supermercados pequeños y medianos, permitiendo centralizar las operaciones diarias del negocio, reducir pérdidas, mejorar el control del inventario y aumentar la capacidad de toma de decisiones.

Este sistema no busca ser un software genérico, sino una solución pensada para la realidad del comercio local.

## Objetivos principales

* Tener control total del negocio en tiempo real
* Reducir pérdidas por quiebres de stock
* Mejorar la rotación de productos
* Automatizar tareas repetitivas
* Mejorar la comunicación con clientes frecuentes
* Preparar el negocio para crecimiento futuro

---

# 2. Información que necesitamos del cliente para iniciar

Antes de comenzar el desarrollo, necesitamos comprender cómo opera actualmente el negocio.

## Información general del negocio

### Identidad del negocio

* Nombre comercial
* Dirección principal
* Horarios de funcionamiento
* Cantidad de sucursales (si aplica)
* Cantidad de cajas activas

### Operación diaria

* Número aproximado de ventas por día
* Horarios con mayor flujo de clientes
* Métodos de pago aceptados
* Uso actual de software o procesos manuales

### Catálogo de productos

Necesitamos conocer:

* Cantidad aproximada de productos
* Categorías principales
* Productos importados
* Productos perecibles
* Productos vendidos por unidad, peso o volumen
* Productos con alta rotación

### Proveedores

* Lista de proveedores principales
* Frecuencia de reposición
* Proveedores nacionales e internacionales

### Gestión de clientes

* ¿Existen clientes frecuentes?
* ¿Se manejan descuentos?
* ¿Se manejan pedidos por WhatsApp?
* ¿Se realizan reservas de productos?

---

# 3. PMV — Funcionalidades iniciales

## Módulo de ventas

Permite registrar cada venta realizada en caja.

### Incluye

* Registro rápido de productos
* Búsqueda por nombre o código
* Gestión de carrito de compra
* Aplicación de descuentos
* Registro de método de pago
* Cierre diario de caja

### Valor para el negocio

* Menos errores en caja
* Mayor velocidad de atención
* Historial completo de ventas

---

## Módulo de inventario

Control inteligente del stock del negocio.

### Incluye

* Registro de entradas de mercadería
* Registro automático de salidas por venta
* Control de stock mínimo
* Control de fechas de vencimiento
* Identificación de productos con baja rotación

### Valor para el negocio

* Menos pérdidas
* Mejor reposición
* Mejor planificación de compras

---

## Módulo de proveedores

Permite gestionar las compras del negocio.

### Incluye

* Registro de proveedores
* Historial de compras
* Seguimiento de costos
* Comparación de precios

### Valor para el negocio

* Mejor negociación
* Control de márgenes

---

## Módulo de reportes gerenciales

Información clara para tomar decisiones.

### Indicadores iniciales

* Ventas del día
* Productos más vendidos
* Productos menos vendidos
* Productos próximos a agotarse
* Categorías más rentables
* Horarios de mayor venta

---

# 4. Gestión de personal, roles y control operativo

Uno de los puntos más sensibles en un negocio retail es poder delegar la operación con confianza cuando el dueño no está presente.

El sistema incluirá herramientas para garantizar transparencia, trazabilidad y control de cada operación realizada por el personal.

## Gestión de usuarios y permisos

Cada colaborador tendrá acceso con credenciales individuales.

### Roles iniciales

#### Administrador (Dueño)

Podrá:

* Visualizar información completa del negocio
* Configurar precios
* Autorizar descuentos especiales
* Aprobar anulaciones
* Gestionar usuarios
* Revisar utilidades y reportes estratégicos
* Recibir alertas automáticas

#### Cajero

Podrá:

* Registrar ventas
* Consultar productos
* Abrir y cerrar caja
* Procesar pagos
* Consultar historial de ventas propias

#### Supervisor

Podrá:

* Autorizar devoluciones
* Realizar ajustes de inventario con justificación
* Resolver incidencias operativas
* Supervisar cajas activas

---

## Control de turnos y cajas

Cada turno quedará registrado.

### Incluye

* Apertura de caja con monto inicial
* Registro de responsable del turno
* Cierre de caja
* Conciliación entre ventas registradas y efectivo real
* Detección de diferencias

### Valor para el negocio

* Mayor control del efectivo
* Menor riesgo de pérdidas
* Mayor transparencia operativa

---

## Bitácora de auditoría

Todas las acciones importantes quedarán registradas.

### Incluye

* Cambios de precios
* Descuentos aplicados
* Anulación de ventas
* Ajustes de inventario
* Eliminación o modificación de productos
* Cambios de configuración

### Valor para el negocio

* Historial completo de decisiones
* Mayor seguridad al delegar
* Resolución rápida de incidencias

---

## Alertas automáticas al dueño

Además de la gestión comercial, el sistema enviará alertas operativas mediante WhatsApp cuando ocurran eventos relevantes.

### Ejemplos de alertas

* Diferencias de caja
* Anulación de ventas
* Descuentos fuera de parámetros
* Caja sin cerrar
* Ajustes manuales de inventario
* Operaciones fuera del horario habitual

---

# 5. Diferenciador estratégico

# WhatsApp Business Automation

Uno de los principales diferenciales del proyecto será la automatización inteligente mediante WhatsApp.

## Alertas automáticas para el dueño

El sistema podrá enviar notificaciones cuando:

* Un producto esté próximo a agotarse
* Un producto llegue a stock crítico
* Existan productos próximos a vencer
* Se alcance una meta diaria de ventas
* La caja no haya sido cerrada
* Existan ventas fuera de horario habitual

## Comunicación con clientes frecuentes

El sistema podrá enviar campañas como:

* Promociones especiales
* Productos recién llegados
* Ofertas del fin de semana
* Fechas especiales
* Recordatorios de pedidos

### Valor real

No solo gestiona el negocio.

También ayuda a vender más.

---

# 6. Preguntas clave para el cliente

Durante la reunión inicial necesitamos responder:

* ¿Qué problemas quiere resolver primero?
* ¿Dónde pierde más dinero actualmente?
* ¿Qué tareas toman más tiempo?
* ¿Qué información hoy no puede medir?
* ¿Qué procesos aún se hacen manualmente?
* ¿Qué desea controlar desde su celular?
* ¿Quiere crecer a más sucursales?

---

# 7. Alcance inicial del proyecto

## Primera etapa

Construcción del PMV funcional.

Incluye:

* Ventas
* Inventario
* Proveedores
* Reportes
* Notificaciones WhatsApp

## Resultado esperado

En la primera versión, el cliente podrá operar su negocio con información centralizada, recibir alertas automáticas y tomar mejores decisiones basadas en datos reales.

---

# 8. Próximo paso

Agendar reunión de descubrimiento con el cliente para validar procesos actuales, prioridades y oportunidades de automatización.
