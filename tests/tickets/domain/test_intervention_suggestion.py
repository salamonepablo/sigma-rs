"""Pruebas de negocio para sugerencia de intervención."""

from datetime import date

from apps.tickets.domain.services.intervention_suggestion import (
    InterventionHistoryItem,
    InterventionPriorityResolver,
    InterventionSuggestionService,
    MaintenanceCycle,
)

GM_CYCLES = [
    MaintenanceCycle("A", "Revisión A", "km", 16_000, "km"),
    MaintenanceCycle("AB", "Revisión AB", "km", 50_000, "km"),
    MaintenanceCycle("ABC", "Revisión ABC", "km", 100_000, "km"),
    MaintenanceCycle("N1", "Numeral 1", "km", 200_000, "km"),
    MaintenanceCycle("N2", "Numeral 2", "km", 400_000, "km"),
    MaintenanceCycle("N3", "Numeral 3", "km", 600_000, "km"),
    MaintenanceCycle("RG", "Reparación General", "km", 2_400_000, "km"),
]


class TestInterventionSuggestionService:
    """Pruebas de negocio para sugerir intervención."""

    def test_suggests_cycle_by_trigger_value(self):
        service = InterventionSuggestionService()
        cycles = [
            MaintenanceCycle(
                intervention_code="A",
                intervention_name="Revision A",
                trigger_type="km",
                trigger_value=16000,
                trigger_unit="km",
            ),
            MaintenanceCycle(
                intervention_code="AB",
                intervention_name="Revision AB",
                trigger_type="km",
                trigger_value=50000,
                trigger_unit="km",
            ),
            MaintenanceCycle(
                intervention_code="ABC",
                intervention_name="Revision ABC",
                trigger_type="km",
                trigger_value=100000,
                trigger_unit="km",
            ),
        ]
        history = [
            InterventionHistoryItem(
                intervention_code="ABC",
                date_from=date(2024, 1, 10),
                date_until=date(2024, 1, 15),
            )
        ]

        suggestion = service.suggest(
            unit_type="locomotora",
            brand_code="GM",
            model_code="GT22-CW",
            cycles=cycles,
            trigger_type="km",
            trigger_value=120000,
            history=history,
        )

        assert suggestion.suggested_code == "ABC"
        assert suggestion.last_intervention_code == "ABC"
        assert suggestion.status == "ok"

    def test_wagon_priority_list_uses_al_rev_a_b_order(self):
        resolver = InterventionPriorityResolver()

        priorities = resolver.resolve(
            unit_type="vagon",
            brand_code="Carga",
            model_code=None,
        )

        assert priorities == ["AL", "REV", "A", "B"]


class TestMaintenanceHistoryInheritance:
    """Regla de herencia: intervención de mayor rango pisa a las inferiores."""

    def _service(self) -> InterventionSuggestionService:
        return InterventionSuggestionService()

    def test_numeral_before_rg_is_not_shown(self):
        """N1 del 2017 no debe aparecer si la RG del 2021 la pisó (caso A710)."""
        service = self._service()
        history = [
            InterventionHistoryItem("RG", date(2021, 10, 19), date(2021, 10, 19)),
            InterventionHistoryItem("ABC", date(2024, 9, 4), date(2024, 9, 4)),
            InterventionHistoryItem("N1", date(2017, 2, 4), date(2017, 2, 4)),
        ]

        result = service.get_maintenance_history(
            unit_type="locomotora",
            brand_code="GM",
            model_code="G22-CW",
            cycles=GM_CYCLES,
            history=history,
        )

        assert result.last_rg_date == date(2021, 10, 19)
        # N1 ocurrió ANTES de la RG → la RG la pisó → debe estar vacío
        assert result.last_numeral_code is None
        assert result.last_numeral_date is None
        # ABC ocurrió DESPUÉS de la RG → debe mostrarse
        assert result.last_abc_code == "ABC"
        assert result.last_abc_date == date(2024, 9, 4)

    def test_numeral_after_rg_is_shown(self):
        """N2 posterior a la RG debe aparecer normalmente."""
        service = self._service()
        history = [
            InterventionHistoryItem("RG", date(2021, 10, 19), date(2021, 10, 19)),
            InterventionHistoryItem("N2", date(2023, 5, 1), date(2023, 5, 1)),
            InterventionHistoryItem("N1", date(2017, 2, 4), date(2017, 2, 4)),
        ]

        result = service.get_maintenance_history(
            unit_type="locomotora",
            brand_code="GM",
            model_code="G22-CW",
            cycles=GM_CYCLES,
            history=history,
        )

        assert result.last_numeral_code == "N2"
        assert result.last_numeral_date == date(2023, 5, 1)

    def test_abc_after_numeral_and_rg_is_shown(self):
        """ABC posterior a la última numeral (que está después de la RG) debe mostrarse."""
        service = self._service()
        history = [
            InterventionHistoryItem("RG", date(2021, 10, 19), date(2021, 10, 19)),
            InterventionHistoryItem("N1", date(2022, 8, 10), date(2022, 8, 10)),
            InterventionHistoryItem("ABC", date(2023, 3, 15), date(2023, 3, 15)),
        ]

        result = service.get_maintenance_history(
            unit_type="locomotora",
            brand_code="GM",
            model_code="G22-CW",
            cycles=GM_CYCLES,
            history=history,
        )

        assert result.last_numeral_code == "N1"
        assert result.last_abc_code == "ABC"
        assert result.last_abc_date == date(2023, 3, 15)

    def test_abc_before_numeral_is_not_shown(self):
        """ABC anterior a la N1 (post-RG) debe ser pisada por la N1."""
        service = self._service()
        history = [
            InterventionHistoryItem("RG", date(2021, 10, 19), date(2021, 10, 19)),
            InterventionHistoryItem("N1", date(2022, 8, 10), date(2022, 8, 10)),
            InterventionHistoryItem("ABC", date(2022, 1, 5), date(2022, 1, 5)),
        ]

        result = service.get_maintenance_history(
            unit_type="locomotora",
            brand_code="GM",
            model_code="G22-CW",
            cycles=GM_CYCLES,
            history=history,
        )

        assert result.last_numeral_code == "N1"
        # ABC ocurrió ANTES de N1 → N1 la pisó → debe estar vacío
        assert result.last_abc_code is None
        assert result.last_abc_date is None

    def test_rg_resets_all_lower_ranks(self):
        """Si la RG es hoy, numeral y ABC previos no deben aparecer."""
        service = self._service()
        history = [
            InterventionHistoryItem("RG", date(2026, 4, 15), date(2026, 4, 15)),
            InterventionHistoryItem("ABC", date(2024, 9, 4), date(2024, 9, 4)),
            InterventionHistoryItem("N3", date(2022, 6, 1), date(2022, 6, 1)),
        ]

        result = service.get_maintenance_history(
            unit_type="locomotora",
            brand_code="GM",
            model_code="G22-CW",
            cycles=GM_CYCLES,
            history=history,
        )

        assert result.last_rg_date == date(2026, 4, 15)
        assert result.last_numeral_code is None
        assert result.last_abc_code is None
