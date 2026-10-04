"""
Тесты для учебного модуля расчета доставки (delivery.py).

Требования восстановлены по контексту кода:
  * вес 0.1-50 кг и дистанция 1-5000 км, иначе код ошибки (-1, "0000-00-00");
  * типы посылок: обычный, хрупкий, опасный;
  * базовый тариф 200 руб. + 5 руб. за километр;
  * весовой коэффициент: 1.2 для 5-20 кг, 1.5 от 20 кг;
  * надбавки: 300 руб. за хрупкую, 1000 руб. за опасную посылку;
  * экспресс-доставка ускоряет и удорожает доставку;
  * срок доставки не может быть нулевым, стоимость округляется до целых рублей.

Запуск: python -m unittest discover -v
"""

import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from delivery import calculate_delivery_cost

ERROR_RESULT = (-1, "0000-00-00")
SHIPMENT_DATE = datetime.date(2026, 9, 3)


class TestParameterValidation(unittest.TestCase):
    """Проверки границ физических параметров и типа посылки."""

    def test_weight_below_minimum_returns_error_code(self):
        self.assertEqual(
            ERROR_RESULT, calculate_delivery_cost(0.05, 100, "обычный")
        )

    def test_weight_above_maximum_returns_error_code(self):
        self.assertEqual(
            ERROR_RESULT, calculate_delivery_cost(50.5, 100, "обычный")
        )

    def test_distance_below_minimum_returns_error_code(self):
        self.assertEqual(ERROR_RESULT, calculate_delivery_cost(1.0, 0, "обычный"))

    def test_distance_above_maximum_returns_error_code(self):
        self.assertEqual(
            ERROR_RESULT, calculate_delivery_cost(1.0, 5001, "обычный")
        )

    def test_minimum_weight_and_minimum_distance_are_accepted(self):
        self.assertEqual(
            (205, "2026-09-04"), calculate_delivery_cost(0.1, 1, "обычный")
        )

    def test_maximum_weight_and_maximum_distance_are_accepted(self):
        self.assertEqual(
            (38800, "2026-09-13"), calculate_delivery_cost(50, 5000, "опасный")
        )

    def test_unknown_package_type_returns_error_code(self):
        for package_type in ("срочный", "", "обычная", "ХРУПКИЙ"):
            with self.subTest(package_type=package_type):
                self.assertEqual(
                    ERROR_RESULT, calculate_delivery_cost(1.0, 100, package_type)
                )

    def test_wrong_parameter_type_returns_error_code_instead_of_exception(self):
        cases = (("10", 100, "обычный"), (1.0, "100", "обычный"))
        for weight, distance, package_type in cases:
            with self.subTest(weight=weight, distance=distance):
                try:
                    result = calculate_delivery_cost(weight, distance, package_type)
                except TypeError as exc:
                    self.fail(
                        f"Ожидался код ошибки {ERROR_RESULT}, но получено "
                        f"исключение TypeError: {exc}"
                    )
                self.assertEqual(ERROR_RESULT, result)


class TestCostCalculation(unittest.TestCase):
    """Проверки тарифных сеток, коэффициентов и надбавок."""

    def test_light_package_cost_equals_base_plus_distance_rate(self):
        self.assertEqual(
            (205, "2026-09-04"), calculate_delivery_cost(0.1, 1, "обычный")
        )

    def test_distance_rate_adds_five_rubles_per_kilometer(self):
        self.assertEqual(
            (700, "2026-09-04"), calculate_delivery_cost(1.0, 100, "обычный")
        )

    def test_package_exactly_five_kg_has_no_weight_coefficient(self):
        self.assertEqual(
            (700, "2026-09-04"), calculate_delivery_cost(5.0, 100, "обычный")
        )

    def test_package_between_five_and_twenty_kg_gets_coefficient_1_2(self):
        self.assertEqual(
            (840, "2026-09-04"), calculate_delivery_cost(10, 100, "обычный")
        )

    def test_package_from_twenty_kg_gets_coefficient_1_5(self):
        self.assertEqual(
            (1050, "2026-09-04"), calculate_delivery_cost(20, 100, "обычный")
        )

    def test_fragile_package_adds_three_hundred_rubles(self):
        self.assertEqual(
            (550, "2026-09-04"), calculate_delivery_cost(1.0, 10, "хрупкий")
        )

    def test_hazardous_package_adds_one_thousand_rubles(self):
        self.assertEqual(
            (1250, "2026-09-04"), calculate_delivery_cost(1.0, 10, "опасный")
        )

    def test_hazardous_package_costs_more_than_fragile_one(self):
        fragile_cost, _ = calculate_delivery_cost(1.0, 10, "хрупкий")
        hazardous_cost, _ = calculate_delivery_cost(1.0, 10, "опасный")
        self.assertGreater(hazardous_cost, fragile_cost)

    def test_type_surcharge_is_added_after_weight_coefficient(self):
        self.assertEqual(
            (1140, "2026-09-04"), calculate_delivery_cost(10, 100, "хрупкий")
        )

    def test_express_delivery_costs_more_than_ordinary_one(self):
        ordinary_cost, _ = calculate_delivery_cost(1.0, 100, "обычный")
        express_cost, _ = calculate_delivery_cost(1.0, 100, "обычный", True)
        self.assertEqual(700, ordinary_cost)
        self.assertGreater(express_cost, ordinary_cost)
        self.assertEqual(1050, express_cost)

    def test_cost_with_fractional_part_is_rounded_to_whole_rubles(self):
        self.assertEqual(
            (308, "2026-09-04"), calculate_delivery_cost(20, 1, "обычный")
        )

    def test_half_ruble_is_rounded_up_not_down(self):
        self.assertEqual(
            (323, "2026-09-04"), calculate_delivery_cost(25, 3, "обычный")
        )


class TestDeliveryDate(unittest.TestCase):
    """Проверки расчета даты и срока доставки."""

    def test_delivery_date_is_counted_from_fixed_shipment_date(self):
        _, date = calculate_delivery_cost(1.0, 5000, "обычный")
        self.assertEqual("2026-09-13", date)
        self.assertGreater(
            datetime.datetime.strptime(date, "%Y-%m-%d").date(), SHIPMENT_DATE
        )

    def test_delivery_under_five_hundred_km_takes_one_day(self):
        self.assertEqual(
            "2026-09-04", calculate_delivery_cost(1.0, 499, "обычный")[1]
        )

    def test_one_day_per_five_hundred_km_is_added(self):
        self.assertEqual(
            "2026-09-05", calculate_delivery_cost(1.0, 1000, "обычный")[1]
        )

    def test_shipment_date_is_never_used_as_delivery_date(self):
        for distance in (100, 200, 499):
            with self.subTest(distance=distance):
                self.assertNotEqual(
                    "2026-09-03",
                    calculate_delivery_cost(1.0, distance, "обычный", True)[1],
                )

    def test_express_delivery_halves_the_number_of_days(self):
        self.assertEqual(
            "2026-09-08", calculate_delivery_cost(1.0, 5000, "обычный", True)[1]
        )

    def test_transport_time_grows_with_distance(self):
        dates = [
            calculate_delivery_cost(1.0, distance, "обычный")[1]
            for distance in (500, 1000, 5000)
        ]
        self.assertEqual(sorted(dates), dates)


if __name__ == "__main__":
    unittest.main(verbosity=2)
