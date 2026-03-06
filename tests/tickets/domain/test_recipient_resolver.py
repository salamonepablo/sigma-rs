"""Pruebas de negocio para resolución de destinatarios."""

from apps.tickets.domain.services.recipient_resolution import (
    RecipientConfig,
    RecipientResolver,
)


class TestRecipientResolver:
    """Pruebas de negocio para resolver destinatarios."""

    def test_prefers_specific_lugar(self):
        resolver = RecipientResolver()
        recipients = [
            RecipientConfig(
                lugar_id="1",
                unit_type="locomotora",
                recipient_type="to",
                email="to@example.com",
            ),
            RecipientConfig(
                lugar_id=None,
                unit_type="locomotora",
                recipient_type="cc",
                email="default@example.com",
            ),
        ]

        resolution = resolver.resolve("1", "locomotora", recipients)
        assert resolution.to == ["to@example.com"]
        assert resolution.cc == []
        assert resolution.status == "ok"

    def test_falls_back_to_default(self):
        resolver = RecipientResolver()
        recipients = [
            RecipientConfig(
                lugar_id=None,
                unit_type="coche_remolcado",
                recipient_type="to",
                email="default@example.com",
            )
        ]

        resolution = resolver.resolve("99", "coche_remolcado", recipients)
        assert resolution.to == ["default@example.com"]
        assert resolution.status == "ok"
