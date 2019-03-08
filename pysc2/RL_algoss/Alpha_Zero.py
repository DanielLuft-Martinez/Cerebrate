# adapted from https://github.com/AppliedDataSciencePartners/DeepReinforcementLearning/blob/master/model.py
# used https://applied-data.science/static/main/res/alpha_go_zero_cheat_sheet.png

import keras.layers as layers
import keras
import tensorflow as tf
from keras import optimizers

def add_convolutional_layer(x):
    x = layers.Conv2D(256, 3, activation='relu')(x)
    x = layers.BatchNormalization(axis=1)(x)
    x = layers.ReLU()(x)
    return x


def add_residual_layer(x):
    x1 = add_convolutional_layer(x)
    x1 = layers.Conv2D(256, 3, activation='relu')(x1)
    x1 = layers.BatchNormalization(axis=1)(x1)
    x1 = layers.add([x, x1])
    x1 = layers.ReLU(x1)
    return x1


def value_head(x):
    x = layers.Conv2D(1,1, activation='relu')(x)
    x = layers.BatchNormalization(axis=1)(x)
    x = layers.ReLU()(x)
    x = layers.Flatten()(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.ReLU()(x)
    x = layers.Dense(1, activation='tanh', name='value_head')(x)
    return x


def policy_head(x, output_dim):
    x = layers.Conv2D(2, 1, activation='relu')(x)
    x = layers.BatchNormalization(axis=1)(x)
    x = layers.ReLU()(x)
    x = layers.Flatten()(x)
    x = layers.Dense(output_dim, activation='softmax', name='policy_head')(x)
    return x


def build_AZmodel(input_dim, output_dim, no_of_residual_layers, learning_rate, momentum):
    main_input = layers.Input(shape=input_dim)

    x = add_convolutional_layer(main_input)

    for _ in range(no_of_residual_layers):
        x = add_residual_layer(x)

    vh = value_head(x)
    ph = policy_head(x, output_dim)

    model = keras.Model(inputs=[main_input], outputs=[vh, ph])
    model.compile(loss={'value_head': 'mean_squared_error', 'policy_head': tf.nn.softmax_cross_entropy_with_logits},
                  optimizer=optimizers.SGD(lr=learning_rate, momentum=momentum)
                  )

    return model
