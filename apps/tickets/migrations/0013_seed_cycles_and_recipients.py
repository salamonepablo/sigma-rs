"""Seed maintenance cycles and default recipients."""

from __future__ import annotations

from django.db import migrations


def seed_cycles_and_recipients(apps, schema_editor):
    """Seed base maintenance cycles and email recipients."""

    BrandModel = apps.get_model("tickets", "BrandModel")
    LocomotiveModelModel = apps.get_model("tickets", "LocomotiveModelModel")
    MaintenanceCycleModel = apps.get_model("tickets", "MaintenanceCycleModel")
    LugarEmailRecipientModel = apps.get_model("tickets", "LugarEmailRecipientModel")

    def get_brand(code: str, name: str):
        brand = BrandModel.objects.filter(code__iexact=code).first()
        if not brand:
            brand = BrandModel.objects.filter(name__iexact=name).first()
        if not brand:
            brand = BrandModel.objects.create(code=code, name=name)
        return brand

    def get_model(code: str, name: str, brand):
        model = LocomotiveModelModel.objects.filter(code__iexact=code).first()
        if not model:
            model = LocomotiveModelModel.objects.filter(name__iexact=name).first()
        if not model:
            model = LocomotiveModelModel.objects.create(
                code=code, name=name, brand=brand
            )
        return model

    gm = get_brand("GM", "GM")
    cnr = get_brand("CNR", "CNR")
    materfer = get_brand("Materfer", "Materfer")
    nohab = get_brand("Nohab", "Nohab")

    ckd8g = get_model("CKD8G", "CKD8G", cnr)

    cycles = [
        # Locomotora GM
        ("locomotora", gm, None, "A", "Revisión A", "km", 16000, "km"),
        ("locomotora", gm, None, "AB", "Revisión AB", "km", 50000, "km"),
        ("locomotora", gm, None, "ABC", "Revisión ABC", "km", 100000, "km"),
        ("locomotora", gm, None, "N1", "Reparación Numeral 1", "km", 200000, "km"),
        ("locomotora", gm, None, "N2", "Reparación Numeral 2", "km", 400000, "km"),
        ("locomotora", gm, None, "N3", "Reparación Numeral 3", "km", 600000, "km"),
        ("locomotora", gm, None, "N4", "Reparación Numeral 4", "km", 800000, "km"),
        ("locomotora", gm, None, "N5", "Reparación Numeral 5", "km", 1000000, "km"),
        ("locomotora", gm, None, "N6", "Reparación Numeral 6", "km", 1200000, "km"),
        ("locomotora", gm, None, "N7", "Reparación Numeral 7", "km", 1400000, "km"),
        ("locomotora", gm, None, "N8", "Reparación Numeral 8", "km", 1600000, "km"),
        ("locomotora", gm, None, "N9", "Reparación Numeral 9", "km", 1800000, "km"),
        ("locomotora", gm, None, "N10", "Reparación Numeral 10", "km", 2000000, "km"),
        ("locomotora", gm, None, "N11", "Reparación Numeral 11", "km", 2200000, "km"),
        ("locomotora", gm, None, "RG", "Reparación General", "km", 2400000, "km"),
        # Locomotora CKD 8G
        ("locomotora", cnr, ckd8g, "EX", "Examen", "km", 10000, "km"),
        ("locomotora", cnr, ckd8g, "R1", "Revisión 1", "km", 20000, "km"),
        ("locomotora", cnr, ckd8g, "R2", "Revisión 2", "km", 40000, "km"),
        ("locomotora", cnr, ckd8g, "R3", "Revisión 3", "km", 60000, "km"),
        ("locomotora", cnr, ckd8g, "R4", "Revisión 4", "km", 80000, "km"),
        ("locomotora", cnr, ckd8g, "R5", "Revisión 5", "km", 100000, "km"),
        ("locomotora", cnr, ckd8g, "R6", "Revisión 6", "km", 120000, "km"),
        ("locomotora", cnr, ckd8g, "360K", "Reparación Numeral 1", "km", 360000, "km"),
        ("locomotora", cnr, ckd8g, "720K", "Reparación Numeral 2", "km", 720000, "km"),
        # Coche Remolcado Materfer
        ("coche_remolcado", materfer, None, "A", "Revisión A", "km", 15000, "km"),
        ("coche_remolcado", materfer, None, "AB", "Revisión AB", "km", 30000, "km"),
        ("coche_remolcado", materfer, None, "ABC", "Revisión ABC", "km", 120000, "km"),
        (
            "coche_remolcado",
            materfer,
            None,
            "RP",
            "Reparación Parcial",
            "km",
            240000,
            "km",
        ),
        (
            "coche_remolcado",
            materfer,
            None,
            "RG",
            "Reparación General",
            "km",
            480000,
            "km",
        ),
        # Coche Remolcado CNR
        ("coche_remolcado", cnr, None, "MEN", "Revisión Mensual", "time", 1, "month"),
        ("coche_remolcado", cnr, None, "SEM", "Revisión Semestral", "time", 6, "month"),
        ("coche_remolcado", cnr, None, "A1", "Reparación A1", "km", 200000, "km"),
        ("coche_remolcado", cnr, None, "A2", "Reparación A2", "km", 400000, "km"),
        ("coche_remolcado", cnr, None, "A3", "Reparación A3", "km", 800000, "km"),
        # Coche Motor Nohab
        ("coche_motor", nohab, None, "MEN", "Revisión Mensual", "time", 1, "month"),
        ("coche_motor", nohab, None, "SEM", "Revisión Semestral", "time", 6, "month"),
        ("coche_motor", nohab, None, "RP", "Reparación Parcial", "km", 240000, "km"),
        ("coche_motor", nohab, None, "RG", "Reparación General", "km", 480000, "km"),
    ]

    for (
        rolling_stock_type,
        brand,
        model,
        code,
        name,
        trigger_type,
        trigger_value,
        trigger_unit,
    ) in cycles:
        MaintenanceCycleModel.objects.get_or_create(
            rolling_stock_type=rolling_stock_type,
            brand=brand,
            model=model,
            intervention_code=code,
            trigger_type=trigger_type,
            trigger_value=trigger_value,
            trigger_unit=trigger_unit,
            defaults={
                "intervention_name": name,
                "is_active": True,
            },
        )

    recipients = {
        "locomotora": {
            "to": [
                "andres.kennel@trenesargentinos.gob.ar",
                "marcos.vazquez@trenesargentinos.gob.ar",
            ],
            "cc": [
                "IngresoLocomotasTRE@trenesargentinos.gob.ar",
                "PedidosSimafLGR@trenesargentinos.gob.ar",
                "pabloj.garcia@trenesargentinos.gob.ar",
                "guido.osardo@trenesargentinos.gob.ar",
                "norberto.keim@trenesargentinos.gob.ar",
                "gianluca.marsano@trenesargentinos.gob.ar",
                "malena.mendoza@trenesargentinos.gob.ar",
                "daniel.pereyra@trenesargentinos.gob.ar",
                "jose.barrios@trenesargentinos.gob.ar",
            ],
        },
        "coche_remolcado": {
            "to": [
                "andres.kennel@trenesargentinos.gob.ar",
                "horacio.toral@trenesargentinos.gob.ar",
            ],
            "cc": [
                "luis.tedesco@trenesargentinos.gob.ar",
                "carlosf.escobar@trenesargentinos.gob.ar",
                "hernan.hermoza@trenesargentinos.gob.ar",
                "javier.sequeira@trenesargentinos.gob.ar",
                "hernan.baigorria@trenesargentinos.gob.ar",
                "raulr.castro@trenesargentinos.gob.ar",
                "silvio.biocca@trenesargentinos.gob.ar",
                "guillermo.pereira@trenesargentinos.gob.ar",
                "jose.barrios@trenesargentinos.gob.ar",
                "ariel.delas@trenesargentinos.gob.ar",
                "fernando.ferian@trenesargentinos.gob.ar",
                "brian.fernandez@trenesargentinos.gob.ar",
                "JefaturadeCochesRemolcadosLGR@trenesargentinos.gob.ar",
                "martin.vaca@trenesargentinos.gob.ar",
                "emanuel.cordoba@trenesargentinos.gob.ar",
                "alexander.mitriani@trenesargentinos.gob.ar",
                "supervisorescochestre@trenesargentinos.gob.ar",
                "Pedidos-de-ultrasonido@trenesargentinos.gob.ar",
                "milagros.leonar@trenesargentinos.gob.ar",
                "pedidosSimafLGR@trenesargentinos.gob.ar",
            ],
        },
    }

    for unit_type, groups in recipients.items():
        for recipient_type, emails in groups.items():
            for email in emails:
                LugarEmailRecipientModel.objects.get_or_create(
                    lugar=None,
                    unit_type=unit_type,
                    recipient_type=recipient_type,
                    email=email,
                    defaults={"is_active": True},
                )


def unseed_cycles_and_recipients(apps, schema_editor):
    """Remove seeded cycles and recipients."""

    MaintenanceCycleModel = apps.get_model("tickets", "MaintenanceCycleModel")
    LugarEmailRecipientModel = apps.get_model("tickets", "LugarEmailRecipientModel")

    MaintenanceCycleModel.objects.all().delete()
    LugarEmailRecipientModel.objects.filter(lugar__isnull=True).delete()


class Migration(migrations.Migration):
    """Seed maintenance cycles and recipients."""

    dependencies = [
        ("tickets", "0012_add_maintenance_entry_cycle_and_recipients"),
    ]

    operations = [
        migrations.RunPython(seed_cycles_and_recipients, unseed_cycles_and_recipients)
    ]
