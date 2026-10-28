from decimal import Decimal

import pytest

from meal_plan_calc import nutrition


@pytest.fixture
def foods():
    return {
        "rice": {
            "category": "carb",
            "calories": "130",
            "fat": "0.3",
            "saturates": "0.1",
            "carbs": "28",
            "sugars": "0.1",
            "fibre": "0.4",
            "protein": "2.7",
            "salt": "0.01",
        },
        "chicken": {
            "category": "protein",
            "calories": "165",
            "fat": "3.6",
            "saturates": "1.0",
            "carbs": "0",
            "sugars": "0",
            "fibre": "0",
            "protein": "31",
            "salt": "0.2",
        },
    }


@pytest.fixture
def categories_split():
    return {
        "carb": Decimal("3") / Decimal("4"),
        "protein": Decimal("2") / Decimal("3"),
    }


def test_empty_nutrition_totals():
    result = nutrition.empty_nutrition_totals()

    assert tuple(result) == nutrition.NUTRIENTS
    assert all(value == Decimal("0") for value in result.values())


def test_calculate_meal_nutrition(foods):
    result = nutrition.calculate_meal_nutrition(
        {"rice": "200"},
        foods,
    )

    assert result["calories"] == Decimal("260")
    assert result["protein"] == Decimal("5.4")
    assert result["carbs"] == Decimal("56")
    assert result["salt"] == Decimal("0.02")


def test_calculate_meal_nutrition_applies_category_fraction(foods):
    result = nutrition.calculate_meal_nutrition(
        {"rice": "200", "chicken": "100"},
        foods,
        {"carb": Decimal("0.5"), "protein": Decimal("0.25")},
    )

    # Rice: 200 g × 130 kcal / 100 g × 0.5 = 130 kcal
    # Chicken: 100 g × 165 kcal / 100 g × 0.25 = 41.25 kcal
    assert result["calories"] == Decimal("171.25")


def test_calculate_meal_nutrition_defaults_to_full_quantity(foods):
    result = nutrition.calculate_meal_nutrition(
        {"rice": "100"},
        foods,
        {"protein": Decimal("0.5")},
    )

    # No fraction is specified for rice's "carb" category
    assert result["calories"] == Decimal("130")


def test_calculate_cooking_nutrition_lunch(foods, categories_split):
    meals = {"monday": {"rice": "200", "chicken": "100"}}

    result = nutrition.calculate_cooking_nutrition(
        "monday", foods, meals, categories_split, "lunch"
    )

    expected_calories = (
        Decimal("130") * Decimal("200") * Decimal("0.75") / Decimal("100")
        + Decimal("165") * Decimal("100") * categories_split["protein"]
        / Decimal("100")
    )
    assert result["calories"] == expected_calories


def test_calculate_cooking_nutrition_dinner(foods, categories_split):
    meals = {"monday": {"rice": "200", "chicken": "100"}}

    result = nutrition.calculate_cooking_nutrition(
        "monday", foods, meals, categories_split, "dinner"
    )

    expected_calories = (
        Decimal("130") * Decimal("200") * Decimal("0.25") / Decimal("100")
        + Decimal("165") * Decimal("100")
        * (Decimal("1") - categories_split["protein"]) / Decimal("100")
    )
    assert result["calories"] == expected_calories


def test_calculate_cooking_nutrition_rejects_invalid_meal_part(
    foods, categories_split
):
    with pytest.raises(ValueError, match="meal_part"):
        nutrition.calculate_cooking_nutrition(
            "monday",
            foods,
            {"monday": {"rice": "100"}},
            categories_split,
            "breakfast",
        )


def test_calculate_meal_type_nutrition(foods):
    meals = {"breakfast": {"rice": "100"}}

    result = nutrition.calculate_meal_type_nutrition(
        "breakfast", foods, meals
    )

    assert result["calories"] == Decimal("130")
    assert result["protein"] == Decimal("2.7")


def test_calculate_day_eating_nutrition(foods, categories_split):
    # Every meal is deliberately small so the total can be checked by hand
    meals = {
        "monday": {"rice": "100"},
        "tuesday": {"rice": "100"},
        "wednesday": {"rice": "100"},
        "thursday": {"rice": "100"},
        "friday": {"rice": "100"},
        "saturday": {"rice": "100"},
        "sunday": {"rice": "100"},
        "breakfast": {"rice": "100"},
        "snack": {},
        "supplements": {},
        "run": {},
        "strength": {},
        "mobility": {},
    }

    result = nutrition.calculate_day_eating_nutrition(
        "wednesday",
        foods,
        meals,
        [
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        ],
        {
            "monday": "strength",
            "tuesday": "run",
            "wednesday": "strength",
            "thursday": "run",
            "friday": "mobility",
            "saturday": "run",
            "sunday": "run",
        },
        categories_split,
    )

    # Breakfast: 100 g rice
    # Wednesday lunch: 75 g rice from Tuesday's cooking
    # Wednesday dinner: 25 g rice from Monday's cooking
    # Snack, supplements, and exercise meal are empty
    assert result["calories"] == Decimal("260")