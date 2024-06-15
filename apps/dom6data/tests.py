from apps.dom6data.autocalc import has_random, round_if_needed, round_up, special_round


def test_round_if_needed():
    assert round_if_needed(36) == 35
    assert round_if_needed(35) == 35
    assert round_if_needed(40) == 40
    assert round_if_needed(42) == 40
    assert round_if_needed(45) == 45
    assert round_if_needed(47) == 45

    assert round_if_needed(30) == 30
    assert round_if_needed(29) == 29
    assert round_if_needed(28) == 28
    assert round_if_needed(25) == 25
    assert round_if_needed(23) == 23

    assert round_if_needed(-35) == -35
    assert round_if_needed(-40) == -40
    assert round_if_needed(-42) == -42
    assert round_if_needed(-45) == -45
    assert round_if_needed(-47) == -47

    assert round_if_needed(35.3) == 35
    assert round_if_needed(40.7) == 40
    assert round_if_needed(28.5) == 28
    assert round_if_needed(25.2) == 25
    assert round_if_needed(23.8) == 23

    assert round_if_needed(0) == 0


def test_special_round():
    assert special_round(10) == 10
    assert special_round(12) == 10
    assert special_round(15) == 15
    assert special_round(17) == 15
    assert special_round(11) == 10
    assert special_round(13) == 10
    assert special_round(16) == 15
    assert special_round(18) == 15
    assert special_round(-10) == -10
    assert special_round(-12) == -15
    assert special_round(-15) == -15
    assert special_round(-17) == -20
    assert special_round(12.3) == 10
    assert special_round(14.7) == 10
    assert special_round(16.5) == 15
    assert special_round(0) == 0


def test_round_up():
    assert round_up(135) == 135
    assert round_up(137) == 140
    assert round_up(12) == 15
    assert round_up(17) == 20
    assert round_up(23) == 25
    assert round_up(28) == 30
    assert round_up(33) == 35
    assert round_up(12.3) == 15
    assert round_up(17.7) == 20
    assert round_up(23.2) == 25
    assert round_up(28.6) == 30
    assert round_up(33.9) == 35
    assert round_up(-12) == -10
    assert round_up(-17) == -15
    assert round_up(-23) == -20
    assert round_up(-28) == -25
    assert round_up(-33) == -30
    assert round_up(0) == 0
    assert round_up(1000000) == 1000000
    assert round_up(1000000.5) == 1000005
    assert round_up(1000000000) == 1000000000
    assert round_up(1000000000.5) == 1000000005


def test_has_random():
    obj = {
        "randompaths": [],
    }
    assert has_random(obj) is False

    obj = {
        "randompaths": [
            {"chance": 0, "paths": "FA"},
            {"chance": 0, "paths": "WE"},
            {"chance": 0, "paths": "DS"},
            {"chance": 0, "paths": "NB"},
        ],
    }
    assert has_random(obj) is False

    obj = {
        "randompaths": [
            {"chance": 50, "paths": "FA"},
            {"chance": 50, "paths": "WE"},
            {"chance": 50, "paths": "DS"},
            {"chance": 50, "paths": "NB"},
        ],
    }
    assert has_random(obj) is False

    obj = {
        "randompaths": [
            {"chance": 100, "paths": "FA"},
            {"chance": 100, "paths": "WE"},
            {"chance": 100, "paths": "DS"},
            {"chance": 100, "paths": "NB"},
        ],
    }
    assert has_random(obj) is True

    obj = {
        "randompaths": [
            {"chance": 0, "paths": "FA"},
            {"chance": 50, "paths": "WE"},
            {"chance": 100, "paths": "DS"},
            {"chance": 0, "paths": "NB"},
        ],
    }
    assert has_random(obj) is True
