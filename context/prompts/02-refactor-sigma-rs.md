## 🛠️ Refactor SIGMA-RS: Dominio y CRUD de Tickets para Material Rodante

### Objetivo

Refactorizar el prototipo de SIGMA-RS para lograr un sistema mantenible, escalable y alineado a arquitectura limpia, siguiendo el estilo y criterios de ARS_MP. El sistema debe gestionar tickets de averías sobre material rodante diésel, diferenciando entre Locomotoras y Coches Remolcados.

### Reglas y Alcance
- Sos un experto Ingeniero de software, vas a refactorizar el sistema siguiendo los principios de arquitectura limpia y el estilo de ARS_MP. Vas a plantear Esquemas de tablas y relaciones de acuerdo a las entidades que vayas creando y primero las analizamos antes de implementar.

- El menú principal permite elegir con 2 botones centrales con alguna imágen o icono de una locomotora tipo GM y un coche remolcado tipo Materfer, para luego acceder al formulario CRUD correspondiente.
- CRUD completo de Tickets (Averías), con los campos y relaciones detallados abajo.
- Modelar entidades siguiendo el patrón de ARS_MP:
  - Unidad de Mantenimiento (abstracta): puede ser Locomotora o Coche Remolcado.
  - Locomotora: Marca (Dalian CNR, GM), Modelo (8G, 8H, G12, GR12, G22-CW, G22-CU, GT22-CW, GT22-CW-2, GT22-CU).
  - Coche Remolcado: Marca (Materfer, CNR), Clase (U, FU, F, CPA, CRA, PUA, PUAD, FS, FG).

- Tablas auxiliares administradas solo por usuarios admin, las vamos a cargar una sola vez (rara vez cambian), pero con posibilidades de ir actualizándolas si es necesario: Más adelante definimos como las vamos a llenar masivamente por primera vez, puede ser que generes un excel con los datos a completar y te los completo con los datos necesarios, por ejemplo, o CSV, etc.
 
 La definición de las tablas las dejo a tu criterio partiendo de lo que te dije anteriormente, proponés, analizamos y avanzamos.
  - Unidades de Mantenimiento
  - Marcas
  - Clases
  - Modelos
  - GOP (Guardias Operativas)
  - Supervisores
  - Nro de Tren
  - Tipos de Falla (Mecánicas, Eléctricas, Neumáticas, Electrónicas, Otras, ATS, Hombre Vivo, Hasler)
  - Sistema afectado (ej: Dependiendo de: 
        - Mecánicas:
          - Motor Diésel
          - Punta de eje
        - Eléctricas:
          - Motor de tracción
          - Otros sistemas eléctricos
        - Neumáticas:
          - Sistema de frenos
          - Otros sistemas neumáticos
        - Electrónicas:
          - Sistema de control
          - Otros sistemas electrónicos
        - Otras:
          - Sistema auxiliar
          - Otros sistemas
        - ATS:
          - Sistema ATS
        - Hombre Vivo:
          - Sistema Hombre Vivo
        - Hasler:
          - Sistema Hasler

### Modelo de Ticket (Avería)

- Nro de Ticket
- Fecha
- Unidad de Mantenimiento (FK a Locomotora o Coche Remolcado)
- GOP (FK)
- Ingreso: [Inmediato, Programado, NO]
- Nro OT (opcional)
- Estado: [Pendiente, Finalizado]
- Supervisor interviniente (FK)
- Nro de Tren (FK) (pero en un principio puede ser cualquier número de 4 dígitos)
- Horas: Aviso, Intervención, Entrega (pueden ser nulas)
- Falla denunciada por conductor (texto)
- Observaciones / Trabajo realizado por GOP (texto)

### Requisitos Técnicos

- Seguir el estilo de ARS_MP: dataclasses puras para dominio, modelos Django para persistencia, separación estricta de capas.
- Usar type hints modernos, docstrings Google, convenciones de nombres y estructura de carpetas como en ARS_MP.
- Preparar el modelo para extender tipos de falla y sistema afectado.
- Los valores predeterminados de los formularios deben obtenerse de las tablas auxiliares.
- CRUD y vistas Django para Tickets y entidades auxiliares.
- Tests siguiendo TDD (Red-Green-Refactor), docstrings en español para tests.

### Ejemplo de entidades (pseudo-código)

```python
@dataclass(kw_only=True)
class UnidadMantenimiento:
    id: UUID
    ...

@dataclass(kw_only=True)
class Locomotora(UnidadMantenimiento):
    marca: str
    modelo: str
    ...

@dataclass(kw_only=True)
class CocheRemolcado(UnidadMantenimiento):
    marca: str
    clase: str
    ...
```

### Notas

- No es necesario replicar el formato visual de la imagen, solo la información y relaciones.
- El sistema debe ser fácilmente extensible para nuevos tipos de unidades, fallas y atributos.
- Documentar supuestos y decisiones de modelado y ADRs.
