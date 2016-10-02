import lasagne.layers as L
import lasagne.nonlinearities as LN
import lasagne.init as LI
import theano.tensor as TT
import theano
from rllab.misc import ext
from rllab.core.lasagne_layers import OpLayer
from rllab.core.lasagne_powered import LasagnePowered
from rllab.core.serializable import Serializable

import numpy as np


def wrapped_conv(*args, **kwargs):
    copy = dict(kwargs)
    copy.pop("image_shape", None)
    copy.pop("filter_shape", None)
    assert copy.pop("filter_flip", False)

    input, W, input_shape, get_W_shape = args
    if theano.config.device == 'cpu':
        return theano.tensor.nnet.conv2d(*args, **kwargs)
    try:
        return theano.sandbox.cuda.dnn.dnn_conv(
            input.astype('float32'),
            W.astype('float32'),
            **copy
        )
    except Exception as e:
        print("falling back to default conv2d")
        return theano.tensor.nnet.conv2d(*args, **kwargs)

class ConvNetwork(object):
    def __init__(self, input_shape, output_dim, hidden_sizes,
                 conv_filters, conv_filter_sizes, conv_strides, conv_pads,
                 hidden_W_init=LI.GlorotUniform(), hidden_b_init=LI.Constant(0.),
                 output_W_init=LI.GlorotUniform(), output_b_init=LI.Constant(0.),
                 # conv_W_init=LI.GlorotUniform(), conv_b_init=LI.Constant(0.),
                 hidden_nonlinearity=LN.rectify,
                 output_nonlinearity=LN.softmax,
                 name=None, input_var=None):

        if name is None:
            prefix = ""
        else:
            prefix = name + "_"

        if len(input_shape) == 3:
            l_in = L.InputLayer(shape=(None, np.prod(input_shape)), input_var=input_var)
            l_hid = L.reshape(l_in, ([0],) + input_shape)
        elif len(input_shape) == 2:
            l_in = L.InputLayer(shape=(None, np.prod(input_shape)), input_var=input_var)
            input_shape = (1,) + input_shape
            l_hid = L.reshape(l_in, ([0],) + input_shape)
        else:
            l_in = L.InputLayer(shape=(None,) + input_shape, input_var=input_var)
            l_hid = l_in
        for idx, conv_filter, filter_size, stride, pad in zip(
                range(len(conv_filters)),
                conv_filters,
                conv_filter_sizes,
                conv_strides,
                conv_pads,
        ):
            l_hid = L.Conv2DLayer(
                l_hid,
                num_filters=conv_filter,
                filter_size=filter_size,
                stride=(stride, stride),
                pad=pad,
                nonlinearity=hidden_nonlinearity,
                name="%sconv_hidden_%d" % (prefix, idx),
                convolution=wrapped_conv,
            )
        for idx, hidden_size in enumerate(hidden_sizes):
            l_hid = L.DenseLayer(
                l_hid,
                num_units=hidden_size,
                nonlinearity=hidden_nonlinearity,
                name="%shidden_%d" % (prefix, idx),
                W=hidden_W_init,
                b=hidden_b_init,
            )
        l_out = L.DenseLayer(
            l_hid,
            num_units=output_dim,
            nonlinearity=output_nonlinearity,
            name="%soutput" % (prefix,),
            W=output_W_init,
            b=output_b_init,
        )
        self._l_in = l_in
        self._l_out = l_out
        self._input_var = l_in.input_var

    @property
    def input_layer(self):
        return self._l_in

    @property
    def output_layer(self):
        return self._l_out

    @property
    def input_var(self):
        return self._l_in.input_var
