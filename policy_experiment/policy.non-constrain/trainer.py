#!/usr/bin/python3
#-*-coding:utf-8-*-
#$File: trainer.py
#$Date: Sat May  7 11:00:10 2016
#$Author: Like Ma <milkpku[at]gmail[dot]com>

from config import Config
from dataset import load_data
from model import get_model

import tensorflow as tf

import argparse

def train(args):

    device = args.device
    load_path = args.load_path
    # load data
    train_data = load_data('train')
    val_data = load_data('validation')

    # load model
    with tf.device('/gpu:%d' % device):
        model = get_model('train')

    # trainer init
    optimizer = Config.optimizer
    train_step = optimizer.minimize(model.loss)

    # init session and server
    sess = tf.InteractiveSession()
    saver = tf.train.Saver()
    if load_path==None:
        sess.run(tf.initialize_all_variables())
    else:
        saver.restore(sess, load_path)
        print("Model restored from %s" % load_path)

    # accuracy
    pred = tf.reshape(model.pred, [-1, 9*10*16])
    label = tf.reshape(model.label, [-1, 9*10*16])
    correct_prediction = tf.equal(tf.argmax(pred, 1), tf.argmax(label,1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    # train steps
    for i in range(Config.n_epoch):

        # training step
        batch_data, batch_label = train_data.next_batch(Config.minibatch_size)

        input_dict = {model.label:batch_label}
        for var, data in zip(model.inputs, batch_data):
            input_dict[var]=data

        #from IPython import embed;embed()
        sess.run(train_step, feed_dict=input_dict)

        # evalue step
        if (i+1)%Config.evalue_point == 0:
            batch_data, batch_label = val_data.next_batch(Config.minibatch_size)
            val_dict = {model.label:batch_label}
            for var, data in zip(model.inputs, batch_data):
                val_dict[var]=data
            score = accuracy.eval(feed_dict=val_dict)
            print("epoch %d, accuracy is %.2f" % (i,score))

        # save step
        if (i+1)%Config.check_point == 0:
            save_path = saver.save(sess, "%s/epoch-%d" %(Config.save_path, i))
            print("Model saved in file: %s" % save_path)

if __name__=='__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", type=int, default=0, help="gpu id")
    parser.add_argument("-c", "--load_path", default=None, help="load trained model")
    args = parser.parse_args()

    train(args)
