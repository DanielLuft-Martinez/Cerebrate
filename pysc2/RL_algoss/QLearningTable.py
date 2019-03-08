# copied from https://github.com/skjb/pysc2-tutorial

import numpy as np
import pandas as pd
from pysc2.RL_algos.RL_Model import RLModel

import os


class QLearningTable(RLModel):
    def __init__(self, actions, data_file="", learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.DATA_FILE = data_file
        self.actions = actions  # a list
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)
        self.disallowed_actions = {}

    def act(self, state, excluded_actions=[]):
        self._check_state_exist(state)

        self.disallowed_actions[state] = excluded_actions

        state_action = self.q_table.ix[state, :]

        for excluded_action in excluded_actions:
            del state_action[excluded_action]

        if np.random.uniform() < self.epsilon:
            # some actions have the same value
            state_action = state_action.reindex(np.random.permutation(state_action.index))

            action = state_action.idxmax()
        else:
            action = np.random.choice(state_action.index)

        return action

    def learn(self, state, action, reward, next_state, done=False):
        if state == next_state:
            return

        self._check_state_exist(state)
        self._check_state_exist(next_state)

        q_predict = self.q_table.ix[state, action]

        s_rewards = self.q_table.ix[next_state, :]

        if next_state in self.disallowed_actions:
            for excluded_action in self.disallowed_actions[next_state]:
                del s_rewards[excluded_action]

        if done:
            q_target = reward  # next state is terminal
        else:
            q_target = reward + self.gamma * s_rewards.max()

        # update
        self.q_table.ix[state, action] += self.lr * (q_target - q_predict)

    def _check_state_exist(self, state):
        if state not in self.q_table.index:
            # append new state to q table
            self.q_table = self.q_table.append(
                pd.Series([0] * len(self.actions), index=self.q_table.columns, name=state))

    def load_model(self, file_name):
        return
        if os.path.isfile(file_name + '.gz'):
            self.q_table = pd.read_pickle(file_name + '.gz', compression='gzip')

    def save_model(self, file_name):
        self.q_table.to_pickle(file_name + '.gz', 'gzip')
