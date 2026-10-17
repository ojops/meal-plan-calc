from decimal import Decimal
import json
from pathlib import Path

# saturates are always included in fat total
# sugars are always included in carbs total
# fibre is not included in carbs total

# meals.json just using meal plan values, maybe not clear what "state", cooked/raw

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

exercise_split = {
    "monday": "strength", 
    "tuesday": "run",
    "wednesday": "strength",
    "thursday": "run",
    "friday": "mobility",
    "saturday": "run",
    "sunday": "run"
}

nutrients_count = {
    "calories":0,
    "fat":0,
    "saturates":0,
    "carbs":0,
    "sugars":0,
    "fibre":0,
    "protein":0,
    "salt":0
}

categories_split = {
    "protein":2/3,
    "carb":3/4,
    "veg":2/3,
    "extra":2/3,
    "fruit":2/3,
    "dairy":2/3,
    "nut":2/3
}


with open(DATA_DIR / "foods.json", "r") as foods_file, open(DATA_DIR / "meals.json", "r") as meals_file:
    foods = json.load(foods_file)
    meals = json.load(meals_file)

    def print_nice(nutrition_library):
        for nutrient in nutrients_count:
            print(nutrient + ":", nutrition_library[nutrient].quantize(Decimal("0.01")))

    def get_day_cooking_nutrition(day):
        nutrients_temp = nutrients_count.copy()
        for ingredient in meals[day]:
            for nutrient in nutrients_temp:
                nutrients_temp[nutrient] += Decimal(foods[ingredient][nutrient])*Decimal(meals[day][ingredient])/100
        return nutrients_temp

    def get_day_cooking_lunch_nutrition(day):
            nutrients_temp = nutrients_count.copy()
            for ingredient in meals[day]:
                for nutrient in nutrients_temp:
                    nutrients_temp[nutrient] += Decimal(foods[ingredient][nutrient])*Decimal(meals[day][ingredient])*Decimal(categories_split[foods[ingredient]["category"]])/100
            return nutrients_temp

    def get_day_cooking_dinner_nutrition(day):
            nutrients_temp = nutrients_count.copy()
            for ingredient in meals[day]:
                for nutrient in nutrients_temp:
                    nutrients_temp[nutrient] += Decimal(foods[ingredient][nutrient])*Decimal(meals[day][ingredient])*Decimal(1-categories_split[foods[ingredient]["category"]])/100
            return nutrients_temp

    def get_day_eating_nutrition(day):
        nutrients_temp = nutrients_count.copy()
        meal_types = ["snack", "supplements", exercise_split[day], "breakfast"]
        for meal_type in meal_types:
            for ingredient in meals[meal_type]:
                for nutrient in nutrients_temp:
                    nutrients_temp[nutrient] += Decimal(foods[ingredient][nutrient])*Decimal(meals[meal_type][ingredient])/100
        for nutrient in nutrients_temp:
            nutrients_temp[nutrient] += get_day_cooking_lunch_nutrition([*exercise_split][[*exercise_split].index(day)-1])[nutrient]
            nutrients_temp[nutrient] += get_day_cooking_dinner_nutrition([*exercise_split][[*exercise_split].index(day)-2])[nutrient]
        return nutrients_temp

    def get_meal_type_eating_nutrition(meal_type):
        nutrients_temp = nutrients_count.copy()
        for ingredient in meals[meal_type]:
            for nutrient in nutrients_temp:
                nutrients_temp[nutrient] += Decimal(foods[ingredient][nutrient])*Decimal(meals[meal_type][ingredient])/100
        return nutrients_temp

    for day in [*exercise_split]:
        print(day.upper())
        print_nice(get_day_eating_nutrition(day))
        print("---")

    #print_nice(get_meal_type_eating_nutrition("snack"))
