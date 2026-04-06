# -*- coding: utf-8 -*-
"""
Created on Sat Jun 17 15:56:34 2023

@author: whuxu
"""
import tensorflow as tf
import os
    
class FeedForward(tf.keras.layers.Layer):
    def __init__(self, dim, d_ffn):
        super(FeedForward, self).__init__()

        self.fc1 = tf.keras.layers.Dense(d_ffn, use_bias=False)
        self.fc2 = tf.keras.layers.Dense(dim, use_bias=False)
        self.fc3 = tf.keras.layers.Dense(d_ffn, use_bias=False)
    
    def call(self, x):
        return self.fc2(tf.nn.swish(self.fc1(x)) * self.fc3(x))
    
class RMSNorm(tf.keras.layers.Layer):
    def __init__(self, dim, eps=1e-6):
        super(RMSNorm, self).__init__()
        self.eps = eps
        self.dim = dim

    def build(self, input_shape):

        self.weight = self.add_variable(name="RMSNorm_w",
                                        shape=(self.dim,),
                                        initializer=tf.ones_initializer(),
                                        trainable=True)
        self.built = True

    def call(self, x):
        output = x * tf.math.rsqrt(tf.reduce_mean(tf.math.square(x), -1, keepdims=True) + self.eps)
        return output * self.weight
    
class OPUSGO(tf.keras.Model):
    def __init__(self, d_model, d_ffn,
                 d_out, drop_rate=0.5):
        
        super(OPUSGO, self).__init__()
        
        self.d_out = d_out
        
        self.ffn_norm = RMSNorm(dim=d_model)
        self.ffn = FeedForward(d_model, d_ffn)     
        self.dropout = tf.keras.layers.Dropout(drop_rate)
        self.final_layer = tf.keras.layers.Dense(d_out)

    def call(self, inputs, training=False):
        assert inputs.shape[-1] == 1280
        
        decode_out = self.ffn(inputs)
        decode_out = tf.nn.swish(decode_out)
        decode_out = self.ffn_norm(decode_out)
        decode_out = self.dropout(decode_out, training=training)
        logit = self.final_layer(decode_out) # (1, L, 5106)
        
        out = tf.sigmoid(logit)
        out = out.numpy()
        
        return out

    def load_model(self, name=None):
        print ("load_weights", name)
        self.load_weights(os.path.join('./models/', name))
