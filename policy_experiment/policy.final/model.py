#!/usr/bin/python3
#-*-coding:utf-8-*-
#$File: model.py
#$Date: Sat May  7 10:59:45 2016
#$Author: Like Ma <milkpku[at]gmail[dot]com>

from config import config

import tensorflow as tf
import functools

from util.model import Model, conv2d

def get_model(name):
    with tf.name_scope(name) as scope:

        self_pos = tf.placeholder(config.dtype, config.data_shape, name='self_pos')
        enemy_pos = tf.placeholder(config.dtype, config.data_shape, name='enemy_pos')
        self_ability = tf.placeholder(config.dtype, config.data_shape, name='self_ability')
        enemy_ability = tf.placeholder(config.dtype, config.data_shape, name='enemy_ability')
        self_protect = tf.placeholder(config.dtype, config.data_shape, name='self_protect')
        enemy_protect = tf.placeholder(config.dtype, config.data_shape, name='enemy_protect')

        input_label = tf.placeholder(config.dtype, config.label_shape, name='input_label')

        x = tf.concat(3, [self_pos, enemy_pos, self_ability, enemy_ability, self_protect, enemy_protect], name='input_concat')
        y = input_label

        nl = tf.nn.tanh

        def conv_pip(name, x):
            with tf.name_scope(name) as scope:
                x = conv2d('0', x, config.data_shape[3]*2, kernel=3, stride=1, nl=nl)
                x = conv2d('1', x, config.data_shape[3], kernel=3, stride=1, nl=nl)
            return x

        pred = conv_pip('conv0', x)
        for layer in range(5):
            pred_branch = tf.concat(3, [pred,x], name='concate%d'%layer)
            pred += conv_pip('conv%d'%(layer+1), pred_branch)

        a = tf.Variable(2.0, dtype=tf.float32, name='control_tanh_const')
        x = a*tf.tanh(pred, name='control_tanh')

        z = tf.mul(tf.exp(x), self_ability)
        z_sum = tf.reduce_sum(z, reduction_indices=[1,2,3], name='partition_function') # partition function

        # another formula of y*logy
        loss = -tf.reduce_sum(tf.mul(x, y), reduction_indices=[1,2,3]) + tf.log(z_sum)
        z_sum = tf.reshape(z_sum, [-1, 1, 1, 1])
        pred = tf.div(z, z_sum, name='predict')
        return Model([self_pos, enemy_pos, self_ability, enemy_ability, self_protect, enemy_protect], input_label, loss, pred, debug=[z, z_sum])

if __name__=='__main__':

    model = get_model('test')
    sess = tf.InteractiveSession()
    sess.run(tf.initialize_all_variables())

    import numpy as np
    x_data = np.random.randint(2, size=[6,100,9,10,16]).astype('float32')
    y_data = np.random.randint(2, size=[100,9,10,16]).astype('float32')

    train_writer = tf.train.SummaryWriter('train_log/', sess.graph)

    input_dict = {}
    for var, data in zip(model.inputs, x_data):
        input_dict[var] = data
    input_dict[model.label] = y_data

    loss_val = model.loss.eval(feed_dict=input_dict)
    pred_val = model.pred.eval(feed_dict=input_dict)
    # print(loss_val)
    print(pred_val)

    pred_val = pred_val.reshape(pred_val.shape[0], -1)
    assert all(abs(pred_val.sum(axis=1)-1.0<1e-6))

    self_ability = x_data[2].reshape(x_data[2].shape[0], -1)
    assert all(np.logical_xor(self_ability>0, pred_val<=0).reshape(-1))
    print('model test OK')
