import pandas as pd

from amrdt.census import build_tract_origins, parse_census_reporter


def _payload(geoid="14000US13121000100", population=100):
    return {
        "release": {"id": "acs2024_5yr", "years": "2020-2024"},
        "data": {
            geoid: {
                "B01003": {
                    "estimate": {"B01003001": population},
                    "error": {"B01003001": 12},
                },
                "B19013": {
                    "estimate": {"B19013001": 75000},
                    "error": {"B19013001": 8000},
                },
            }
        },
    }


def test_parse_census_reporter_keeps_estimate_and_uncertainty():
    frame = parse_census_reporter(_payload())
    assert frame.loc[0, "geoid"] == "13121000100"
    assert frame.loc[0, "population_moe"] == 12
    assert frame.loc[0, "acs_release"] == "acs2024_5yr"


def test_build_origins_joins_coordinates_filters_and_normalizes(tmp_path):
    gazetteer = tmp_path / "tracts.txt"
    pd.DataFrame(
        {
            "GEOID": ["13121000100", "13089000200"],
            "INTPTLAT": [33.758, 34.5],
            "INTPTLONG": [-84.388, -84.0],
        }
    ).to_csv(gazetteer, sep="\t", index=False)

    frame = build_tract_origins(
        [_payload(), _payload("14000US13089000200", 200)],
        gazetteer,
        center_lat=33.758,
        center_lon=-84.388,
        radius_km=5,
    )

    assert frame["geoid"].tolist() == ["13121000100"]
    assert frame.loc[0, "population_weight"] == 1.0
