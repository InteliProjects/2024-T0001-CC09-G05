import numpy as np
import pytest
from envs.env import MatchEnv
import pandas as pd
from processing.data_process import DataPreparation

class TestMatchEnv:
    @pytest.fixture
    def match_env(self):
        vendas = pd.read_csv('./vendas_dataset.csv')
        compras = pd.read_csv('./compras_dataset.csv')
        compras,vendas = DataPreparation.prepare_data(compras,vendas)
        table_compras_grouped, table_vendas_grouped = DataPreparation.group_data(compras,vendas)

        env = MatchEnv(table_vendas_grouped, table_compras_grouped)
        yield env

    def test_pick_current_purchase(self, match_env):
        purchase_id = 1
        quantity = 10

        initial_sell_remaining_space = match_env.sell_remaining_space
        initial_purchase_remaining_qty = match_env.current_purchase_group.loc[purchase_id]["remaining_qty"]

        match_env.pick_current_purchase(purchase_id, quantity)

        assert match_env.sell_remaining_space == initial_sell_remaining_space - quantity
        assert match_env.current_purchase_group.loc[purchase_id]["remaining_qty"] == initial_purchase_remaining_qty - quantity
    
    def test_get_state(self, match_env):
        state = match_env.get_state()

        assert isinstance(state, np.ndarray)
        assert state.shape == (6,) 

        state_3 = state[3] - match_env.current_purchase_price_diff
        state_5 = state[5] - match_env.current_purchase_score

        assert state[0] == match_env.sell_remaining_space_rate
        assert state[1] == np.float32(match_env.sell_expected_price)
        assert state[2] == match_env.purchases_avg_price
        assert state_3 < 1e-4
        assert state[4] == match_env.current_purchase_qty
        assert state_5 < 1e-4

    def test_update_state(self, match_env):
        initial_purchases_total_price = match_env.purchases_total_price
        initial_purchases_avg_price = match_env.purchases_avg_price
        initial_sell_remaining_space_rate = match_env.sell_remaining_space_rate
        initial_avg_rent = match_env.avg_rent

        quantity = 10
        match_env.update_state(quantity)

        assert match_env.purchases_total_price == initial_purchases_total_price + match_env.current_purchase_price * quantity

        assert match_env.purchases_avg_price == initial_purchases_avg_price 
        assert match_env.sell_remaining_space_rate == initial_sell_remaining_space_rate 
        assert match_env.avg_rent == initial_avg_rent

    def test_step(self, match_env):
        initial_iter = match_env.iter
        initial_sell_remaining_space = match_env.sell_remaining_space
        initial_current_purchase_price = match_env.current_purchase_price
        initial_current_purchase_score = match_env.current_purchase_score
        initial_old_price_diff = match_env.old_price_diff

        action = np.array([0.5])
        state, reward, done, _, _ = match_env.step(action)

        assert match_env.iter == initial_iter + 1
        assert match_env.sell_remaining_space != initial_sell_remaining_space
        assert match_env.current_purchase_price != initial_current_purchase_price
        assert match_env.current_purchase_score != initial_current_purchase_score
        assert match_env.old_price_diff != initial_old_price_diff
        assert match_env.done == False
    
    def test_get_reward(self, match_env):
        match_env.sell_expected_price = 100
        match_env.purchases_avg_price = 105
        match_env.avg_rent = 0.02

        reward = match_env.get_reward()

        expected_price_difference = abs(match_env.sell_expected_price - match_env.purchases_avg_price)
        expected_rent_difference = abs((match_env.avg_rent * 100) - 100) * 0.1
        expected_reward = (-20 * pow(expected_price_difference, 2)) + (-1.5 * pow(expected_rent_difference, 2))

        assert reward == expected_reward

    def test_reset(self, match_env):
        initial_current_sell = match_env.current_sell
        initial_sell_expected_price = match_env.sell_expected_price
        initial_current_purchase_price = match_env.current_purchase_price
        initial_current_purchase_qty = match_env.current_purchase_qty
        initial_current_purchase_score = match_env.current_purchase_score
        initial_current_purchase_price_diff = match_env.current_purchase_price_diff

        state, info = match_env.reset()

        assert match_env.iter == 0
        assert not match_env.current_sell.equals(initial_current_sell)
        assert match_env.used_purchases == []
        assert match_env.purchases_total_price == 0
        assert match_env.sell_max_qty == match_env.current_sell["Quantidade"]
        assert match_env.sell_expected_price != initial_sell_expected_price
        assert match_env.sell_remaining_space == match_env.sell_max_qty
        assert match_env.purchases_avg_price == 0
        assert match_env.current_purchase_price != initial_current_purchase_price
        assert match_env.current_purchase_qty != initial_current_purchase_qty
        assert match_env.current_purchase_score != initial_current_purchase_score
        assert match_env.current_purchase_price_diff != initial_current_purchase_price_diff
        assert match_env.sell_remaining_space_rate == match_env.sell_remaining_space / match_env.sell_max_qty
        assert match_env.old_price_diff == np.inf
        assert not match_env.done