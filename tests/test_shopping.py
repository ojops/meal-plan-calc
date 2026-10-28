from decimal import Decimal

from meal_plan_calc.shopping import calculate_shopping_quantities


def test_calculate_shopping_quantities_for_one_day():
    meals = {
        "monday": {"rice": "100", "chicken": "150"},
        "breakfast": {"oats": "75", "banana": "100"},
        "snack": {"banana": "50"},
        "supplements": {"creatine": "5"},
        "strength": {"rice": "25", "chicken": "50"},
    }

    result = calculate_shopping_quantities(
        ["monday"],
        meals,
        {"monday": "strength"},
    )

    assert result == {
        "rice": Decimal("125"),
        "chicken": Decimal("200"),
        "oats": Decimal("75"),
        "banana": Decimal("150"),
        "creatine": Decimal("5"),
    }


def test_calculate_shopping_quantities_for_multiple_days():
    meals = {
        "monday": {"rice": "100", "chicken": "150"},
        "tuesday": {"rice": "50", "salmon": "120"},
        "breakfast": {"oats": "75"},
        "snack": {"banana": "50"},
        "supplements": {"creatine": "5"},
        "strength": {"chicken": "50"},
        "run": {"salmon": "30"},
    }

    result = calculate_shopping_quantities(
        ["monday", "tuesday"],
        meals,
        {"monday": "strength", "tuesday": "run"},
    )

    assert result == {
        "rice": Decimal("150"),
        "chicken": Decimal("200"),
        "salmon": Decimal("150"),
        "oats": Decimal("150"),
        "banana": Decimal("100"),
        "creatine": Decimal("10"),
    }


def test_calculate_shopping_quantities_for_empty_days():
    result = calculate_shopping_quantities(
        [],
        {},
        {},
    )

    assert result == {}


def test_calculate_shopping_quantities_uses_decimal_arithmetic():
    meals = {
        "monday": {"oil": "0.1"},
        "breakfast": {"oil": "0.2"},
        "snack": {},
        "supplements": {},
        "strength": {},
    }

    result = calculate_shopping_quantities(
        ["monday"],
        meals,
        {"monday": "strength"},
    )

    assert result["oil"] == Decimal("0.3")