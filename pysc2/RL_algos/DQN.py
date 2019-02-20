# adapted from https://github.com/keon/deep-q-learning/blob/master/dqn.py
# while looking at https://towardsdatascience.com/reinforcement-learning-w-keras-openai-dqns-1eed3a5338c
# and https://medium.com/@jonathan_hui/rl-dqn-deep-q-network-e207751f7ae4 (1)

# -*- coding: utf-8 -*-
import random
import os
import numpy as np
from collections import deque
import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import RMSprop
from pysc2.RL_algos.RL_Model import RLModel

EPISODES = 1000

class DQNModel(RLModel):

    # hidden_layers of type
    def __init__(self, state_size, action_size, hidden_layers=[24, 24]):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95    # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.batch_size = 32  # takes batch sizes of 32 for learning
        self.learning_rate = 0.001  # for gradient descent
        self.tau = 0.125  # for learning new model
        self.model = self._build_model(hidden_layers)
        self.target_model = self._build_model(hidden_layers)
        self.target_train(copy=True)


    def _build_model(self, hidden_layers):

        # the loss function for DQN networks (1)
        def huber_loss(y_true, y_pred):
            return tf.losses.huber_loss(y_true, y_pred)

        # Neural Net for Deep-Q learning Model

        model = Sequential()
        model.add(Dense(hidden_layers[0], input_dim=self.state_size, activation='relu'))
        for hns in hidden_layers[1:-1]:
            model.add(Dense(hns, activation='relu'))
        model.add(Dense(self.action_size, activation='softmax'))
        model.compile(loss=huber_loss,
                      optimizer=RMSprop(lr=self.learning_rate))
        return model

    def act(self, state):
        # epsilon - greedy function (1)
        state = np.reshape(state, [1, len(state)])
        act_values = self.model.predict(state)
        best_action = np.argmax(act_values[0])
        if np.random.rand() <= self.epsilon - self.epsilon/self.action_size:
            return random.choice([i for i in range(len(act_values[0])) if i != best_action])
        return best_action  # returns action

    def learn(self, state, action, reward, next_state, done=False):
        state = self._normalize_state(state)
        next_state = np.zeros([1, len(state)]) if next_state == "terminal" else self._normalize_state(next_state)
        self.memory.append((state, action, reward, next_state, done))
        self._replay()

    def _replay(self):
        if len(self.memory) < self.batch_size:
            return

        minibatch = random.sample(self.memory, self.batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = (reward + self.gamma *
                          np.amax(self.target_model.predict(next_state)[0]))
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, verbose=0)

        # decrease epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        # copy over model
        self.target_train()

    def target_train(self, copy=False):
        weights = self.model.get_weights()
        target_weights = self.target_model.get_weights()
        for i in range(len(target_weights)):
            if not copy:
                target_weights[i] = weights[i] * self.tau + target_weights[i] * (1 - self.tau)
            else:
                target_weights[i] = weights[i]
        self.target_model.set_weights(target_weights)

    def load_model(self, file_name):
        if os.path.isfile(file_name):
            self.model.load_weights(file_name)

    def save_model(self, file_name):
        self.model.save_weights(file_name)

    def _normalize_state(self, state):
        state = np.array(state)
        state = np.reshape(state, [1, len(state)])
        return state
"""
if __name__ == "__main__":
    env = gym.make('CartPole-v1')
    state_size = env.observation_space.shape[0]
    action_size = env.action_space.n
    agent = DQNAgent(state_size, action_size)
    # agent.load("./save/cartpole-dqn.h5")
    done = False
    batch_size = 32

    for e in range(EPISODES):
        state = env.reset()
        state = np.reshape(state, [1, state_size])
        for time in range(500):
            # env.render()
            action = agent.act(state)
            next_state, reward, done, _ = env.step(action)
            reward = reward if not done else -10
            next_state = np.reshape(next_state, [1, state_size])
            agent.learn(state, action, reward, next_state, done)
            state = next_state
            if done:
                print("episode: {}/{}, score: {}, e: {:.2}"
                      .format(e, EPISODES, time, agent.epsilon))
                break
        # if e % 10 == 0:
        #     agent.save("./save/cartpole-dqn.h5")
"""