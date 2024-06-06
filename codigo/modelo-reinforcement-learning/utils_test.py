import math
from utils import OperationUtils, ScoreUtils, RentUtils

class TestOperationUtils:
    def test_safe_division_nonzero(self):
        assert OperationUtils.safe_division(10, 5) == 2

    def test_safe_division_by_zero(self):
        assert OperationUtils.safe_division(10, 0) == 0

class TestScoreUtils:
    def test_purchase_score_positive_delta(self):
        # Test when delta is positive
        expected_price = 100
        avg_price = 90
        assert ScoreUtils.purchase_score(expected_price, avg_price) == 1.9

    def test_purchase_score_negative_delta(self):
        # Test when delta is negative
        expected_price = 90
        avg_price = 100
        expected_score = 1 / (1 + math.exp(10)) + 0  # Calculated manually
        assert ScoreUtils.purchase_score(expected_price, avg_price) == expected_score

    def test_purchase_score_zero_delta(self):
        # Test when delta is zero
        expected_price = 100
        avg_price = 100
        expected_score = 1 / (1 + math.exp(0)) + 1  # Calculated manually
        assert ScoreUtils.purchase_score(expected_price, avg_price) == 2.0

    def test_purchase_score_avg_rate_below_1(self):
        # Test when expected_avg_rate is below 1
        expected_price = 100
        avg_price = 90
        expected_score = 1 / (1 + math.exp(-10)) + 0.9  # Calculated manually
        assert ScoreUtils.purchase_score(expected_price, avg_price) == 1.9

class TestRentUtils:
    def test_calc_rent_positive(self):
        # Test when buy value is lower than sell value
        buy_value = 100
        sell_value = 110
        du_idx = 20
        di_rent = 0.02
        expected_rent = 286.37499746628055
        assert RentUtils.calc_rent(buy_value, sell_value, du_idx, di_rent) == expected_rent

    def test_calc_rent_negative(self):
        # Test when buy value is higher than sell value
        buy_value = 110
        sell_value = 100
        du_idx = 20
        di_rent = 0.02
        expected_rent = -42.56781859879282
        assert RentUtils.calc_rent(buy_value, sell_value, du_idx, di_rent) == expected_rent

    def test_calc_rent_zero(self):
        # Test when buy value is equal to sell value
        buy_value = 100
        sell_value = 100
        du_idx = 20
        di_rent = 0.02
        expected_rent = 0
        assert RentUtils.calc_rent(buy_value, sell_value, du_idx, di_rent) == expected_rent


# Execute the tests
if __name__ == "__main__":
    import pytest
    pytest.main()
