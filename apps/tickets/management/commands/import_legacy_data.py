"""Management command to import legacy data from Access database exports.

Imports data from CSV/TXT files exported from baseLocs.mdb:
- Lugares.txt -> LugarModel
- Locomotoras.txt -> MaintenanceUnitModel + LocomotiveModel
- Detenciones.txt -> NovedadModel

Usage:
    python manage.py import_legacy_data --lugares
    python manage.py import_legacy_data --locomotoras
    python manage.py import_legacy_data --detenciones
    python manage.py import_legacy_data --all
"""

import csv
import uuid
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.tickets.models import (
    BrandModel,
    IntervencionTipoModel,
    LocomotiveModel,
    LocomotiveModelModel,
    LugarModel,
    MaintenanceUnitModel,
    NovedadModel,
    RailcarClassModel,
    RailcarModel,
)


class Command(BaseCommand):
    """Import legacy data from Access database exports."""

    help = "Import legacy data from Access database exports (Lugares, Locomotoras, Detenciones)"

    # Default path to legacy data files
    DEFAULT_PATH = Path("context/db-legacy")

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
        "Chata": {"brand": "Carga", "class": "Chata"},
        "Hopper": {"brand": "Carga", "class": "Hopper"},
        "BK": {"brand": "Carga", "class": "BK"},
        "Cubierto": {"brand": "Carga", "class": "Cubierto"},
        "Tanque": {"brand": "Carga", "class": "Tanque"},
        "Tanque?": {"brand": "Carga", "class": "Tanque"},
        "Plataforma": {"brand": "Carga", "class": "Plataforma"},
        "Tolva": {"brand": "Carga", "class": "Tolva"},
        "Vagon": {"brand": "Carga", "class": "Vagon"},
        "": None,
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
            help="Import all files (lugares, locomotoras, coches, detenciones)",
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
                options["detenciones"],
                options["detenciones_ccrr"],
            ]
        ):
            self.stdout.write(
                self.style.WARNING(
                    "No import option specified. Use --lugares, --intervenciones, "
                    "--locomotoras, --detenciones, --coches, --intervenciones-ccrr, "
                    "--detenciones-ccrr, --all, or --all-ccrr"
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
            ("Carga", "Vagones de Carga"),
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
        carga = BrandModel.objects.get(code="Carga")

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
            # Vagones de carga (freight wagons)
            ("Chata", "Vagon Chata", carga),
            ("Hopper", "Vagon Hopper", carga),
            ("BK", "Vagon BK", carga),
            ("Cubierto", "Vagon Cubierto", carga),
            ("Tanque", "Vagon Tanque", carga),
            ("Plataforma", "Vagon Plataforma", carga),
            ("Tolva", "Vagon Tolva", carga),
            ("Vagon", "Vagon Generico", carga),
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
        """Import detenciones from Detenciones.txt."""
        file_path = path / "Detenciones.txt"
        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Importing detenciones from {file_path}...")

        # Build lookup dicts for faster access
        lugares_by_codigo = {lugar.codigo: lugar for lugar in LugarModel.objects.all()}
        units_by_number = {u.number: u for u in MaintenanceUnitModel.objects.all()}
        intervenciones_by_codigo = {
            i.codigo: i for i in IntervencionTipoModel.objects.all()
        }

        created = 0
        skipped = 0
        batch = []
        batch_size = 1000

        with open(file_path, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    locs = row["Locs"].strip()
                    fecha_desde_str = row["Fecha_desde"].strip()
                    fecha_hasta_str = row.get("Fecha_hasta", "").strip()
                    intervencion_codigo = row["Intervencion"].strip()
                    lugar_codigo_str = row.get("Lugar", "").strip()
                    observaciones = row.get("Observaciones", "").strip() or None
                    fecha_est_str = row.get("Fecha_est", "").strip()

                    # Parse dates
                    fecha_desde = self._parse_date(fecha_desde_str)
                    if not fecha_desde:
                        skipped += 1
                        continue

                    fecha_hasta = (
                        self._parse_date(fecha_hasta_str) if fecha_hasta_str else None
                    )
                    fecha_estimada = (
                        self._parse_date(fecha_est_str) if fecha_est_str else None
                    )

                    # Get intervention type from FK
                    intervencion = intervenciones_by_codigo.get(intervencion_codigo)
                    legacy_intervencion_codigo = (
                        intervencion_codigo if not intervencion else None
                    )

                    # Get maintenance unit
                    maintenance_unit = units_by_number.get(locs)

                    # Get lugar
                    lugar = None
                    legacy_lugar_codigo = None
                    if lugar_codigo_str:
                        try:
                            lugar_codigo = int(lugar_codigo_str)
                            lugar = lugares_by_codigo.get(lugar_codigo)
                            if not lugar:
                                legacy_lugar_codigo = lugar_codigo
                        except ValueError:
                            pass

                    if dry_run:
                        created += 1
                        continue

                    novedad = NovedadModel(
                        id=uuid.uuid4(),
                        maintenance_unit=maintenance_unit,
                        legacy_unit_code=locs if not maintenance_unit else None,
                        fecha_desde=fecha_desde,
                        fecha_hasta=fecha_hasta,
                        fecha_estimada=fecha_estimada,
                        intervencion=intervencion,
                        legacy_intervencion_codigo=legacy_intervencion_codigo,
                        lugar=lugar,
                        legacy_lugar_codigo=legacy_lugar_codigo,
                        observaciones=observaciones,
                        is_legacy=True,
                    )
                    batch.append(novedad)
                    created += 1

                    # Bulk insert in batches
                    if len(batch) >= batch_size:
                        NovedadModel.objects.bulk_create(batch)
                        self.stdout.write(f"  Inserted {created} records...")
                        batch = []

                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  Error: {e}"))
                    skipped += 1

        # Insert remaining records
        if batch and not dry_run:
            NovedadModel.objects.bulk_create(batch)

        self.stdout.write(
            self.style.SUCCESS(f"Detenciones: {created} created, {skipped} skipped")
        )

    def import_detenciones_ccrr(self, path: Path, dry_run: bool = False):
        """Import detenciones CCRR from DetencionesCCRR.txt."""
        import sys

        file_path = path / "DetencionesCCRR.txt"
        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Importing detenciones CCRR from {file_path}...")

        # Count total lines for progress
        with open(file_path, "r", encoding="latin-1") as f:
            total_lines = sum(1 for _ in f) - 1  # -1 for header
        self.stdout.write(f"Total records to process: {total_lines}")

        # Build lookup dicts for faster access
        self.stdout.write("Building lookup dictionaries...")
        lugares_by_codigo = {lugar.codigo: lugar for lugar in LugarModel.objects.all()}
        units_by_number = {u.number: u for u in MaintenanceUnitModel.objects.all()}
        intervenciones_by_codigo = {
            i.codigo: i for i in IntervencionTipoModel.objects.all()
        }
        self.stdout.write(
            f"  Lugares: {len(lugares_by_codigo)}, Units: {len(units_by_number)}, "
            f"Intervenciones: {len(intervenciones_by_codigo)}"
        )

        # Build set of existing records for duplicate detection
        # Key: (unit_number, fecha_desde, intervencion_codigo, lugar_codigo)
        self.stdout.write("Loading existing records for duplicate detection...")
        existing_records = set()
        for nov in NovedadModel.objects.filter(is_legacy=True).values(
            "maintenance_unit__number",
            "legacy_unit_code",
            "fecha_desde",
            "intervencion__codigo",
            "legacy_intervencion_codigo",
            "lugar__codigo",
            "legacy_lugar_codigo",
        ):
            unit_num = nov["maintenance_unit__number"] or nov["legacy_unit_code"]
            interv = nov["intervencion__codigo"] or nov["legacy_intervencion_codigo"]
            lugar = nov["lugar__codigo"] or nov["legacy_lugar_codigo"]
            key = (unit_num, str(nov["fecha_desde"]), interv, str(lugar))
            existing_records.add(key)
        self.stdout.write(f"  Loaded {len(existing_records)} existing records")

        created = 0
        skipped = 0
        duplicates = 0
        processed = 0
        batch = []
        batch_size = 1000

        with open(file_path, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)

            for row in reader:
                processed += 1

                # Progress indicator every 5000 records
                if processed % 5000 == 0:
                    pct = (processed / total_lines) * 100
                    self.stdout.write(
                        f"  Progress: {processed}/{total_lines} ({pct:.1f}%) - "
                        f"created: {created}, skipped: {skipped}, duplicates: {duplicates}"
                    )
                    sys.stdout.flush()

                try:
                    coche = row["Coche"].strip()
                    fecha_desde_str = row["Fecha_desde"].strip()
                    fecha_hasta_str = row.get("Fecha_hasta", "").strip()
                    intervencion_codigo = row["Intervencion"].strip()
                    lugar_codigo_str = row.get("Lugar", "").strip()
                    observaciones = row.get("Observaciones", "").strip() or None
                    fecha_est_str = row.get("Fecha_est", "").strip()

                    # Parse dates
                    fecha_desde = self._parse_date(fecha_desde_str)
                    if not fecha_desde:
                        skipped += 1
                        continue

                    # Check for duplicate
                    dup_key = (
                        coche,
                        str(fecha_desde),
                        intervencion_codigo,
                        lugar_codigo_str,
                    )
                    if dup_key in existing_records:
                        duplicates += 1
                        continue

                    fecha_hasta = (
                        self._parse_date(fecha_hasta_str) if fecha_hasta_str else None
                    )
                    fecha_estimada = (
                        self._parse_date(fecha_est_str) if fecha_est_str else None
                    )

                    # Get intervention type from FK
                    intervencion = intervenciones_by_codigo.get(intervencion_codigo)
                    legacy_intervencion_codigo = (
                        intervencion_codigo if not intervencion else None
                    )

                    # Get maintenance unit
                    maintenance_unit = units_by_number.get(coche)
                    legacy_unit_code = coche if not maintenance_unit else None

                    # Get lugar
                    lugar = None
                    legacy_lugar_codigo = None
                    if lugar_codigo_str:
                        try:
                            lugar_codigo = int(lugar_codigo_str)
                            lugar = lugares_by_codigo.get(lugar_codigo)
                            if not lugar:
                                legacy_lugar_codigo = lugar_codigo
                        except ValueError:
                            pass

                    if dry_run:
                        created += 1
                        continue

                    novedad = NovedadModel(
                        id=uuid.uuid4(),
                        maintenance_unit=maintenance_unit,
                        legacy_unit_code=legacy_unit_code,
                        fecha_desde=fecha_desde,
                        fecha_hasta=fecha_hasta,
                        fecha_estimada=fecha_estimada,
                        intervencion=intervencion,
                        legacy_intervencion_codigo=legacy_intervencion_codigo,
                        lugar=lugar,
                        legacy_lugar_codigo=legacy_lugar_codigo,
                        observaciones=observaciones,
                        is_legacy=True,
                    )
                    batch.append(novedad)
                    # Add to existing set to avoid duplicates within batch
                    existing_records.add(dup_key)
                    created += 1

                    # Bulk insert in batches
                    if len(batch) >= batch_size:
                        NovedadModel.objects.bulk_create(batch)
                        batch = []

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"  Error at row {processed}: {e}")
                    )
                    skipped += 1

        # Insert remaining records
        if batch and not dry_run:
            NovedadModel.objects.bulk_create(batch)

        self.stdout.write(
            self.style.SUCCESS(
                f"Detenciones CCRR: {created} created, {skipped} skipped, {duplicates} duplicates"
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
