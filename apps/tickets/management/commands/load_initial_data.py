"""Management command to load initial reference data and maintenance units.

Usage:
    python manage.py load_initial_data
"""

import csv
import uuid
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.tickets.infrastructure.models import (
    AffectedSystemModel,
    BrandModel,
    FailureTypeModel,
    GOPModel,
    LocomotiveModel,
    LocomotiveModelModel,
    MaintenanceUnitModel,
    MotorcoachModel,
    RailcarClassModel,
    RailcarModel,
)


class Command(BaseCommand):
    """Load initial data from CSV files into the database."""

    help = "Load initial reference data and maintenance units from CSV files"

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write("Loading initial data...")

        # Load reference data first
        self._load_brands()
        self._load_locomotive_models()
        self._load_railcar_classes()
        self._load_gops()
        self._load_failure_types()

        # Load maintenance units
        self._load_maintenance_units()

        self.stdout.write(self.style.SUCCESS("Initial data loaded successfully!"))

    def _load_brands(self):
        """Load manufacturer brands."""
        brands = [
            {"code": "GM", "name": "GM", "full_name": "General Motors"},
            {"code": "CNR", "name": "Dalian CNR", "full_name": "CNR Dalian Locomotive & Rolling Stock Co."},
            {"code": "MTF", "name": "Materfer", "full_name": "Material Ferroviario S.A."},
            {"code": "NOHAB", "name": "Nohab", "full_name": "Nydqvist & Holm AB"},
        ]

        for brand_data in brands:
            brand, created = BrandModel.objects.get_or_create(
                code=brand_data["code"],
                defaults={
                    "id": uuid.uuid4(),
                    "name": brand_data["name"],
                    "full_name": brand_data["full_name"],
                },
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  Brand {brand.name}: {status}")

    def _load_locomotive_models(self):
        """Load locomotive model specifications."""
        gm_brand = BrandModel.objects.get(code="GM")
        cnr_brand = BrandModel.objects.get(code="CNR")

        models = [
            {"code": "G22-CW", "name": "G22-CW", "brand": gm_brand},
            {"code": "GT22-CW", "name": "GT22-CW", "brand": gm_brand},
            {"code": "GT22-CW-2", "name": "GT22-CW-2", "brand": gm_brand},
            {"code": "CKD8G", "name": "CKD8G", "brand": cnr_brand},
        ]

        for model_data in models:
            model, created = LocomotiveModelModel.objects.get_or_create(
                code=model_data["code"],
                defaults={
                    "id": uuid.uuid4(),
                    "name": model_data["name"],
                    "brand": model_data["brand"],
                },
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  Locomotive model {model.name}: {status}")

    def _load_railcar_classes(self):
        """Load railcar class specifications."""
        cnr_brand = BrandModel.objects.get(code="CNR")
        mtf_brand = BrandModel.objects.get(code="MTF")

        classes = [
            # CNR classes
            {"code": "CDA", "name": "CDA", "brand": cnr_brand},
            {"code": "CPA", "name": "CPA", "brand": cnr_brand},
            {"code": "CRA", "name": "CRA", "brand": cnr_brand},
            {"code": "FG", "name": "FG", "brand": cnr_brand},
            {"code": "FS", "name": "FS", "brand": cnr_brand},
            {"code": "PUA", "name": "PUA", "brand": cnr_brand},
            {"code": "PUAD", "name": "PUAD", "brand": cnr_brand},
            # Materfer classes
            {"code": "FURGON_UNICA", "name": "Furgon Unica", "brand": mtf_brand},
            {"code": "UNICA", "name": "Unica", "brand": mtf_brand},
        ]

        for class_data in classes:
            railcar_class, created = RailcarClassModel.objects.get_or_create(
                code=class_data["code"],
                defaults={
                    "id": uuid.uuid4(),
                    "name": class_data["name"],
                    "brand": class_data["brand"],
                },
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  Railcar class {railcar_class.name}: {status}")

    def _load_gops(self):
        """Load operational guards (GOPs)."""
        gops = [
            {"code": "PMRE", "name": "Playa Mecánica Remedios de Escalada"},
            {"code": "TY", "name": "Guardia Temperley"},
            {"code": "PC", "name": "Guardia Plaza C."},
            {"code": "MPN", "name": "Guardia Mar del Plata"},
            {"code": "CA", "name": "Guardia Cañuelas"},
            {"code": "PU", "name": "Guardia Maipú"},
        ]

        for gop_data in gops:
            gop, created = GOPModel.objects.get_or_create(
                code=gop_data["code"],
                defaults={
                    "id": uuid.uuid4(),
                    "name": gop_data["name"],
                },
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  GOP {gop.code}: {status}")

    def _load_failure_types(self):
        """Load failure types and their default affected systems."""
        # Failure types with their default affected system
        failure_types = [
            {"code": "MEC", "name": "Mecánicas", "system": "Sistema Mecánico"},
            {"code": "ELE", "name": "Eléctricas", "system": "Sistema Eléctrico"},
            {"code": "NEU", "name": "Neumáticas", "system": "Sistema Neumático"},
            {"code": "ELEC", "name": "Electrónicas", "system": "Sistema Electrónico"},
            {"code": "OTR", "name": "Otras", "system": "Otro"},
            {"code": "ATS", "name": "Falla de ATS", "system": "ATS"},
            {"code": "HASLER", "name": "Falla de Hasler", "system": "Hasler"},
            {"code": "HV", "name": "Falla de Hombre Vivo", "system": "Hombre Vivo"},
        ]

        for ft_data in failure_types:
            # Create failure type
            failure_type, ft_created = FailureTypeModel.objects.get_or_create(
                code=ft_data["code"],
                defaults={
                    "id": uuid.uuid4(),
                    "name": ft_data["name"],
                },
            )
            ft_status = "created" if ft_created else "exists"
            self.stdout.write(f"  Failure type {failure_type.name}: {ft_status}")

            # Create default affected system for this failure type
            system, sys_created = AffectedSystemModel.objects.get_or_create(
                code=ft_data["code"],
                failure_type=failure_type,
                defaults={
                    "id": uuid.uuid4(),
                    "name": ft_data["system"],
                },
            )
            sys_status = "created" if sys_created else "exists"
            self.stdout.write(f"    -> System {system.name}: {sys_status}")

    def _load_maintenance_units(self):
        """Load maintenance units from CSV file."""
        csv_path = Path("context/ums.csv")

        if not csv_path.exists():
            self.stdout.write(self.style.WARNING(f"CSV file not found: {csv_path}"))
            return

        # Pre-load brands and models for faster lookups
        brands = {b.code: b for b in BrandModel.objects.all()}
        # Map CSV brand names to brand codes
        brand_mapping = {
            "GM": "GM",
            "Dalian CNR": "CNR",
            "CNR": "CNR",
            "Materfer": "MTF",
            "Nohab": "NOHAB",
        }

        loco_models = {m.code: m for m in LocomotiveModelModel.objects.all()}
        railcar_classes = {c.code: c for c in RailcarClassModel.objects.all()}

        # Map CSV class names to class codes
        class_mapping = {
            "CDA": "CDA",
            "CPA": "CPA",
            "CRA": "CRA",
            "FG": "FG",
            "FS": "FS",
            "PUA": "PUA",
            "PUAD": "PUAD",
            "Furgon Unica": "FURGON_UNICA",
            "Unica": "UNICA",
        }

        counts = {"locomotora": 0, "coche_remolcado": 0, "coche_motor": 0, "skipped": 0}

        with open(csv_path, encoding="latin-1") as f:
            reader = csv.DictReader(f, delimiter=";")

            for row in reader:
                unit_number = row["Unidad de Mantenimiento"].strip()
                unit_type_csv = row["Tipo"].strip()
                brand_name = row["Marca"].strip()
                model_name = row.get("Modelo", "").strip()
                class_name = row.get("Clase", "").strip()
                car_count = row.get("Cantidad Coches", "").strip()
                configuration = row.get("Conformación", "").strip()

                # Skip if unit already exists
                if MaintenanceUnitModel.objects.filter(number=unit_number).exists():
                    counts["skipped"] += 1
                    continue

                # Get brand
                brand_code = brand_mapping.get(brand_name)
                if not brand_code or brand_code not in brands:
                    self.stdout.write(
                        self.style.WARNING(f"  Unknown brand: {brand_name} for unit {unit_number}")
                    )
                    continue

                brand = brands[brand_code]

                try:
                    if unit_type_csv == "Locomotora":
                        self._create_locomotive(
                            unit_number, brand, model_name, loco_models
                        )
                        counts["locomotora"] += 1

                    elif unit_type_csv == "Coche Remolcado":
                        class_code = class_mapping.get(class_name)
                        if class_code and class_code in railcar_classes:
                            self._create_railcar(
                                unit_number, brand, railcar_classes[class_code]
                            )
                            counts["coche_remolcado"] += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  Unknown railcar class: {class_name} for unit {unit_number}"
                                )
                            )

                    elif unit_type_csv == "Coche Motor":
                        self._create_motorcoach(
                            unit_number, brand, configuration, car_count
                        )
                        counts["coche_motor"] += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  Error creating unit {unit_number}: {e}")
                    )

        self.stdout.write(
            f"  Locomotives: {counts['locomotora']}, "
            f"Railcars: {counts['coche_remolcado']}, "
            f"Motorcoaches: {counts['coche_motor']}, "
            f"Skipped: {counts['skipped']}"
        )

    def _create_locomotive(self, number, brand, model_name, loco_models):
        """Create a locomotive maintenance unit."""
        # Normalize model name (handle variations like G22-CW vs G22CW)
        model_code = model_name.replace(" ", "")
        loco_model = loco_models.get(model_code)

        if not loco_model:
            self.stdout.write(
                self.style.WARNING(f"  Unknown locomotive model: {model_name} for unit {number}")
            )
            return

        unit_id = uuid.uuid4()

        # Create base maintenance unit
        MaintenanceUnitModel.objects.create(
            id=unit_id,
            number=number,
            unit_type=MaintenanceUnitModel.UnitType.LOCOMOTIVE,
        )

        # Create locomotive
        LocomotiveModel.objects.create(
            maintenance_unit_id=unit_id,
            brand=brand,
            model=loco_model,
        )

    def _create_railcar(self, number, brand, railcar_class):
        """Create a railcar maintenance unit."""
        unit_id = uuid.uuid4()

        # Create base maintenance unit
        MaintenanceUnitModel.objects.create(
            id=unit_id,
            number=number,
            unit_type=MaintenanceUnitModel.UnitType.RAILCAR,
        )

        # Create railcar
        RailcarModel.objects.create(
            maintenance_unit_id=unit_id,
            brand=brand,
            railcar_class=railcar_class,
        )

    def _create_motorcoach(self, number, brand, configuration, car_count):
        """Create a motorcoach maintenance unit."""
        unit_id = uuid.uuid4()

        # Create base maintenance unit
        MaintenanceUnitModel.objects.create(
            id=unit_id,
            number=number,
            unit_type=MaintenanceUnitModel.UnitType.MOTORCOACH,
        )

        # Create motorcoach
        MotorcoachModel.objects.create(
            maintenance_unit_id=unit_id,
            brand=brand,
            configuration=configuration or "CM",
            car_count=int(car_count) if car_count else 1,
        )
