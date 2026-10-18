# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from converter import Converter


class TestConverter(unittest.TestCase):
    def test_big_positive_number_returns_1000(self):
        self.assertEqual(1000, Converter.do(100.7))
        self.assertEqual(1000, Converter.do(250.0))
        self.assertEqual(1000, Converter.do(999.9))

    def test_positive_number_below_boundary_returns_integer_part(self):
        self.assertEqual(100, Converter.do(100.6))
        self.assertEqual(65, Converter.do(65.7))
        self.assertEqual(0, Converter.do(0.1))

    def test_zero_raises_value_error(self):
        with self.assertRaises(ValueError):
            Converter.do(0.0)

    def test_negative_number_in_range_returns_integer_part_minus_five(self):
        self.assertEqual(-35, Converter.do(-30.4))
        self.assertEqual(-34, Converter.do(-29.9))
        self.assertEqual(-5, Converter.do(-0.1))

    def test_number_below_negative_boundary_returns_minus_2000(self):
        self.assertEqual(-2000, Converter.do(-30.5))
        self.assertEqual(-2000, Converter.do(-94.5))
        self.assertEqual(-2000, Converter.do(-500.0))

    def test_return_type_is_int(self):
        self.assertIsInstance(Converter.do(10.5), int)
        self.assertIsInstance(Converter.do(-10.5), int)
        self.assertIsInstance(Converter.do(100.7), int)


if __name__ == "__main__":
    unittest.main()
