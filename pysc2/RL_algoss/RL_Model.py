class RLModel:
    def act(self, state):
        raise NotImplemented

    def learn(self, state, action, reward, next_state, done):
        raise NotImplemented

    def save_model(self, file_name):
        raise NotImplemented

    def load_model(self, file_name):
        raise NotImplemented
