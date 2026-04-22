from app.services.tle_client import parse_tle_file


def test_parse_valid_tle():
    raw = """ISS (ZARYA)
1 25544U 98067A   24112.51303241  .00018627  00000+0  33441-3 0  9993
2 25544  51.6411 132.2489 0002107  58.3917  62.4303 15.49896559448988"""

    result = parse_tle_file(raw)

    assert len(result) == 1
    assert result[0]["name"] == "ISS (ZARYA)"
    assert result[0]["norad_id"] == 25544
    assert result[0]["line1"].startswith("1")
    assert result[0]["line2"].startswith("2")


def test_parse_skips_malformed_block():
    raw = """BAD SATELLITE
X 99999 bad data here
Y 99999 also bad
ISS (ZARYA)
1 25544U 98067A   24112.51303241  .00018627  00000+0  33441-3 0  9993
2 25544  51.6411 132.2489 0002107  58.3917  62.4303 15.49896559448988"""

    result = parse_tle_file(raw)
    assert len(result) == 1
    assert result[0]["name"] == "ISS (ZARYA)"