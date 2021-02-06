from abc import ABC

import numpy as np
import gym
from gym import spaces

from kaggle_environments import make
from kaggle_environments.envs.hungry_geese.hungry_geese import Action, translate

ACTION_NAMES = {0: 'NORTH',
                1: 'SOUTH',
                2: 'WEST',
                3: 'EAST'}

OPPOSITE_ACTION_NAMES = {0: 'SOUTH',
                         1: 'NORTH',
                         2: 'EAST',
                         3: 'WEST'}


class GooseEnv(gym.Env, ABC):

    def __init__(self, debug=False):
        self._env = make('hungry_geese',
                         configuration={
                             'min_food': 2
                         },
                         debug=debug)
        self._config = self._env.configuration
        obs_shape = self._config.columns * self._config.rows

        self._debug = debug
        self._trainer = self._env.train([None, "greedy"])
        self._previous_obs = None  # agent should know the prev. obs to get a direction of a goose moving
        self._previous_state = None

        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(low=-0.5, high=1, shape=(2*obs_shape,), dtype=np.float64)

    def reset(self):
        state = self._trainer.reset()
        self._previous_state = state
        obs = get_obs(self._env.configuration, state)
        double_obs = np.concatenate((obs, obs))
        self._previous_obs = obs
        return double_obs

    def step(self, action: int):
        if self._debug:
            print(f"Action to do: {ACTION_NAMES[action]}")
        state = self._trainer.step(ACTION_NAMES[action])
        obs = get_obs(self._env.configuration, state[0])
        double_obs = np.concatenate((self._previous_obs, obs))
        self._previous_obs = obs

        done = state[2]
        info = state[3]

        reward = state[1]
        reward += self.get_reward_for_food(action)
        self._previous_state = state[0]

        restricted = OPPOSITE_ACTION_NAMES[action]
        info['allowed_actions'] = [x for x in ACTION_NAMES if ACTION_NAMES[x] != restricted]
        return double_obs, reward, done, info

    def get_reward_for_food(self, action):
        goose_head = self._previous_state['geese'][0][0]
        food = self._previous_state['food']
        next_head = translate(goose_head, Action[ACTION_NAMES[action]], self._config.columns, self._config.rows)
        if next_head in food:
            return 10
        else:
            return 0


def get_obs(config, state):
    """
    Returns an observation map with geese and food;

    Args:
        config: kaggle environment env.configuration object
        state: kaggle environment env.reset or env.step methods output object

    Returns:
        obs: np.ndarray with observations
    """

    player_number = 2
    food_number = 1
    enemy_number = -1

    obs = np.zeros([config.columns * config.rows])
    # mark geese
    n_geese = len(state['geese'])
    obs[state['geese'][0]] = player_number
    for i in range(1, n_geese):
        obs[state['geese'][i]] = enemy_number
    # mark food
    obs[state['food']] = food_number
    # normalize
    obs = obs / player_number
    return obs
