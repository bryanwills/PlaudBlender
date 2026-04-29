from datetime import date as date_cls

from app_v2.services import data_service as data_service_module


def _build_service(monkeypatch):
    monkeypatch.setattr(
        data_service_module.ChronosDataService,
        "_init_services",
        lambda self: None,
    )
    return data_service_module.ChronosDataService()


def test_recent_empty_days_are_marked_verified_or_suspected(monkeypatch):
    service = _build_service(monkeypatch)
    monkeypatch.setattr(
        service,
        "_get_recent_plaud_recording_dates",
        lambda _days_back: {"2026-04-17", "2026-04-19", "2026-04-20"},
    )

    days = [
        data_service_module.DaySummary(
            date="2026-04-20",
            date_display="Monday, Apr 20",
            total_duration_seconds=3600,
            recording_count=1,
            event_count=10,
        ),
        data_service_module.DaySummary(
            date="2026-04-19",
            date_display="Sunday, Apr 19",
            total_duration_seconds=0,
            recording_count=0,
            event_count=0,
        ),
        data_service_module.DaySummary(
            date="2026-04-18",
            date_display="Saturday, Apr 18",
            total_duration_seconds=0,
            recording_count=0,
            event_count=0,
        ),
        data_service_module.DaySummary(
            date="2026-04-17",
            date_display="Friday, Apr 17",
            total_duration_seconds=7200,
            recording_count=2,
            event_count=50,
        ),
    ]

    audited = service._apply_recent_empty_day_audit(
        days,
        start_dt=date_cls(2026, 4, 17),
        end_dt=date_cls(2026, 4, 20),
        today=date_cls(2026, 4, 20),
    )

    assert audited[1].coverage_status == "suspected_gap"
    assert audited[1].coverage_note == "Possible sync gap — Plaud shows recordings"
    assert audited[2].coverage_status == "verified_empty"
    assert audited[2].coverage_note == "Verified empty in Plaud"


def test_old_empty_days_skip_recent_plaud_audit(monkeypatch):
    service = _build_service(monkeypatch)

    def _unexpected_call(_days_back):
        raise AssertionError("Old ranges should not trigger a recent Plaud audit")

    monkeypatch.setattr(service, "_get_recent_plaud_recording_dates", _unexpected_call)

    days = [
        data_service_module.DaySummary(
            date="2026-01-10",
            date_display="Saturday, Jan 10",
            total_duration_seconds=0,
            recording_count=0,
            event_count=0,
        )
    ]

    audited = service._apply_recent_empty_day_audit(
        days,
        start_dt=date_cls(2026, 1, 10),
        end_dt=date_cls(2026, 1, 10),
        today=date_cls(2026, 4, 20),
    )

    assert audited[0].coverage_status is None
    assert audited[0].coverage_note is None