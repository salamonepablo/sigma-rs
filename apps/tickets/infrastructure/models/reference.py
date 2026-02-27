"""Reference data models for the tickets app.

Contains models for auxiliary/reference tables that are rarely modified:
Brand, LocomotiveModel, RailcarClass, FailureType, AffectedSystem,
GOP, Personal, TrainNumber, IntervencionTipo, Lugar.
"""

import uuid

from django.db import models


class BrandModel(models.Model):
    """Manufacturer brand for rolling stock.

    Known brands: GM (General Motors), CNR (Dalian), Materfer.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre",
        help_text="Nombre corto de la marca (ej: GM, CNR)",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código",
        help_text="Código único de la marca",
    )
    full_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nombre completo",
        help_text="Nombre legal o descriptivo completo",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        db_table = "brand"
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class LocomotiveModelModel(models.Model):
    """Locomotive model specification.

    Known GM models: GT22CW, GT22CW-2, G22CW, G22CU, GR12, G12.
    Known CNR models: 8G, 8H.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    name = models.CharField(
        max_length=50,
        verbose_name="Nombre",
        help_text="Nombre del modelo (ej: GT22CW)",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código",
        help_text="Código único del modelo",
    )
    brand = models.ForeignKey(
        BrandModel,
        on_delete=models.PROTECT,
        related_name="locomotive_models",
        verbose_name="Marca",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        db_table = "locomotive_model"
        verbose_name = "Modelo de locomotora"
        verbose_name_plural = "Modelos de locomotora"
        ordering = ["brand", "name"]

    def __str__(self) -> str:
        return f"{self.brand.name} {self.name}"


class RailcarClassModel(models.Model):
    """Railcar class specification.

    Classes are independent of brand/manufacturer.
    Known classes: U, FU, F, CT, CPA, CRA, PUA, PUAD, FS, FG, etc.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código",
        help_text="Código único de la clase (ej: U, FU, CPA)",
    )
    name = models.CharField(
        max_length=50,
        verbose_name="Nombre",
        help_text="Nombre descriptivo de la clase",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        db_table = "railcar_class"
        verbose_name = "Clase de coche remolcado"
        verbose_name_plural = "Clases de coche remolcado"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class FailureTypeModel(models.Model):
    """Failure type category.

    Known types: Mecánicas, Eléctricas, Neumáticas, Electrónicas,
    Otras, ATS, Hombre Vivo, Hasler.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre",
        help_text="Nombre del tipo de falla (ej: Mecánicas)",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código",
        help_text="Código único del tipo de falla",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        db_table = "failure_type"
        verbose_name = "Tipo de falla"
        verbose_name_plural = "Tipos de falla"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class AffectedSystemModel(models.Model):
    """Affected system within a failure type.

    Examples by failure type:
    - Mecánicas: Motor Diésel, Punta de eje
    - Eléctricas: Motor de tracción, Otros sistemas eléctricos
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre",
        help_text="Nombre del sistema (ej: Motor Diésel)",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código",
        help_text="Código único del sistema",
    )
    failure_type = models.ForeignKey(
        FailureTypeModel,
        on_delete=models.PROTECT,
        related_name="affected_systems",
        verbose_name="Tipo de falla",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        db_table = "affected_system"
        verbose_name = "Sistema afectado"
        verbose_name_plural = "Sistemas afectados"
        ordering = ["failure_type", "name"]

    def __str__(self) -> str:
        return self.name


class GOPModel(models.Model):
    """Operational Guard (Guardia Operativa).

    Represents work shifts that handle maintenance tickets.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    name = models.CharField(
        max_length=50,
        verbose_name="Nombre",
        help_text="Nombre de la GOP (ej: GOP 1)",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código",
        help_text="Código único de la GOP",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        db_table = "gop"
        verbose_name = "Guardia Operativa"
        verbose_name_plural = "Guardias Operativas"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class PersonalModel(models.Model):
    """Maintenance personnel (Interviniente).

    Represents workers who intervene in ticket resolution.
    Loaded from SAP employee data.
    """

    class Sector(models.TextChoices):
        LOCOMOTORAS = "locomotora", "Locomotoras"
        COCHES_REMOLCADOS = "coche_remolcado", "Coches Remolcados"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    legajo_sap = models.CharField(
        max_length=20,
        verbose_name="Legajo SAP",
        help_text="Número de legajo en SAP",
    )
    cuit = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="CUIT",
    )
    full_name = models.CharField(
        max_length=200,
        verbose_name="Nombre y Apellido",
    )
    sector = models.CharField(
        max_length=20,
        choices=Sector.choices,
        verbose_name="Sector",
        help_text="Locomotoras o Coches Remolcados",
    )
    sector_simaf = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Sector SIMAF",
        help_text="Sector en sistema SIMAF",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        db_table = "personal"
        verbose_name = "Personal"
        verbose_name_plural = "Personal"
        ordering = ["full_name"]
        # Un empleado puede estar en ambos sectores
        unique_together = [["legajo_sap", "sector"]]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.legajo_sap})"


class IntervencionTipoModel(models.Model):
    """Intervention type for maintenance events (Novedades).

    Imported from legacy baseLocs.mdb Access database table 'Intervenciones'.
    Classifies the type of maintenance intervention performed.
    """

    class IntervencionClase(models.TextChoices):
        REV = "REV", "Revisión"
        DET = "DET", "Detención"
        NONE = "-", "-"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código",
        help_text="Código del tipo de intervención (ej: AL, RA, AB)",
    )
    descripcion = models.CharField(
        max_length=100,
        verbose_name="Descripción",
        help_text="Descripción del tipo de intervención",
    )
    clase = models.CharField(
        max_length=10,
        choices=IntervencionClase.choices,
        default=IntervencionClase.NONE,
        verbose_name="Clase",
        help_text="Clasificación: Revisión (REV) o Detención (DET)",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        db_table = "intervencion_tipo"
        verbose_name = "Tipo de Intervención"
        verbose_name_plural = "Tipos de Intervención"
        ordering = ["codigo"]

    def __str__(self) -> str:
        return self.codigo


class LugarModel(models.Model):
    """Physical location for maintenance operations.

    Represents stations, workshops, depots, and other locations
    where maintenance activities take place.
    Imported from legacy Access database (baseLocs.mdb).
    """

    class LugarTipo(models.TextChoices):
        TALLER = "Taller", "Taller"
        ESTACION = "Estación", "Estación"
        DEPOSITO = "Depósito", "Depósito"
        DESVIO = "Desvío", "Desvío"
        MESA = "Mesa", "Mesa"
        LINEA = "Línea", "Línea"

    class LugarRevision(models.TextChoices):
        REPARACION = "Reparacion", "Reparación"
        ALISTAMIENTO = "Alistamiento", "Alistamiento"
        NINGUNA = "-", "-"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    codigo = models.IntegerField(
        unique=True,
        verbose_name="Código",
        help_text="Código numérico del lugar (legacy)",
    )
    descripcion = models.CharField(
        max_length=100,
        verbose_name="Descripción",
        help_text="Nombre completo del lugar",
    )
    short_desc = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Abreviatura",
        help_text="Código corto (ej: LP, TY, RE)",
    )
    tipo = models.CharField(
        max_length=20,
        choices=LugarTipo.choices,
        blank=True,
        null=True,
        verbose_name="Tipo",
    )
    revision = models.CharField(
        max_length=20,
        choices=LugarRevision.choices,
        blank=True,
        null=True,
        verbose_name="Tipo de revisión",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        db_table = "lugar"
        verbose_name = "Lugar"
        verbose_name_plural = "Lugares"
        ordering = ["descripcion"]

    def __str__(self) -> str:
        if self.short_desc and self.short_desc != "-":
            return f"{self.codigo} - {self.descripcion} ({self.short_desc})"
        return f"{self.codigo} - {self.descripcion}"


class TrainNumberModel(models.Model):
    """Train service number.

    Identifies railway services (typically 4-digit numbers).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    number = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Número de tren",
        help_text="Número del servicio (ej: 1234)",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Descripción",
    )
    route = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Recorrido",
        help_text="Recorrido del tren (ej: Constitución - La Plata)",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        db_table = "train_number"
        verbose_name = "Número de tren"
        verbose_name_plural = "Números de tren"
        ordering = ["number"]

    def __str__(self) -> str:
        return self.number
