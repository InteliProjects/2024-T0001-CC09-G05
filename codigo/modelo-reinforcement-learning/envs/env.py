from typing import Optional

import gymnasium as gym
import numpy as np

from utils import OperationUtils, ScoreUtils, RentUtils

import logging

logger = logging.getLogger(__name__)

# Define the environment class for matching sells and purchases
class MatchEnv(gym.Env):
    def __init__(self, table_vendas_grouped, table_compras_grouped):
        self.sells_grouped = table_vendas_grouped
        self.purchases_grouped = table_compras_grouped

        self.action_space = gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32)
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32)

        # state
        self.sell_remaining_space_rate = 0
        self.sell_expected_price = 0
        self.purchases_avg_price = 0
        self.current_purchase_price = 0
        self.current_purchase_qty = 0
        self.current_purchase_score = 0
        self.current_purchase_price_diff = 0

        self.iter = 0
        self.sell_remaining_space = 0
        self.current_sell = None
        self.current_purchase_group = None
        self.used_purchases = []
        self.purchases_total_price = 0
        self.sell_max_qty = 0
        self.old_price_diff = 0

        self.done = False
        self.avg_rent = 0

        self.cum_reward = 0

        self.reset()

    # Method to select a purchase
    def pick_current_purchase(self, purchase_id, quantity):
        purchase = self.current_purchase_group.loc[purchase_id]
        purchase_id = purchase.name
        available_qty = purchase["remaining_qty"]
        quantity = min(quantity, available_qty)
        purchase_remaining_qty = purchase["remaining_qty"] - quantity
        self.current_purchase_group.loc[purchase_id, "remaining_qty"] = purchase_remaining_qty
        self.sell_remaining_space -= quantity
        self.used_purchases.append({"id": purchase_id, "qty": quantity})
        return quantity

    # Method to get the current state of the environment
    def get_state(self) -> np.array:
        return np.array([
            self.sell_remaining_space_rate,
            self.sell_expected_price,
            self.purchases_avg_price,
            self.current_purchase_price_diff,
            self.current_purchase_qty,
            self.avg_rent,
        ], dtype=np.float32)

    # Method to update the state based on the selected purchase
    def update_state(self, quantity):
        self.purchases_total_price += self.current_purchase_price * quantity
        self.purchases_avg_price = OperationUtils.safe_division(self.purchases_total_price,
                                                                (self.sell_max_qty - self.sell_remaining_space))
        self.sell_remaining_space_rate = OperationUtils.safe_division(self.sell_remaining_space, self.sell_max_qty)
        du = RentUtils.calc_du_idx(self.current_sell["Dt. Operação"], self.current_sell["Vencimento"])
        self.avg_rent = RentUtils.calc_rent(self.purchases_avg_price, self.current_sell["Preço"], du,
                                            self.current_sell["DI"]) if self.purchases_avg_price > 0 else 0
        return self.get_state()

    # Method to calculate the reward based on the state
    def get_reward(self):
        price_difference = abs(self.sell_expected_price - self.purchases_avg_price)
        rent_difference = abs((self.avg_rent * 100) - 100) * 0.1
        price_scale = 25
        rent_scale = 1.5

        reward = 0
        reward += (-price_scale * pow(price_difference, 2)) + (-rent_scale * pow(rent_difference, 2))
        return reward

    # Method to take a step in the environment based on the action
    def step(self, action):
        current_purchase_idx = self.iter % len(self.current_purchase_group) if self.iter > 0 else 0
        quantity_percentage = action[0]
        quantity = int(self.current_purchase_qty * quantity_percentage)
        quantity = min(quantity, self.sell_remaining_space)

        quantity = self.pick_current_purchase(current_purchase_idx, quantity)

        state = self.update_state(quantity)
        reward = self.get_reward()

        if self.sell_remaining_space == 0:
            self.cum_reward += reward
            logger.debug(
                f"Reward: {self.cum_reward} - Avg Rent: {self.avg_rent} - Sell ID {self.current_sell['UniqueID']} - ")
            self.done = True

        if abs(self.current_purchase_price - self.sell_expected_price) < self.old_price_diff:
            reward += 0.1
        elif abs(self.current_purchase_price - self.sell_expected_price) == 0:
            reward += 1
        elif abs(self.current_purchase_price - self.sell_expected_price) > self.old_price_diff:
            reward -= 0.1

        self.iter += 1
        next_purchase = self.iter % len(self.current_purchase_group) if self.iter > 0 else 0
        current_purchase = self.current_purchase_group.iloc[next_purchase]
        self.current_purchase_price = current_purchase["Preço"]
        self.current_purchase_qty = current_purchase["remaining_qty"]
        self.current_purchase_score = current_purchase["score"]

        self.old_price_diff = self.current_purchase_price - self.sell_expected_price

        self.current_purchase_price_diff = self.current_purchase_price - self.sell_expected_price
        return state, reward, self.done, False, {"info": "info"}

    # Method to reset the environment to its initial state
    def reset(self, seed: Optional[int] = None):
        self.iter = 0
        self.cum_reward = 0
        self.current_sell = RentUtils.get_random_sell(self.sells_grouped)
        self.used_purchases = []
        self.purchases_total_price = 0
        self.sell_max_qty = self.current_sell["Quantidade"]
        self.sell_expected_price = RentUtils.get_expected_price(self.current_sell["Dt. Operação"],
                                                                self.current_sell["Vencimento"],
                                                                self.current_sell["Preço"],
                                                                self.current_sell["DI"])
        self.current_purchase_group = self.purchases_grouped.get_group(self.current_sell["UniqueID"]).reset_index(
            drop=True)
        self.current_purchase_group["score"] = self.current_purchase_group.apply(
            lambda x: ScoreUtils.purchase_score(self.sell_expected_price, x["Preço"]), axis=1)

        self.current_purchase_group["remaining_qty"] = self.current_purchase_group["Quantidade"]

        # self.current_purchase_group = self.current_purchase_group.sample(frac=1).reset_index(drop=True)
        self.current_purchase_group.sort_values(by="score", ascending=False, ignore_index=True)
        current_purchase = self.current_purchase_group.iloc[self.iter]

        self.sell_remaining_space = self.sell_max_qty
        self.purchases_avg_price = 0
        self.current_purchase_price = current_purchase["Preço"]
        self.current_purchase_qty = current_purchase["Quantidade"]
        self.current_purchase_score = current_purchase["score"]
        self.current_purchase_price_diff = self.current_purchase_price - self.sell_expected_price
        self.sell_remaining_space_rate = self.sell_remaining_space / self.sell_max_qty
        self.old_price_diff = np.inf

        self.done = False

        return self.get_state(), {}

# Define the execution environment class
class ExecutionEnv():
    def __init__(self, sell, purchases):
        self.sell = sell
        self.purchases = purchases

        # state
        self.sell_remaining_space_rate = 0
        self.sell_expected_price = 0
        self.purchases_avg_price = 0
        self.current_purchase_price = 0
        self.current_purchase_qty = 0
        self.current_purchase_score = 0
        self.current_purchase_price_diff = 0

        self.iter = 0
        self.sell_remaining_space = 0
        self.used_purchases = {}
        self.purchases_total_price = 0
        self.sell_max_qty = 0
        self.old_price_diff = 0

        self.done = False
        self.avg_rent = 0

    # Initialization of execution environment
    def pick_current_purchase(self, purchase_id, quantity):
        purchase = self.purchases.iloc[purchase_id]
        available_qty = purchase["remaining_qty"]
        quantity = min(quantity, available_qty)
        purchase_remaining_qty = purchase["remaining_qty"] - quantity
        self.purchases.loc[purchase.name, "remaining_qty"] = purchase_remaining_qty
        self.sell_remaining_space -= quantity
        real_purchase_id = purchase["real_id"]
        self.used_purchases[real_purchase_id] = self.used_purchases.get(real_purchase_id, 0) + quantity
        return quantity

    # Method to get the current state of the execution environment
    def get_state(self) -> np.array:
        return np.array([
            self.sell_remaining_space_rate,
            self.sell_expected_price,
            self.purchases_avg_price,
            self.current_purchase_price_diff,
            self.current_purchase_qty,
            self.current_purchase_score
        ], dtype=np.float32)

    # Method to update the state of the execution environment
    def update_state(self, quantity):
        self.purchases_total_price += self.current_purchase_price * quantity
        self.purchases_avg_price = OperationUtils.safe_division(self.purchases_total_price,
                                                                (self.sell_max_qty - self.sell_remaining_space))
        self.sell_remaining_space_rate = OperationUtils.safe_division(self.sell_remaining_space, self.sell_max_qty)
        du = RentUtils.calc_du_idx(self.sell["Dt. Operação"], self.sell["Vencimento"])
        self.avg_rent = RentUtils.calc_rent(self.purchases_avg_price, self.sell["Preço"], du,
                                            self.sell["DI"]) if self.purchases_avg_price > 0 else 0
        return self.get_state()

    # Method to take a step in the execution environment
    def step(self, action):
        self.done = False
        current_purchase_idx = self.iter % len(self.purchases) if self.iter > 0 else 0
        quantity_percentage = action[0]
        quantity = int(self.current_purchase_qty * quantity_percentage)
        quantity = min(quantity, self.sell_remaining_space)

        quantity = self.pick_current_purchase(current_purchase_idx, quantity)

        state = self.update_state(quantity)

        if self.sell_remaining_space == 0:
            self.done = True

        self.iter += 1

        next_purchase = self.iter % len(self.purchases) if self.iter > 0 else 0
        current_purchase = self.purchases.iloc[next_purchase]
        self.current_purchase_price = current_purchase["Preço"]
        self.current_purchase_qty = current_purchase["remaining_qty"]
        self.current_purchase_score = current_purchase["score"]
        self.old_price_diff = self.current_purchase_price - self.sell_expected_price
        self.current_purchase_price_diff = self.current_purchase_price - self.sell_expected_price
        return state, self.done

    # Method to reset the execution environment to its initial state
    def reset(self):
        self.iter = 0
        self.used_purchases = {}

        self.purchases_total_price = 0
        self.sell_max_qty = self.sell["Quantidade"]
        self.sell_expected_price = RentUtils.get_expected_price(self.sell["Dt. Operação"],
                                                                self.sell["Vencimento"],
                                                                self.sell["Preço"],
                                                                self.sell["DI"])

        self.purchases["score"] = self.purchases.apply(
            lambda x: ScoreUtils.purchase_score(self.sell_expected_price, x["Preço"]), axis=1)
        self.purchases["remaining_qty"] = self.purchases["Quantidade"]
        self.purchases.sort_values(by="score", ascending=False, ignore_index=True)

        current_purchase = self.purchases.iloc[self.iter]
        self.sell_remaining_space = self.sell_max_qty
        self.purchases_avg_price = 0
        self.current_purchase_price = current_purchase["Preço"]
        self.current_purchase_qty = current_purchase["Quantidade"]
        self.current_purchase_score = current_purchase["score"]
        self.current_purchase_price_diff = self.current_purchase_price - self.sell_expected_price
        self.sell_remaining_space_rate = self.sell_remaining_space / self.sell_max_qty
        self.old_price_diff = np.inf
        self.done = False

        return self.get_state()


class DummyEnv(gym.Env):
    """
    A dummy environment used for basic testing or template purposes.

    Implements minimal functionalities to align with gym.Env requirements.
    """
    def __init__(self):
        self.action_space = gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32)
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32)

    def step(self, action):
        """
        Processes a given action, essentially doing nothing in this dummy environment.

        Args:
            action (array): An action, irrelevant in this context as no real processing happens.

        Returns:
            tuple: Constant state, zero reward, episode done status, and empty info.
        """
        return np.array([0, 0, 0, 0, 0, 0], dtype=np.float32), 0, False, False, {}

    def reset(self):
        """
        Resets the dummy environment to its baseline state.

        Returns:
            np.array: A constant array representing the state.
        """
        return np.array([0, 0, 0, 0, 0, 0], dtype=np.float32), {}
