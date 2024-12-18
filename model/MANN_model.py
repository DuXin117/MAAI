'''
Author: Xin Du
Date: 2023-12-07 14:57:35
LastEditors: Xin Du
LastEditTime: 2024-12-18 22:17:19
Description: file content
'''
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


class MemoryAugmentedLayer(keras.layers.Layer):
    def __init__(self ,
         memory_units ,
         memory_size  ,
         key_size     ,
         dropout = 0.1,
         activation = 'elu',
         **kwargs):
        super(MemoryAugmentedLayer, self).__init__(**kwargs)
        self.memory_units = memory_units
        self.memory_size = memory_size
        self.key_size = key_size
        self.read_attention = keras.layers.Dense(self.memory_units, activation='softmax')
        self.write_attention = keras.layers.Dense(self.memory_units, activation='softmax')

        self.key_generation = keras.Sequential([ 
            layers.Dense(
            self.key_size,
            kernel_initializer='glorot_uniform',
            activation=activation
            ),
        ])

        self.value_generation = keras.Sequential([ 
            layers.Dense(
            self.memory_size,
            kernel_initializer='glorot_uniform',
            activation=activation
            ),
        ])

        self.query_generation = keras.Sequential([ 
            layers.Dense(
            self.key_size,
            kernel_initializer='glorot_uniform',
            activation=activation
            ),
        ])

    def build(self, input_shape):
        self.key_memory = self.add_weight(
            shape=(
            self.memory_units, self.key_size),
            initializer='glorot_uniform',
            trainable=False,
            name='key_memory')

        self.value_memory = self.add_weight(shape=(
            self.memory_units, self.memory_size),
            initializer='glorot_uniform',
            trainable=False,
            name='value_memory')

        super(MemoryAugmentedLayer, self).build(input_shape)


    def call(self, inputs):

        key_vector = self.key_generation(inputs)  
        value_vector = self.value_generation(inputs)  
        query_vector = self.query_generation(inputs)  

        write_weights = self.write_attention(tf.matmul(key_vector, self.key_memory, transpose_b=True)) 
        write_weights_expanded = tf.expand_dims(write_weights, axis=-1)
        key_memory_update = tf.multiply(write_weights_expanded, tf.expand_dims(key_vector, axis=1))  
        self.key_memory.assign_add(tf.reduce_mean(key_memory_update, axis=0))  

        value_memory_update = tf.multiply(write_weights_expanded, tf.expand_dims(value_vector, axis=1))  
        self.value_memory.assign_add(tf.reduce_mean(value_memory_update, axis=0))  
        read_weights = self.read_attention(tf.matmul(query_vector, self.key_memory, transpose_b=True)) 
        read_vector = tf.matmul(read_weights, self.value_memory) 
        return read_vector



class MemoryAugmentedNN(keras.Model):

    def __init__(self, 
        input_dim = 18, 
        output_dim = 18, 
        enc_dim = 128,
        memory_units = 128, 
        memory_size = 64,
        key_size = 128,
        dropout = 0.1,
        activation = 'elu',
        ):
        super(MemoryAugmentedNN, self).__init__()

        self.encoder = keras.layers.Dense(enc_dim, activation='relu')

        self.encoder = keras.Sequential([ 
            layers.Dense(
            enc_dim,
            kernel_initializer='glorot_uniform',
            activation=activation
            ),
            layers.Dropout(dropout)
        ])

        self.memory_augmented_layer = MemoryAugmentedLayer(memory_units, memory_size, key_size, dropout, activation)
        
        self.decoder = keras.Sequential([ 
                        layers.Dense(
                        enc_dim,
                        kernel_initializer='glorot_uniform',
                        activation=activation
                        ),
                        layers.Dropout(dropout)
        ])

        self.output_layer = layers.Dense(
                                output_dim, 
                                kernel_initializer='glorot_uniform', 
                                activation='linear'
        )


    def call(self, inputs):
        encoded = self.encoder(inputs)
        read_vector = self.memory_augmented_layer(encoded)
        decoder_input = tf.concat([encoded, read_vector], axis = 1)
        decoded = self.decoder(decoder_input)
        outputs = self.output_layer(decoded)
        return outputs

