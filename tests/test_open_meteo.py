from custom_components.flynow.open_meteo import OpenMeteoError


def test_open_meteo_error_type():
    err = OpenMeteoError("boom")
    assert "boom" in str(err)
