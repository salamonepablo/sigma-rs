"""Pruebas de negocio para sugerencia de intervención."""

from datetime import date

from apps.tickets.domain.services.intervention_suggestion import (
    InterventionHistoryItem,
    InterventionPriorityResolver,
    InterventionSuggestionService,
    MaintenanceCycle,
)


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
