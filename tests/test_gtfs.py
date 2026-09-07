from zipfile import ZipFile

from amrdt.gtfs import audit_gtfs_feed


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
