"""
Module description:

"""

__version__ = '0.1'
__author__ = 'Vito Walter Anelli, Claudio Pomo, Daniele Malitesta, Antonio Ferrara'
__email__ = 'vitowalter.anelli@poliba.it, claudio.pomo@poliba.it,' \
            'daniele.malitesta@poliba.it, antonio.ferrara@poliba.it'

import os

import numpy as np
import tensorflow as tf
from tensorflow import keras

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.random.set_seed(0)


class DeepFMModel(keras.Model):
    def __init__(self,
                 num_users,
                 num_items,
                 embed_mf_size,
                 hidden_layers,
                 lambda_weights,
                 learning_rate=0.01,
                 name="DeepFM",
                 **kwargs):
        super().__init__(name=name, **kwargs)
        tf.random.set_seed(42)
        self.num_users = num_users
        self.num_items = num_items
        self.embed_mf_size = embed_mf_size
        self.hidden_layers = hidden_layers  # Specify as ((5, 'sigmoid'), (10, 'relu'))
        self.lambda_weights = lambda_weights

        self.initializer = tf.initializers.GlorotUniform()

        self.user_mf_embedding = keras.layers.Embedding(input_dim=self.num_users, output_dim=self.embed_mf_size,
                                                        embeddings_initializer=self.initializer, name='U_MF',
                                                        embeddings_regularizer=keras.regularizers.l2(
                                                            self.lambda_weights),
                                                        dtype=tf.float32)
        self.item_mf_embedding = keras.layers.Embedding(input_dim=self.num_items, output_dim=self.embed_mf_size,
                                                        embeddings_regularizer=keras.regularizers.l2(
                                                            self.lambda_weights),
                                                        embeddings_initializer=self.initializer, name='I_MF',
                                                        dtype=tf.float32)

        self.u_bias = keras.layers.Embedding(input_dim=self.num_users, output_dim=1,
                                             embeddings_initializer=self.initializer, name='B_U_MF',
                                             dtype=tf.float32)
        self.i_bias = keras.layers.Embedding(input_dim=self.num_items, output_dim=1,
                                             embeddings_initializer=self.initializer, name='B_I_MF',
                                             dtype=tf.float32)

        self.bias_ = tf.Variable(0., name='GB')

        self.user_mf_embedding(0)
        self.item_mf_embedding(0)
        self.u_bias(0)
        self.i_bias(0)

        self.hidden = tf.keras.Sequential(
            [tf.keras.layers.Dense(self.hidden_layers[0][0],
                                   activation=self.hidden_layers[0][1], input_dim=2*self.embed_mf_size)] +
            [tf.keras.layers.Dense(n, activation=act) for n, act in self.hidden_layers[1:]]
        )

        self.prediction_layer = tf.keras.layers.Dense(1, input_dim=self.hidden_layers[-1][0], activation='sigmoid')

        self.loss = keras.losses.BinaryCrossentropy()

        self.optimizer = tf.optimizers.Adam(learning_rate)

    @tf.function
    def call(self, inputs, training=None, mask=None):
        user, item = inputs
        user_mf_e = self.user_mf_embedding(user)
        item_mf_e = self.item_mf_embedding(item)
        fm_output = tf.reduce_sum(user_mf_e * item_mf_e, axis=-1)
        fm_output += self.bias_ + self.u_bias(user) + self.i_bias(item)
        nn_input = tf.concat([user_mf_e, item_mf_e], axis=-1)
        hidden_output = self.hidden(nn_input)
        nn_output = self.prediction_layer(hidden_output)

        return tf.sigmoid(fm_output + nn_output)

    @tf.function
    def train_step(self, batch):
        user, pos, label = batch
        with tf.GradientTape() as tape:
            # Clean Inference
            output = self(inputs=(user, pos), training=True)
            loss = self.loss(label, output)

        grads = tape.gradient(loss, self.trainable_weights)
        self.optimizer.apply_gradients(zip(grads, self.trainable_weights))

        return loss

    @tf.function
    def predict(self, inputs, training=False, **kwargs):
        """
        Get full predictions on the whole users/items matrix.

        Returns:
            The matrix of predicted values.
        """
        output = self.call(inputs=inputs, training=training)
        return output

    @tf.function
    def get_recs(self, inputs, training=False, **kwargs):
        """
        Get full predictions on the whole users/items matrix.

        Returns:
            The matrix of predicted values.
        """
        user, item = inputs
        user_mf_e = self.user_mf_embedding(user)
        item_mf_e = self.item_mf_embedding(item)
        fm_output = tf.expand_dims(tf.reduce_sum(user_mf_e * item_mf_e, axis=-1), -1)
        fm_output += self.bias_ + self.u_bias(user) + self.i_bias(item)
        nn_input = tf.concat([user_mf_e, item_mf_e], axis=-1)
        hidden_output = self.hidden(nn_input)
        nn_output = self.prediction_layer(hidden_output)

        return tf.squeeze(tf.sigmoid(fm_output + nn_output))

    @tf.function
    def get_top_k(self, preds, train_mask, k=100):
        return tf.nn.top_k(tf.where(train_mask, preds, -np.inf), k=k, sorted=True)
