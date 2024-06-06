import pandas_market_calendars as mcal
import random
import math

from torchrl.envs import GymWrapper, TransformedEnv, Compose, ObservationNorm, DoubleToFloat, StepCounter

import logging
logger = logging.getLogger(__name__)

class OperationUtils:
    @staticmethod
    def safe_division(a, b):
        if b == 0:
            return 0
        return a / b

    @staticmethod
    def sig(x):
        return 1 / (1 + math.exp(-x))

class ScoreUtils:
    @staticmethod
    def purchase_score(expected_price, avg_price):
        delta = expected_price - avg_price
        expected_avg_rate = avg_price / expected_price
        delta_score = (expected_price - delta) if delta >= 0 else delta
        sig_delta_score = OperationUtils.sig(delta_score)
        expected_avg_rate_score = expected_avg_rate if expected_avg_rate <= 1 else 0
        final_score = sig_delta_score + expected_avg_rate_score
        return final_score

class RentUtils:
    calendar = mcal.get_calendar('BMF')
    @staticmethod
    def calc_rent(buy_value, sell_value, du_idx, di_rent):
        buy_sell_rent = (sell_value / buy_value) - 1
        rent_anual = (1 + buy_sell_rent) ** du_idx - 1
        rent_over_cdi = rent_anual / di_rent
        return rent_over_cdi

    @staticmethod
    def calc_du_idx(start_date, end_date):
        time_frame = RentUtils.calendar.schedule(start_date, end_date)
        date_range = mcal.date_range(time_frame, frequency='1D')
        return 252 / (len(date_range) - 1)

    @staticmethod
    def get_random_sell(sell_group):
        random_sell_group_key = random.choice(list(sell_group.groups.keys()))
        random_sell_group = sell_group.get_group(random_sell_group_key).reset_index()
        random_sell_id = random.randint(0, len(random_sell_group) - 1)
        return random_sell_group.iloc[random_sell_id]

    @staticmethod
    def get_expected_price(operation_dt, expiration_dt, sell_price, di):
        du = RentUtils.calc_du_idx(operation_dt, expiration_dt)
        return round((sell_price / pow(di + 1, OperationUtils.safe_division(1, du))), 5)

class EnvUtils:
    @staticmethod
    def wrap_gym_env(env, device):
        logger.info("Wrapping env with GymWrapper")
        return GymWrapper(env, device=device)

    @staticmethod
    def to_transformed_env(env):
        logger.info("Wrapping env with transformations")
        transformed_env = TransformedEnv(env, Compose(
        ObservationNorm(in_keys=["observation"]),
        DoubleToFloat(),
        StepCounter()))
        transformed_env.transform[0].init_stats(num_iter=2000, reduce_dim=0, cat_dim=0)
        return transformed_env