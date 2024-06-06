from collections import defaultdict
import torch
import wandb
from tensordict.nn import NormalParamExtractor, TensorDictModule
from torch import nn
from torchrl.collectors import SyncDataCollector
from torchrl.data import ReplayBuffer, SamplerWithoutReplacement, LazyTensorStorage
from torchrl.envs.utils import check_env_specs, ExplorationType, set_exploration_type
from torchrl.modules import ProbabilisticActor, TanhNormal, ValueOperator
from torchrl.objectives import ClipPPOLoss
from torchrl.objectives.value import GAE
from tqdm import tqdm

import matplotlib.pyplot as plt

import logging
logger = logging.getLogger(__name__)

class PPO:
    # Initialize PPO algorithm with hyperparameters and device
    def __init__(self, hyperparams, device):
        self.hyperparams = hyperparams
        self.env = None
        self.device = device
        self.policy_module = None
        self.value_module = None
        self.transform = None

    # Set the training environment for PPO
    def set_training_env(self, env):
        logging.info("Setting training environment")
        check_env_specs(env)
        self.env = env
        self.transform = env.transform[0]

        self.policy_module = self.build_policy_module(self.env)
        self.value_module = self.build_value_module()

        # initialize the lazy modules
        logger.info("Initializing Lazy Modules")
        self.policy_module(self.env.reset())
        self.value_module(self.env.reset())

        self.collector = self.build_collectors(self.env, self.policy_module)
        self.replay_buffer = self.build_replay_buffer()
        self.advantage_module = self.build_advantage_module(self.value_module)
        self.loss_module = self.build_loss_module(self.policy_module, self.value_module)
        self.optim, self.scheduler = self.build_optimizer(self.loss_module)

        wandb.watch(self.policy_module, log_freq=100)
        wandb.watch(self.value_module, log_freq=100)
        wandb.watch(self.loss_module, log_freq=100)
        wandb.watch(self.advantage_module, log_freq=100)

    # Build the policy module for the actor network
    def build_policy_module(self, env):
        logging.info("Building policy module")
        actor_net = nn.Sequential(
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(2 * env.action_spec.shape[-1], device=self.device),
            NormalParamExtractor(),
        )
        dict_module = TensorDictModule(
            actor_net, in_keys=["observation"], out_keys=["loc", "scale"]
        )

        return ProbabilisticActor(
            module=dict_module,
            spec=env.action_spec,
            in_keys=["loc", "scale"],
            distribution_class=TanhNormal,
            distribution_kwargs={
                "min": env.action_spec.space.low,
                "max": env.action_spec.space.high,
            },
            return_log_prob=True,
        )

    # Set the prediction environment
    def set_prediction_env(self, dummy_env):
        self.policy_module = self.build_policy_module(dummy_env)
        self.value_module = self.build_value_module()

    # Build the value module for the critic network
    def build_value_module(self):
        logging.info("Building value module")
        value_net = nn.Sequential(
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(1, device=self.device),
        )
        return ValueOperator(
            module=value_net,
            in_keys=["observation"],
        )

    # Build data collectors for PPO
    def build_collectors(self, env, policy_module):
        logging.info("Building collectors")
        collector = SyncDataCollector(
            env,
            policy_module,
            frames_per_batch=self.hyperparams["frames_per_batch"],
            total_frames=self.hyperparams["total_frames"],
            split_trajs=False,
            device=self.device,
        )

        return collector

    # Build the replay buffer
    def build_replay_buffer(self):
        logging.info("Building replay buffer")
        return ReplayBuffer(
            storage=LazyTensorStorage(max_size=self.hyperparams["frames_per_batch"]),
            sampler=SamplerWithoutReplacement(),
        )

    # Build the advantage module for GAE
    def build_advantage_module(self, value_module):
        logging.info("Building advantage module")
        return GAE(
            gamma=self.hyperparams["gamma"],
            lmbda=self.hyperparams["lmbda"],
            value_network=value_module,
            average_gae=True,
        )

    # Build the loss module for PPO
    def build_loss_module(self, policy_module, value_module):
        logging.info("Building loss module")
        return ClipPPOLoss(
            actor_network=policy_module,
            critic_network=value_module,
            clip_epsilon=self.hyperparams["clip_epsilon"],
            entropy_bonus=bool(self.hyperparams["entropy_eps"]),
            entropy_coef=self.hyperparams["entropy_eps"],
            critic_coef=1.0,
            loss_critic_type="smooth_l1",
        )

    # Build the optimizer and scheduler for training
    def build_optimizer(self, loss_module):
        logging.info("Building optimizer")
        optim = torch.optim.Adam(loss_module.parameters(), self.hyperparams["lr"])
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optim, self.hyperparams["total_frames"] // self.hyperparams["frames_per_batch"], 0.0
        )
        return optim, scheduler

    # Methods for saving and loading models
    def save(self, path, policy_module, value_module):
        logging.info(f"Saving model to {path}")
        torch.save(
            {
                "policy_module": policy_module.state_dict(),
                "value_module": value_module.state_dict(),
                "transform": self.transform,
            },
            path,
        )

    def save_model(self, path):
        self.save(path, self.policy_module, self.value_module)
    def _load(self, path, policy_module, value_module):
        logging.info(f"Loading model from {path}")
        checkpoint = torch.load(path, map_location=self.device)
        policy_module.load_state_dict(checkpoint["policy_module"])
        value_module.load_state_dict(checkpoint["value_module"])
        self.transform = checkpoint["transform"]

    def load(self, path):
        self._load(path, self.policy_module, self.value_module)

    # Method for predicting actions using the trained policy
    def predict_action(self, observation):
        observation_tensor = torch.from_numpy(observation).float().to(self.device)
        normalized_observation = self.transform(observation_tensor)
        with torch.no_grad():
            return self.policy_module(normalized_observation)

    # Main training loop for PPO
    def train(self):
        plt.ion()
        plt.clf()
        self.env.rollout(3)
        logging.info("Starting training - PPO")
        logs = defaultdict(list)
        pbar = tqdm(total=self.hyperparams["total_frames"])
        eval_str = ""
        logger.info("Starting training loop")

        for i, tensordict_data in enumerate(self.collector):
            for _ in range(self.hyperparams["num_epochs"]):
                self.advantage_module(tensordict_data)
                data_view = tensordict_data.reshape(-1)
                self.replay_buffer.extend(data_view.cpu())
                for _ in range(self.hyperparams["frames_per_batch"] // self.hyperparams["sub_batch_size"]):
                    subdata = self.replay_buffer.sample(self.hyperparams["sub_batch_size"])
                    loss_vals = self.loss_module(subdata.to(self.device))
                    loss_value = (
                            loss_vals["loss_objective"]
                            + loss_vals["loss_critic"]
                            + loss_vals["loss_entropy"]
                    )
                    loss_value.backward()
                    torch.nn.utils.clip_grad_norm_(self.loss_module.parameters(), self.hyperparams["max_grad_norm"])
                    self.optim.step()
                    self.optim.zero_grad()

            logs["reward"].append(tensordict_data["next", "reward"].mean().item())
            pbar.update(tensordict_data.numel())
            cum_reward_str = (
                f"average reward={logs['reward'][-1]: 4.4f} (init={logs['reward'][0]: 4.4f})"
            )
            logs["step_count"].append(tensordict_data["step_count"].max().item())
            stepcount_str = f"step count (max): {logs['step_count'][-1]}"
            logs["lr"].append(self.optim.param_groups[0]["lr"])
            lr_str = f"lr policy: {logs['lr'][-1]: 4.4f}"
            if i % 10 == 0:
                eval_str = self.evaluate(self.env, self.policy_module, logs)

            if i % 1000 == 0:
                self.save(f"base_model.pth", self.policy_module, self.value_module)
            wandb.log(
                {
                    "reward": logs["reward"][-1],
                    "step_count": logs["step_count"][-1],
                    "lr": logs["lr"][-1],
                }
            )
            pbar.set_description(", ".join([eval_str, cum_reward_str, stepcount_str, lr_str]))
            self.scheduler.step()
            self.plot_training(logs)
    logging.info("Training finished")

    # Method for evaluating the trained policy
    def evaluate(self, env, policy_module, logs):
        with set_exploration_type(ExplorationType.MEAN), torch.no_grad():
            # execute a rollout with the trained policy
            eval_rollout = env.rollout(100000, policy_module)
            logs["eval reward"].append(eval_rollout["next", "reward"].mean().item())
            logs["eval reward (sum)"].append(
                eval_rollout["next", "reward"].sum().item()
            )
            logs["eval step_count"].append(eval_rollout["step_count"].max().item())
            eval_str = (
                f"eval cumulative reward: {logs['eval reward (sum)'][-1]: 4.4f} "
                f"(init: {logs['eval reward (sum)'][0]: 4.4f}), "
                f"eval step-count: {logs['eval step_count'][-1]}"
            )
            del eval_rollout
            return eval_str

    # Method for plotting training progress
    def plot_training(self, logs):
        logging.debug("Plotting training")
        plt.figure(figsize=(10, 10))
        plt.subplot(2, 2, 1)
        plt.plot(logs["reward"])
        plt.title("training rewards (average)")
        plt.subplot(2, 2, 2)
        plt.plot(logs["step_count"])
        plt.title("Max step count (training)")
        plt.subplot(2, 2, 3)
        plt.plot(logs["eval reward (sum)"])
        plt.title("Return (test)")
        plt.subplot(2, 2, 4)
        plt.plot(logs["eval step_count"])
        plt.title("Max step count (test)")
        plt.show()


class PPOEvaluate:
    # Initialize PPO algorithm with hyperparameters and device
    def __init__(self, hyperparams, device):
        self.hyperparams = hyperparams
        self.env = None
        self.device = device
        self.policy_module = None
        self.value_module = None
        self.transform = None

    # Set the training environment for PPO
    def set_training_env(self, env):
        logging.info("Setting training environment")
        check_env_specs(env)
        self.env = env
        self.transform = env.transform[0]

        self.policy_module = self.build_policy_module(self.env)
        self.value_module = self.build_value_module()

        # initialize the lazy modules
        logger.info("Initializing Lazy Modules")
        self.policy_module(self.env.reset())
        self.value_module(self.env.reset())

        self.collector = self.build_collectors(self.env, self.policy_module)
        self.replay_buffer = self.build_replay_buffer()
        self.advantage_module = self.build_advantage_module(self.value_module)
        self.loss_module = self.build_loss_module(self.policy_module, self.value_module)
        self.optim, self.scheduler = self.build_optimizer(self.loss_module)

    # Build the policy module for the actor network
    def build_policy_module(self, env):
        logging.info("Building policy module")
        actor_net = nn.Sequential(
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(2 * env.action_spec.shape[-1], device=self.device),
            NormalParamExtractor(),
        )
        dict_module = TensorDictModule(
            actor_net, in_keys=["observation"], out_keys=["loc", "scale"]
        )

        return ProbabilisticActor(
            module=dict_module,
            spec=env.action_spec,
            in_keys=["loc", "scale"],
            distribution_class=TanhNormal,
            distribution_kwargs={
                "min": env.action_spec.space.low,
                "max": env.action_spec.space.high,
            },
            return_log_prob=True,
        )

    # Set the prediction environment
    def set_prediction_env(self, dummy_env):
        self.policy_module = self.build_policy_module(dummy_env)
        self.value_module = self.build_value_module()

    # Build the value module for the critic network
    def build_value_module(self):
        logging.info("Building value module")
        value_net = nn.Sequential(
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(self.hyperparams["num_cells"], device=self.device),
            nn.Tanh(),
            nn.LazyLinear(1, device=self.device),
        )
        return ValueOperator(
            module=value_net,
            in_keys=["observation"],
        )

    # Build data collectors for PPO
    def build_collectors(self, env, policy_module):
        logging.info("Building collectors")
        collector = SyncDataCollector(
            env,
            policy_module,
            frames_per_batch=self.hyperparams["frames_per_batch"],
            total_frames=self.hyperparams["total_frames"],
            split_trajs=False,
            device=self.device,
        )

        return collector

    # Build the replay buffer
    def build_replay_buffer(self):
        logging.info("Building replay buffer")
        return ReplayBuffer(
            storage=LazyTensorStorage(max_size=self.hyperparams["frames_per_batch"]),
            sampler=SamplerWithoutReplacement(),
        )

    # Build the advantage module for GAE
    def build_advantage_module(self, value_module):
        logging.info("Building advantage module")
        return GAE(
            gamma=self.hyperparams["gamma"],
            lmbda=self.hyperparams["lmbda"],
            value_network=value_module,
            average_gae=True,
        )

    # Build the loss module for PPO
    def build_loss_module(self, policy_module, value_module):
        logging.info("Building loss module")
        return ClipPPOLoss(
            actor_network=policy_module,
            critic_network=value_module,
            clip_epsilon=self.hyperparams["clip_epsilon"],
            entropy_bonus=bool(self.hyperparams["entropy_eps"]),
            entropy_coef=self.hyperparams["entropy_eps"],
            critic_coef=1.0,
            loss_critic_type="smooth_l1",
        )

    # Build the optimizer and scheduler for training
    def build_optimizer(self, loss_module):
        logging.info("Building optimizer")
        optim = torch.optim.Adam(loss_module.parameters(), self.hyperparams["lr"])
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optim, self.hyperparams["total_frames"] // self.hyperparams["frames_per_batch"], 0.0
        )
        return optim, scheduler

    # Methods for saving and loading models
    def save(self, path, policy_module, value_module):
        logging.info(f"Saving model to {path}")
        torch.save(
            {
                "policy_module": policy_module.state_dict(),
                "value_module": value_module.state_dict(),
                "transform": self.transform,
            },
            path,
        )

    def save_model(self, path):
        self.save(path, self.policy_module, self.value_module)
    def _load(self, path, policy_module, value_module):
        logging.info(f"Loading model from {path}")
        checkpoint = torch.load(path, map_location=self.device)
        policy_module.load_state_dict(checkpoint["policy_module"])
        value_module.load_state_dict(checkpoint["value_module"])
        self.transform = checkpoint["transform"]

    def load(self, path):
        self._load(path, self.policy_module, self.value_module)

    # Method for predicting actions using the trained policy
    def predict_action(self, observation):
        observation_tensor = torch.from_numpy(observation).float().to(self.device)
        normalized_observation = self.transform(observation_tensor)
        with torch.no_grad():
            return self.policy_module(normalized_observation)

    # Main training loop for PPO
    def train(self):
        plt.ion()
        plt.clf()
        self.env.rollout(3)
        logging.info("Starting training - PPO")
        logs = defaultdict(list)
        pbar = tqdm(total=self.hyperparams["total_frames"])
        eval_str = ""
        logger.info("Starting training loop")

        for i, tensordict_data in enumerate(self.collector):
            for _ in range(self.hyperparams["num_epochs"]):
                self.advantage_module(tensordict_data)
                data_view = tensordict_data.reshape(-1)
                self.replay_buffer.extend(data_view.cpu())
                for _ in range(self.hyperparams["frames_per_batch"] // self.hyperparams["sub_batch_size"]):
                    subdata = self.replay_buffer.sample(self.hyperparams["sub_batch_size"])
                    loss_vals = self.loss_module(subdata.to(self.device))
                    loss_value = (
                            loss_vals["loss_objective"]
                            + loss_vals["loss_critic"]
                            + loss_vals["loss_entropy"]
                    )
                    loss_value.backward()
                    torch.nn.utils.clip_grad_norm_(self.loss_module.parameters(), self.hyperparams["max_grad_norm"])
                    self.optim.step()
                    self.optim.zero_grad()

            logs["reward"].append(tensordict_data["next", "reward"].mean().item())
            pbar.update(tensordict_data.numel())
            cum_reward_str = (
                f"average reward={logs['reward'][-1]: 4.4f} (init={logs['reward'][0]: 4.4f})"
            )
            logs["step_count"].append(tensordict_data["step_count"].max().item())
            stepcount_str = f"step count (max): {logs['step_count'][-1]}"
            logs["lr"].append(self.optim.param_groups[0]["lr"])
            lr_str = f"lr policy: {logs['lr'][-1]: 4.4f}"
            if i % 10 == 0:
                eval_str = self.evaluate(self.env, self.policy_module, logs)

            if i % 1000 == 0:
                self.save(f"base_model.pth", self.policy_module, self.value_module)
            pbar.set_description(", ".join([eval_str, cum_reward_str, stepcount_str, lr_str]))
            self.scheduler.step()
            self.plot_training(logs)
    logging.info("Training finished")

    # Method for evaluating the trained policy
    def evaluate(self, env, policy_module, logs):
        with set_exploration_type(ExplorationType.MEAN), torch.no_grad():
            # execute a rollout with the trained policy
            eval_rollout = env.rollout(100000, policy_module)
            logs["eval reward"].append(eval_rollout["next", "reward"].mean().item())
            logs["eval reward (sum)"].append(
                eval_rollout["next", "reward"].sum().item()
            )
            logs["eval step_count"].append(eval_rollout["step_count"].max().item())
            eval_str = (
                f"eval cumulative reward: {logs['eval reward (sum)'][-1]: 4.4f} "
                f"(init: {logs['eval reward (sum)'][0]: 4.4f}), "
                f"eval step-count: {logs['eval step_count'][-1]}"
            )
            del eval_rollout
            return eval_str

    # Method for plotting training progress
    def plot_training(self, logs):
        logging.debug("Plotting training")
        plt.figure(figsize=(10, 10))
        plt.subplot(2, 2, 1)
        plt.plot(logs["reward"])
        plt.title("training rewards (average)")
        plt.subplot(2, 2, 2)
        plt.plot(logs["step_count"])
        plt.title("Max step count (training)")
        plt.subplot(2, 2, 3)
        plt.plot(logs["eval reward (sum)"])
        plt.title("Return (test)")
        plt.subplot(2, 2, 4)
        plt.plot(logs["eval step_count"])
        plt.title("Max step count (test)")
        plt.show()
