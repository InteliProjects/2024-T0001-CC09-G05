import time
import argparse
import numpy as np
import wandb
from agent.ppo import PPO
from agent.ppo import PPOEvaluate
import logging
from envs.env import MatchEnv, DummyEnv, ExecutionEnv
from utils import EnvUtils
from processing.data_process import DataPreparation
import pandas as pd
from warnings import filterwarnings
import torch
filterwarnings("ignore")


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)

num_cells = 128
lr = 1e-5
max_grad_norm = 1.0
frames_per_batch = 2000

# For a complete training, bring the number of frames up to 1M
total_frames = 100_000

# PPO
sub_batch_size = 512  # cardinality of the sub-samples gathered from the current data in the inner loop
num_epochs = 10  # optimisation steps per batch of data collected
clip_epsilon = (
    0.2  # clip value for PPO loss: see the equation in the intro for more context.
)
gamma = 0.99
lmbda = 0.95
entropy_eps = 1e-5

hyperparams = {
    "num_cells": num_cells,
    "num_epochs": num_epochs,
    "sub_batch_size": sub_batch_size,
    "max_grad_norm": max_grad_norm,
    "frames_per_batch": frames_per_batch,
    "total_frames": total_frames,
    "gamma": gamma,
    "lmbda": lmbda,
    "clip_epsilon": clip_epsilon,
    "entropy_eps": entropy_eps,
    "lr": lr,
}


device = "cuda" if torch.cuda.is_available() else "cpu"

class ProcessMatch:
    def __init__(self, vendas_file, compras_file):
        self.vendas = pd.read_csv(vendas_file)
        self.compras = pd.read_csv(compras_file)
        self.matched_vendas = {}
        self.matched_rent = {}
        self.matches = {}
        self.model = None
        self.current_env = None
        self.total_to_match = len(self.vendas)
        self.match_count = 0
        self.start_time = None
        self.end_time = None
        self.ended = False
        self.stop_requested = False

    def load_model(self, model_path):
        logger.debug("Loading model")
        self.model = PPOEvaluate(hyperparams, device=device)
        dummy_env = DummyEnv()
        wrapped_dummy_env = EnvUtils.wrap_gym_env(dummy_env, device)
        self.model.set_prediction_env(wrapped_dummy_env)
        self.model.load(model_path)

    def run(self, workers=0):
        self.start_time = time.time()
        logger.debug("Running process")
        prep = DataPreparation()
        self.compras, self.vendas = prep.prepare_data(self.compras, self.vendas)
        self.compras["remaining_qty"] = self.compras["Quantidade"]

        compras_grouped, vendas_grouped = prep.group_data(self.compras, self.vendas)

        for group_name, venda_group in vendas_grouped:
            if self.stop_requested:
                break
            for row_idx, row in venda_group.iterrows():
                real_id = row["real_id"]
                curr_env = ExecutionEnv(row, self.compras.loc[self.compras["UniqueID"] == group_name])
                state = curr_env.reset()
                done = False

                while not done:
                    action = self.model.predict_action(state)[2]
                    state, done = curr_env.step(action)
                self.matches[real_id] = curr_env.used_purchases
                self.vendas.loc[row_idx, "avg_rent"] = curr_env.avg_rent

                for _row_idx, _row in curr_env.purchases.iterrows():
                    self.compras.loc[self.compras["real_id"] == _row["real_id"], "remaining_qty"] = _row["remaining_qty"]
                logger.info(f"Venda {group_name} finalizada")
                self.matched_vendas[f'{group_name}-{row["real_id"]}'] = row["real_id"]
                self.matched_rent[f'{group_name}-{row["real_id"]}'] = curr_env.avg_rent
                self.match_count += 1

        self.end_time = time.time()
        self.ended = True
        self.cleanup_after_stop()

    def request_stop(self):
        self.stop_requested = True

    def cleanup_after_stop(self):
        self.model = None
        self.currppo =ent_env = None
    def get_venda_matches(self, venda_id):
        purchases = self.matches[venda_id]
        purchases_dt = pd.DataFrame()
        for key, value in purchases.items():
            row = self.compras.loc[self.compras["real_id"] == key]
            row["used_qty"] = value
            purchases_dt = pd.concat([purchases_dt, row])

        return purchases_dt




import argparse

def main(total_frames, device):
    
    run = wandb.init(
        project="ReMATCH",
        config=hyperparams,
        job_type="train",
        tags=["train", "ppo"],
    )

    wandb.login() # Remove this block if you are not using wandb
    timestamp_number = int(time.time())
    hyperparams["total_frames"] = total_frames
    model_name = f'{total_frames // 1000 }k_frames_{timestamp_number}.pth'
    ppo = PPOEvaluate(hyperparams, device=device)

    logger.info("Loading datasets")
    vendas = pd.read_csv('./datasets/vendas_dataset.csv')
    compras = pd.read_csv('./datasets/compras_dataset.csv')

    prep = DataPreparation()
    compras, vendas = prep.prepare_data(compras, vendas)
    vendas = vendas[vendas["UniqueID"] != "Cliente 6_2023-11-16_MGLU3_BRAD"]

    compras_grouped, vendas_grouped = prep.group_data(compras, vendas)

    env = MatchEnv(vendas_grouped, compras_grouped)
    env = EnvUtils.wrap_gym_env(env, device)
    env = EnvUtils.to_transformed_env(env)

    ppo.set_training_env(env)
    ppo.train()
    ppo.save_model(f"models/{model_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--total_frames', type=int, required=True, help='Total frames for training')
    parser.add_argument('--device', type=str, required=True, help='Device for training')
    args = parser.parse_args()
    main(args.total_frames, args.device)