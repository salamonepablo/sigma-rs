"""Management command to import legacy data from Access database exports.

Imports data from CSV/TXT files exported from baseLocs.mdb:
- Lugares.txt -> LugarModel
- Locomotoras.txt -> MaintenanceUnitModel + LocomotiveModel
- Vagones.txt -> MaintenanceUnitModel + WagonModel
- Detenciones.txt -> NovedadModel

Usage:
    python manage.py import_legacy_data --lugares
    python manage.py import_legacy_data --locomotoras
    python manage.py import_legacy_data --vagones
    python manage.py import_legacy_data --detenciones
    python manage.py import_legacy_data --all
"""

import csv
import uuid
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.tickets.infrastructure.services.legacy_novedad_importer import (
    LegacyNovedadImporter,
)
from apps.tickets.models import (
    BrandModel,
    IntervencionTipoModel,
    LocomotiveModel,
    LocomotiveModelModel,
    LugarModel,
    MaintenanceUnitModel,
    RailcarClassModel,
    RailcarModel,
    WagonModel,
    WagonTypeModel,
)


class Command(BaseCommand):
    """Import legacy data from Access database exports."""

    help = "Import legacy data from Access database exports (Lugares, Locomotoras, Detenciones)"

    # Default path to legacy data files
    DEFAULT_PATH = Path(settings.LEGACY_DATA_PATH)

    # Mapping of legacy Serie to our Brand and Model
    SERIE_MAPPING = {
        # GM Locomotives
        "G12": {"brand": "GM", "model": "G12"},
        "GR12": {"brand": "GM", "model": "GR12"},
        "G22": {"brand": "GM", "model": "G22-CW"},
        "GT22-CW": {"brand": "GM", "model": "GT22-CW"},
        "GT22-CW2": {"brand": "GM", "model": "GT22-CW-2"},
        "GT22-CW3": {"brand": "GM", "model": "GT22-CW-3"},
        "GM 319": {"brand": "GM", "model": "319"},
        "GM": {"brand": "GM", "model": "OTHER"},
        # CNR Locomotives
        "CNR": {"brand": "CNR", "model": "CKD8G"},
        # Other brands
        "GAIA": {"brand": "GAIA", "model": "GAIA"},
        "Alco": {"brand": "Alco", "model": "Alco"},
        "Alco RSD16": {"brand": "Alco", "model": "RSD16"},
        "Alco RSD16 ": {"brand": "Alco", "model": "RSD16"},
        "CSR": {"brand": "CSR", "model": "CSR"},
        "CAF 593": {"brand": "CAF", "model": "593"},
        "C.M. NOHAB": {"brand": "Nohab", "model": "Nohab"},
    }

    # Units that are Motorcoaches, not Locomotives
    MOTORCOACH_UNITS = {"105", "106"}

    # Mapping of legacy Serie to Brand and RailcarClass for Coches Remolcados
    # Format: "Serie in file": {"brand": "BrandCode", "class": "ClassCode"}
    SERIE_COCHE_MAPPING = {
        # Materfer variants
        "U. Materfer": {"brand": "Materfer", "class": "U"},
        "U.C. Materfer": {"brand": "Materfer", "class": "UC"},
        "F.U. Materfer": {"brand": "Materfer", "class": "FU"},
        "F.U.C. Materfer": {"brand": "Materfer", "class": "FUC"},
        "F. Materfer": {"brand": "Materfer", "class": "F"},
        "F.C. Materfer": {"brand": "Materfer", "class": "FC"},
        "D.A. Materfer": {"brand": "Materfer", "class": "DA"},
        "C.T. Materfer": {"brand": "Materfer", "class": "CT"},
        "C.U. Materfer": {"brand": "Materfer", "class": "CU"},
        "C.U.G. Materfer": {"brand": "Materfer", "class": "CUG"},
        "P. Materfer": {"brand": "Materfer", "class": "P"},
        "R.A. Materfer": {"brand": "Materfer", "class": "RA"},
        # CNR coches
        "CNR": {"brand": "CNR", "class": "CNR"},
        "CPA": {"brand": "CNR", "class": "CPA"},
        "CRA": {"brand": "CNR", "class": "CRA"},
        "PUA": {"brand": "CNR", "class": "PUA"},
        "PUAD": {"brand": "CNR", "class": "PUAD"},
        "FG": {"brand": "CNR", "class": "FG"},
        "FS": {"brand": "CNR", "class": "FS"},
        "CDA": {"brand": "CNR", "class": "CDA"},
        # Sorefame
        "Sorefame": {"brand": "Sorefame", "class": "Sorefame"},
        "Sorefame P": {"brand": "Sorefame", "class": "P"},
        "Sorefame CT": {"brand": "Sorefame", "class": "CT"},
        "Rp - Sorefame": {"brand": "Sorefame", "class": "Rp"},
        "Ry - Sorefame": {"brand": "Sorefame", "class": "Ry"},
        "Mc - Sorefame": {"brand": "Sorefame", "class": "Mc"},
        # Tecnotren
        "Tecnotren (M)": {"brand": "Tecnotren", "class": "M"},
        "Tecnotren (R)": {"brand": "Tecnotren", "class": "R"},
        # Toshiba
        "Toshiba": {"brand": "Toshiba", "class": "Toshiba"},
        # Werkspoor
        "CSS Werkspoor": {"brand": "Werkspoor", "class": "CSS"},
        "CVS Werkspoor": {"brand": "Werkspoor", "class": "CVS"},
        "FS Werkspoor": {"brand": "Werkspoor", "class": "FS"},
        "FC": {"brand": "Werkspoor", "class": "FC"},
        "OA Hitachi": {"brand": "Hitachi", "class": "OA"},
        # Automovilera
        "Automovilera": {"brand": "Automovilera", "class": "Automovilera"},
        # Vagones de carga (freight wagons)
        "Chata": None,
        "Hopper": None,
        "BK": None,
        "Cubierto": None,
        "Tanque": None,
        "Tanque?": None,
        "Plataforma": None,
        "Tolva": None,
        "Vagon": None,
        "": None,
    }

    WAGON_CLASS_MAPPING = {
        "bk": "BK",
        "hopper": "HOPPER",
        "tolva (hopper)": "HOPPER",
        "tolva": "HOPPER",
        "chata": "CHATA",
        "cubierto": "CUBIERTO",
        "plataforma": "PLATAFORMA",
        "automovilera": "AUTOMOVILERA",
        "tanque": "TANQUE",
        "tanque?": "TANQUE",
        "vagon": "VAGON",
        "": "VAGON",
    }

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--path",
            type=str,
            default=str(self.DEFAULT_PATH),
            help="Path to directory containing legacy data files",
        )
        parser.add_argument(
            "--lugares",
            action="store_true",
            help="Import Lugares.txt",
        )
        parser.add_argument(
            "--locomotoras",
            action="store_true",
            help="Import Locomotoras.txt",
        )
        parser.add_argument(
            "--intervenciones",
            action="store_true",
            help="Import Intervenciones.txt",
        )
        parser.add_argument(
            "--detenciones",
            action="store_true",
            help="Import Detenciones.txt (locomotoras)",
        )
        parser.add_argument(
            "--coches",
            action="store_true",
            help="Import Coches.txt (coches remolcados)",
        )
        parser.add_argument(
            "--vagones",
            action="store_true",
            help="Import Iniciales/Vagones.txt",
        )
        parser.add_argument(
            "--intervenciones-ccrr",
            action="store_true",
            help="Import IntervencionesCCRR.txt",
        )
        parser.add_argument(
            "--detenciones-ccrr",
            action="store_true",
            help="Import DetencionesCCRR.txt",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help=(
                "Import all files (lugares, locomotoras, coches, vagones, detenciones)"
            ),
        )
        parser.add_argument(
            "--all-ccrr",
            action="store_true",
            help="Import all CCRR files (coches, intervenciones-ccrr, detenciones-ccrr)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without actually importing",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        path = Path(options["path"])

        if not path.exists():
            raise CommandError(f"Path does not exist: {path}")

        import_all = options["all"]
        import_all_ccrr = options["all_ccrr"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))

        # Import in order: lugares first, then intervenciones, then units, then detenciones
        if import_all or options["lugares"]:
            self.import_lugares(path, dry_run)

        if import_all or options["intervenciones"]:
            self.import_intervenciones(path, dry_run)

        if import_all_ccrr or options["intervenciones_ccrr"]:
            self.import_intervenciones_ccrr(path, dry_run)

        if import_all or options["locomotoras"]:
            self.import_locomotoras(path, dry_run)

        if import_all or import_all_ccrr or options["coches"]:
            self.import_coches(path, dry_run)

        if import_all or options["vagones"]:
            self.import_vagones(path, dry_run)

        if import_all or options["detenciones"]:
            self.import_detenciones(path, dry_run)

        if import_all_ccrr or options["detenciones_ccrr"]:
            self.import_detenciones_ccrr(path, dry_run)

        if not any(
            [
                import_all,
                import_all_ccrr,
                options["lugares"],
                options["intervenciones"],
                options["intervenciones_ccrr"],
                options["locomotoras"],
                options["coches"],
                options["vagones"],
                options["detenciones"],
                options["detenciones_ccrr"],
            ]
        ):
            self.stdout.write(
                self.style.WARNING(
                    "No import option specified. Use --lugares, --intervenciones, "
                    "--locomotoras, --detenciones, --coches, --vagones, "
                    "--intervenciones-ccrr, --detenciones-ccrr, --all, or --all-ccrr"
                )
            )

    def import_lugares(self, path: Path, dry_run: bool = False):
        """Import lugares from Lugares.txt."""
        file_path = path / "Lugares.txt"
        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Importing lugares from {file_path}...")

        created = 0
        updated = 0
        skipped = 0

        with open(file_path, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    codigo = int(row["Lugar_codigo"])
                    descripcion = row["Lugar_descripcion"].strip()
                    short_desc = row.get("Lugar_shortdesc", "").strip() or None
                    tipo = row.get("Lugar_tipo", "").strip() or None
                    revision = row.get("Lugar_revision", "").strip() or None

                    if dry_run:
                        self.stdout.write(f"  Would import: {codigo} - {descripcion}")
                        created += 1
                        continue

                    lugar, was_created = LugarModel.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            "descripcion": descripcion,
                            "short_desc": short_desc if short_desc != "-" else None,
                            "tipo": tipo
                            if tipo in dict(LugarModel.LugarTipo.choices)
                            else None,
                            "revision": revision
                            if revision in dict(LugarModel.LugarRevision.choices)
                            else None,
                        },
                    )

                    if was_created:
                        created += 1
                    else:
                        updated += 1

                except (ValueError, KeyError) as e:
                    self.stdout.write(self.style.WARNING(f"  Skipping row: {e}"))
                    skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Lugares: {created} created, {updated} updated, {skipped} skipped"
            )
        )

    def import_intervenciones(self, path: Path, dry_run: bool = False):
        """Import intervention types from Intervenciones.txt."""
        file_path = path / "Intervenciones.txt"
        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Importing intervenciones from {file_path}...")

        created = 0
        updated = 0
        skipped = 0

        with open(file_path, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    codigo = row["Intervencion_tipo"].strip()
                    descripcion = row["Intervencion_descripcion"].strip()
                    clase = row.get("Intervencion_clase", "").strip() or "-"

                    if dry_run:
                        self.stdout.write(f"  Would import: {codigo} - {descripcion}")
                        created += 1
                        continue

                    interv, was_created = (
                        IntervencionTipoModel.objects.update_or_create(
                            codigo=codigo,
                            defaults={
                                "descripcion": descripcion,
                                "clase": clase
                                if clase
                                in dict(IntervencionTipoModel.IntervencionClase.choices)
                                else "-",
                            },
                        )
                    )

                    if was_created:
                        created += 1
                    else:
                        updated += 1

                except (ValueError, KeyError) as e:
                    self.stdout.write(self.style.WARNING(f"  Skipping row: {e}"))
                    skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Intervenciones: {created} created, {updated} updated, {skipped} skipped"
            )
        )

    def import_intervenciones_ccrr(self, path: Path, dry_run: bool = False):
        """Import intervention types for CCRR from IntervencionesCCRR.txt."""
        file_path = path / "IntervencionesCCRR.txt"
        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Importing intervenciones CCRR from {file_path}...")

        created = 0
        updated = 0
        skipped = 0

        with open(file_path, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    codigo = row["Intervencion_tipo"].strip()
                    descripcion = row["Intervencion_descripcion"].strip()
                    clase = row.get("Intervencion_clase", "").strip() or "-"

                    if dry_run:
                        self.stdout.write(f"  Would import: {codigo} - {descripcion}")
                        created += 1
                        continue

                    interv, was_created = (
                        IntervencionTipoModel.objects.update_or_create(
                            codigo=codigo,
                            defaults={
                                "descripcion": descripcion,
                                "clase": clase
                                if clase
                                in dict(IntervencionTipoModel.IntervencionClase.choices)
                                else "-",
                            },
                        )
                    )

                    if was_created:
                        created += 1
                    else:
                        updated += 1

                except (ValueError, KeyError) as e:
                    self.stdout.write(self.style.WARNING(f"  Skipping row: {e}"))
                    skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Intervenciones CCRR: {created} created, {updated} updated, {skipped} skipped"
            )
        )

    def import_locomotoras(self, path: Path, dry_run: bool = False):
        """Import locomotoras from Locomotoras.txt."""
        file_path = path / "Locomotoras.txt"
        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Importing locomotoras from {file_path}...")

        # Ensure brands and models exist
        self._ensure_brands_and_models()

        created = 0
        skipped_existing = 0
        skipped_error = 0

        with open(file_path, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    locs = row["Locs"].strip()
                    serie = row["Serie"].strip()

                    # Skip if already exists
                    if MaintenanceUnitModel.objects.filter(number=locs).exists():
                        skipped_existing += 1
                        continue

                    # Skip motorcoaches - they should be added separately
                    if locs in self.MOTORCOACH_UNITS:
                        skipped_existing += 1
                        continue

                    # Get brand and model from serie mapping
                    mapping = self.SERIE_MAPPING.get(serie)
                    if not mapping:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Unknown serie '{serie}' for unit {locs}"
                            )
                        )
                        skipped_error += 1
                        continue

                    if dry_run:
                        self.stdout.write(
                            f"  Would import: {locs} ({mapping['brand']} {mapping['model']})"
                        )
                        created += 1
                        continue

                    # Get brand and model
                    brand = BrandModel.objects.filter(
                        name__iexact=mapping["brand"]
                    ).first()
                    if not brand:
                        brand = BrandModel.objects.filter(
                            code__iexact=mapping["brand"]
                        ).first()

                    if not brand:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Brand not found: {mapping['brand']} for {locs}"
                            )
                        )
                        skipped_error += 1
                        continue

                    model = LocomotiveModelModel.objects.filter(
                        name__iexact=mapping["model"]
                    ).first()
                    if not model:
                        model = LocomotiveModelModel.objects.filter(
                            code__iexact=mapping["model"]
                        ).first()

                    if not model:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Model not found: {mapping['model']} for {locs}"
                            )
                        )
                        skipped_error += 1
                        continue

                    # Create MaintenanceUnit and Locomotive
                    with transaction.atomic():
                        mu = MaintenanceUnitModel.objects.create(
                            id=uuid.uuid4(),
                            number=locs,
                            unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
                            is_active=True,
                        )
                        LocomotiveModel.objects.create(
                            maintenance_unit=mu,
                            brand=brand,
                            model=model,
                        )
                        created += 1

                except (ValueError, KeyError) as e:
                    self.stdout.write(
                        self.style.WARNING(f"  Error processing row: {e}")
                    )
                    skipped_error += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Locomotoras: {created} created, {skipped_existing} already exist, {skipped_error} errors"
            )
        )

    def import_coches(self, path: Path, dry_run: bool = False):
        """Import coches remolcados from Coches.txt."""
        file_path = path / "Coches.txt"
        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Importing coches from {file_path}...")

        # Ensure brands and railcar classes exist
        self._ensure_railcar_brands_and_classes()

        created = 0
        skipped_existing = 0
        skipped_cargo = 0
        skipped_error = 0

        with open(file_path, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    coche = row["Coche"].strip()
                    serie = row["Serie"].strip()

                    # Skip if already exists
                    if MaintenanceUnitModel.objects.filter(number=coche).exists():
                        skipped_existing += 1
                        continue

                    # Get brand and class from serie mapping
                    mapping = self.SERIE_COCHE_MAPPING.get(serie)
                    if mapping is None:
                        # None means it's a cargo wagon, skip it
                        skipped_cargo += 1
                        continue

                    if not mapping:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Unknown serie '{serie}' for coche {coche}"
                            )
                        )
                        skipped_error += 1
                        continue

                    if dry_run:
                        self.stdout.write(
                            f"  Would import: {coche} ({mapping['brand']} {mapping['class']})"
                        )
                        created += 1
                        continue

                    # Get brand
                    brand = BrandModel.objects.filter(
                        code__iexact=mapping["brand"]
                    ).first()
                    if not brand:
                        brand = BrandModel.objects.filter(
                            name__iexact=mapping["brand"]
                        ).first()

                    if not brand:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Brand not found: {mapping['brand']} for {coche}"
                            )
                        )
                        skipped_error += 1
                        continue

                    # Get railcar class using composite code (brand_class)
                    composite_code = f"{mapping['brand']}_{mapping['class']}"
                    railcar_class = RailcarClassModel.objects.filter(
                        code=composite_code
                    ).first()

                    if not railcar_class:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Class not found: {composite_code} for {coche}"
                            )
                        )
                        skipped_error += 1
                        continue

                    # Create MaintenanceUnit and Railcar
                    with transaction.atomic():
                        mu = MaintenanceUnitModel.objects.create(
                            id=uuid.uuid4(),
                            number=coche,
                            unit_type=MaintenanceUnitModel.UnitType.RAILCAR,
                            is_active=True,
                        )
                        RailcarModel.objects.create(
                            maintenance_unit=mu,
                            brand=brand,
                            railcar_class=railcar_class,
                        )
                        created += 1

                except (ValueError, KeyError) as e:
                    self.stdout.write(
                        self.style.WARNING(f"  Error processing row: {e}")
                    )
                    skipped_error += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Coches: {created} created, {skipped_existing} already exist, "
                f"{skipped_cargo} cargo wagons skipped, {skipped_error} errors"
            )
        )

    def import_vagones(self, path: Path, dry_run: bool = False):
        """Import wagons from Iniciales/Vagones.txt."""
        file_path = path / "Iniciales" / "Vagones.txt"
        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Importing vagones from {file_path}...")

        self._ensure_wagon_reference_data()

        brand = BrandModel.objects.filter(code__iexact="Carga").first()
        if not brand:
            self.stdout.write(self.style.ERROR("Brand not found: Carga"))
            return

        wagon_types_by_code = {w.code: w for w in WagonTypeModel.objects.all()}

        created = 0
        skipped_existing = 0
        skipped_error = 0

        with open(file_path, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    coche = (row.get("Coche") or "").strip()
                    legacy_class = (row.get("Clase") or "").strip()

                    if not coche:
                        skipped_error += 1
                        continue

                    if MaintenanceUnitModel.objects.filter(number=coche).exists():
                        skipped_existing += 1
                        continue

                    wagon_type_code = self._map_wagon_type_code(legacy_class)
                    wagon_type = wagon_types_by_code.get(wagon_type_code)
                    if not wagon_type:
                        fallback = wagon_types_by_code.get("VAGON")
                        if fallback:
                            wagon_type = fallback
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  Wagon type not found: {wagon_type_code} for {coche}"
                                )
                            )
                            skipped_error += 1
                            continue

                    if dry_run:
                        created += 1
                        continue

                    with transaction.atomic():
                        mu = MaintenanceUnitModel.objects.create(
                            id=uuid.uuid4(),
                            number=coche,
                            unit_type=MaintenanceUnitModel.UnitType.WAGON,
                            rolling_stock_category=MaintenanceUnitModel.Category.CARGO,
                            is_active=True,
                        )
                        WagonModel.objects.create(
                            maintenance_unit=mu,
                            brand=brand,
                            wagon_type=wagon_type,
                            legacy_class=legacy_class or None,
                        )
                        created += 1

                except (ValueError, KeyError) as e:
                    self.stdout.write(
                        self.style.WARNING(f"  Error processing row: {e}")
                    )
                    skipped_error += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Vagones: {created} created, {skipped_existing} already exist, "
                f"{skipped_error} errors"
            )
        )

    def _map_wagon_type_code(self, legacy_class: str) -> str:
        """Map legacy wagon class to WagonType code."""
        normalized = legacy_class.strip().lower()
        return self.WAGON_CLASS_MAPPING.get(normalized, "VAGON")

    def _ensure_wagon_reference_data(self):
        """Ensure brand and wagon types exist for wagons."""
        brand, created = BrandModel.objects.get_or_create(
            code="Carga",
            defaults={"name": "Carga", "full_name": "Vagones de Carga"},
        )
        if created:
            self.stdout.write("  Created brand: Carga")

        wagon_types = [
            ("BK", "BK"),
            ("HOPPER", "Hopper"),
            ("CHATA", "Chata"),
            ("CUBIERTO", "Cubierto"),
            ("PLATAFORMA", "Plataforma"),
            ("AUTOMOVILERA", "Automovilera"),
            ("TANQUE", "Tanque"),
            ("VAGON", "Vagon"),
        ]

        for code, name in wagon_types:
            wagon_type, was_created = WagonTypeModel.objects.get_or_create(
                code=code,
                defaults={"name": name},
            )
            if was_created:
                self.stdout.write(f"  Created wagon type: {wagon_type.name}")

    def _ensure_railcar_brands_and_classes(self):
        """Ensure all required brands and railcar classes exist for coches."""
        # Brands to create for coches
        brands_to_create = [
            ("Materfer", "Materfer S.A."),
            ("CNR", "China CNR Corporation (Dalian)"),
            ("Sorefame", "Sorefame"),
            ("Tecnotren", "Tecnotren"),
            ("Toshiba", "Toshiba"),
            ("Werkspoor", "Werkspoor"),
            ("Hitachi", "Hitachi"),
            ("Automovilera", "Automovilera"),
        ]

        for code, full_name in brands_to_create:
            brand, created = BrandModel.objects.get_or_create(
                code=code,
                defaults={"name": code, "full_name": full_name},
            )
            if created:
                self.stdout.write(f"  Created brand: {code}")

        # Get brands for class creation
        materfer = BrandModel.objects.get(code="Materfer")
        cnr = BrandModel.objects.get(code="CNR")
        sorefame = BrandModel.objects.get(code="Sorefame")
        tecnotren = BrandModel.objects.get(code="Tecnotren")
        toshiba = BrandModel.objects.get(code="Toshiba")
        werkspoor = BrandModel.objects.get(code="Werkspoor")
        hitachi = BrandModel.objects.get(code="Hitachi")
        automovilera = BrandModel.objects.get(code="Automovilera")

        # Railcar classes to create
        classes_to_create = [
            # Materfer classes
            ("U", "Unica", materfer),
            ("UC", "Unica Cabina", materfer),
            ("FU", "Furgon Unica", materfer),
            ("FUC", "Furgon Unica Cabina", materfer),
            ("F", "Furgon", materfer),
            ("FC", "Furgon Correo", materfer),
            ("DA", "Dormitorio con AA", materfer),
            ("CT", "Clase Turista", materfer),
            ("CU", "Clase Unica", materfer),
            ("CUG", "Clase Unica G", materfer),
            ("P", "Primera", materfer),
            ("RA", "Restaurant con AA", materfer),
            # CNR classes
            ("CNR", "CNR generico", cnr),
            ("CPA", "Coche de Pasajeros A", cnr),
            ("CRA", "Coche Remolque A", cnr),
            ("PUA", "Pasajeros Unica A", cnr),
            ("PUAD", "Pasajeros Unica A Discapacitados", cnr),
            ("FG", "Furgon Generador", cnr),
            ("FS", "Furgon Standard", cnr),
            ("CDA", "Coche Dormitorio A", cnr),
            # Sorefame classes
            ("Sorefame", "Sorefame generico", sorefame),
            ("Rp", "Remolque de pasajeros", sorefame),
            ("Ry", "Remolque tipo Y", sorefame),
            ("Mc", "Motor cabina", sorefame),
            # Tecnotren classes
            ("M", "Motor", tecnotren),
            ("R", "Remolque", tecnotren),
            # Toshiba
            ("Toshiba", "Toshiba generico", toshiba),
            # Werkspoor classes
            ("CSS", "Coche Salon Standard", werkspoor),
            ("CVS", "Coche Viajeros Standard", werkspoor),
            # Hitachi
            ("OA", "Coche OA", hitachi),
            # Automovilera
            ("Automovilera", "Automovilera generico", automovilera),
        ]

        # Also add Sorefame CT and P classes
        sorefame_extra = [
            ("CT", "Clase Turista", sorefame),
            ("P", "Primera", sorefame),
            ("FS", "Furgon Standard", werkspoor),
            ("FC", "Furgon Correo", werkspoor),
        ]

        for code, name, brand in classes_to_create + sorefame_extra:
            # Use a composite key approach since code might not be unique
            railcar_class, created = RailcarClassModel.objects.get_or_create(
                code=f"{brand.code}_{code}",
                defaults={"name": name, "brand": brand},
            )
            if created:
                self.stdout.write(f"  Created railcar class: {brand.code} {name}")

    def _get_railcar_class(self, brand_code: str, class_code: str):
        """Get railcar class by brand and class code."""
        composite_code = f"{brand_code}_{class_code}"
        return RailcarClassModel.objects.filter(code=composite_code).first()

    def _ensure_brands_and_models(self):
        """Ensure all required brands and locomotive models exist."""
        # Brands to create
        brands_to_create = [
            ("GM", "General Motors"),
            ("CNR", "China CNR Corporation (Dalian)"),
            ("Nohab", "NOHAB"),
            ("Alco", "American Locomotive Company"),
            ("GAIA", "GAIA"),
            ("CSR", "China South Railway"),
            ("CAF", "Construcciones y Auxiliar de Ferrocarriles"),
        ]

        for code, full_name in brands_to_create:
            brand, created = BrandModel.objects.get_or_create(
                code=code,
                defaults={"name": code, "full_name": full_name},
            )
            if created:
                self.stdout.write(f"  Created brand: {code}")

        # Get GM brand for locomotive models
        gm_brand = BrandModel.objects.get(code="GM")
        cnr_brand = BrandModel.objects.get(code="CNR")
        alco_brand = BrandModel.objects.get(code="Alco")
        gaia_brand = BrandModel.objects.get(code="GAIA")
        csr_brand = BrandModel.objects.get(code="CSR")
        caf_brand = BrandModel.objects.get(code="CAF")
        nohab_brand = BrandModel.objects.get(code="Nohab")

        # Models to create
        models_to_create = [
            ("G12", "G12", gm_brand),
            ("GR12", "GR12", gm_brand),
            ("G22-CW", "G22-CW", gm_brand),
            ("GT22-CW", "GT22-CW", gm_brand),
            ("GT22-CW-2", "GT22-CW-2", gm_brand),
            ("GT22-CW-3", "GT22-CW-3", gm_brand),
            ("319", "319", gm_brand),
            ("OTHER", "Otro GM", gm_brand),
            ("CKD8G", "CKD8G", cnr_brand),
            ("CKD8H", "CKD8H", cnr_brand),
            ("RSD16", "RSD16", alco_brand),
            ("Alco", "Alco genérico", alco_brand),
            ("GAIA", "GAIA", gaia_brand),
            ("CSR", "CSR", csr_brand),
            ("593", "Serie 593", caf_brand),
            ("Nohab", "Nohab", nohab_brand),
        ]

        for code, name, brand in models_to_create:
            model, created = LocomotiveModelModel.objects.get_or_create(
                code=code,
                defaults={"name": name, "brand": brand},
            )
            if created:
                self.stdout.write(f"  Created model: {name}")

    def import_detenciones(self, path: Path, dry_run: bool = False):
        """Import novedades from Detenciones_Locs.txt."""
        importer = LegacyNovedadImporter()
        stats = importer.import_detenciones(
            base_path=path,
            dry_run=dry_run,
            raise_on_missing=False,
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Detenciones: {inserted} created, {duplicates} duplicates skipped, "
                "{invalid} invalid/skipped".format(
                    inserted=stats.inserted,
                    duplicates=stats.duplicates,
                    invalid=stats.invalid,
                )
            )
        )

    def import_detenciones_ccrr(self, path: Path, dry_run: bool = False):
        """Import detenciones CCRR from DetencionesCCRR.txt."""
        importer = LegacyNovedadImporter()
        stats = importer.import_detenciones_ccrr(
            base_path=path,
            dry_run=dry_run,
            raise_on_missing=False,
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Detenciones CCRR: {inserted} created, {invalid} skipped, "
                "{duplicates} duplicates".format(
                    inserted=stats.inserted,
                    duplicates=stats.duplicates,
                    invalid=stats.invalid,
                )
            )
        )

    def _parse_date(self, date_str: str):
        """Parse date from legacy format (DD/MM/YYYY)."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError:
            return None
