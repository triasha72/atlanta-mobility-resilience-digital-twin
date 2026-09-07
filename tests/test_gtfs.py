from zipfile import ZipFile

from amrdt.gtfs import (
    active_service_ids,
    audit_gtfs_feed,
    haversine_meters,
    walking_transfer_minutes,
)


def test_audits_required_gtfs_files_without_retaining_rows(tmp_path) -> None:
    feed = tmp_path / "marta.zip"
    contents = {
        "agency.txt": "agency_id,agency_name\nMARTA,MARTA\n",
        "routes.txt": "route_id,route_type\n1,1\n2,3\n",
        "trips.txt": "route_id,service_id,trip_id\n1,WEEKDAY,T1\n",
        "stops.txt": "stop_id,stop_name\nS1,Stop\n",
        "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\nT1,08:00:00,08:00:00,S1,1\n",
        "calendar.txt": "service_id,monday,start_date,end_date\nWEEKDAY,1,20260101,20261231\n",
    }
    with ZipFile(feed, "w") as archive:
        for name, value in contents.items():
            archive.writestr(name, value)

    receipt = audit_gtfs_feed(feed, source_url="https://example.test/marta.zip")

    assert receipt["row_counts"]["stops.txt"] == 1
    assert receipt["route_type_counts"] == {"1": 1, "3": 1}
    assert receipt["contains_source_rows"] is False


def test_service_date_and_walking_transfer_helpers(tmp_path) -> None:
    feed = tmp_path / "marta.zip"
    with ZipFile(feed, "w") as archive:
        archive.writestr("calendar.txt", "service_id,monday,start_date,end_date\nWK,1,20260101,20261231\n")
        archive.writestr(
            "calendar_dates.txt",
            "service_id,date,exception_type\nWK,20260105,2\nSAT,20260106,1\n",
        )
    assert active_service_ids(feed, "20260105") == set()
    assert active_service_ids(feed, "20260106") == {"SAT"}
    assert walking_transfer_minutes(400) == 5.0
    assert 100 < haversine_meters(33.75, -84.39, 33.751, -84.39) < 120
