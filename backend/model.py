# -*- coding: utf-8 -*-


# Commented out IPython magic to ensure Python compatibility.
import re
from typing import Dict, List, Optional, Text, Tuple
# %matplotlib inline
import matplotlib.pyplot as plt
from matplotlib import colors

import tensorflow as tf
import numpy as np
import pandas as pd

"""Note: This links your Google Drive to Colab. Useful if the data is stored in Google Drive."""

from google.colab import drive
drive.mount('/content/drive')

"""# 2. Common functions

These come from the original paper's [GitHub](https://github.com/google-research/google-research/tree/master/simulation_research/next_day_wildfire_spread), and have been modified slightly.

Run the following three cells to define the required library functions for loading the data.
"""

# Constants for the data reader

INPUT_FEATURES = ['elevation', 'th', 'vs',  'tmmn', 'tmmx', 'sph',
                  'pr', 'pdsi', 'NDVI', 'population', 'erc', 'PrevFireMask']

OUTPUT_FEATURES = ['FireMask']

# Data statistics
# For each variable, the statistics are ordered in the form:
# (min_clip, max_clip, mean, std)
# I recalculated the statistics based on the training set only (uncropped)
DATA_STATS = {
    # 0.1 percentile, 99.9 percentile
    # Elevation
    'elevation' : (0.0, 3536.0, 896.5714, 842.6101),
    # Drought index - this claimed to be pressure, but it's Palmer Drought Severity Index
    # https://en.wikipedia.org/wiki/Palmer_drought_index
    # 0.1 percentile, 99.9 percentile
    'pdsi' : (-6.0559, 6.7432, -0.7729, 2.4407),
    # Normalized Difference Vegetation Index https://gisgeography.com/ndvi-normalized-difference-vegetation-index/
    'NDVI' : (-3826.0, 9282.0, 5350.6865, 2185.2192),
    # Precipitation in mm.
    # Negative values make no sense, so min is set to 0.
    # 0., 99.9 percentile
    'pr': (0.0, 19.2422, 0.3234289, 1.5336641),
    # Specific humidity ranges from 0 to 100%.
    'sph': (0., 1., 0.0065263123, 0.003735537), #max changed to 1
    # Wind direction - degrees clockwise from north.
    # Thus min set to 0 and max set to 360.
    'th' : (0.0, 360.0, 146.6468, 3435.0725),
    # Min/max temperature in Kelvin.
    # -20 degree C, 99.9 percentile
    'tmmn' : (253.15, 299.6313, 281.85196, 18.4972), #min changed
    # -20 degree C, 99.9 percentile
    'tmmx' : (253.15, 317.3869, 297.71643, 19.4581), #min changed
    # Wind speed.
    # Negative values do not make sense, given there is a wind direction.
    # 0., 99.9 percentile
    'vs' : (0.0, 9.7368, 3.6278, 1.3092),
    # NFDRS fire danger index energy release component expressed in BTU's per
    # square foot.
    # Negative values do not make sense. Thus min set to zero.
    # 0., 99.9 percentile
    'erc' : (0.0, 109.9254, 53.4690, 25.0980),
    # Population
    # min, 99.9 percentile
    'population' : (0.0, 2935.7548828125, 30.4603, 214.20015),
    # We don't want to normalize the FireMasks.
    'PrevFireMask': (-1., 1., 0., 1.),
    'FireMask': (-1., 1., 0., 1.)
}

"""Library of common functions used in deep learning neural networks.
"""
def random_crop_input_and_output_images(
    input_img: tf.Tensor,
    output_img: tf.Tensor,
    sample_size: int,
    num_in_channels: int,
    num_out_channels: int,
) -> Tuple[tf.Tensor, tf.Tensor]:
  """Randomly axis-align crop input and output image tensors.

  Args:
    input_img: Tensor with dimensions HWC.
    output_img: Tensor with dimensions HWC.
    sample_size: Side length (square) to crop to.
    num_in_channels: Number of channels in `input_img`.
    num_out_channels: Number of channels in `output_img`.
  Returns:
    input_img: Tensor with dimensions HWC.
    output_img: Tensor with dimensions HWC.
  """
  combined = tf.concat([input_img, output_img], axis=2)
  combined = tf.image.random_crop(
      combined,
      [sample_size, sample_size, num_in_channels + num_out_channels])
  input_img = combined[:, :, 0:num_in_channels]
  output_img = combined[:, :, -num_out_channels:]
  return input_img, output_img


def center_crop_input_and_output_images(
    input_img: tf.Tensor,
    output_img: tf.Tensor,
    sample_size: int,
) -> Tuple[tf.Tensor, tf.Tensor]:
  """Calls `tf.image.central_crop` on input and output image tensors.

  Args:
    input_img: Tensor with dimensions HWC.
    output_img: Tensor with dimensions HWC.
    sample_size: Side length (square) to crop to.
  Returns:
    input_img: Tensor with dimensions HWC.
    output_img: Tensor with dimensions HWC.
  """
  central_fraction = sample_size / input_img.shape[0]
  input_img = tf.image.central_crop(input_img, central_fraction)
  output_img = tf.image.central_crop(output_img, central_fraction)
  return input_img, output_img

"""_parse_fn was modified to include sample_weights in addition to the inputs and labels.

This is a mask with 0's where the data is unknown (label: -1 No Data) and 1's where the data is known (label: 0 No Fire or 1: Fire)

This tells the neural network to ignore the missing data when calculating loss functions and training
"""

"""Dataset reader for Earth Engine data."""

def _get_base_key(key: Text) -> Text:
  """Extracts the base key from the provided key.

  Earth Engine exports TFRecords containing each data variable with its
  corresponding variable name. In the case of time sequences, the name of the
  data variable is of the form 'variable_1', 'variable_2', ..., 'variable_n',
  where 'variable' is the name of the variable, and n the number of elements
  in the time sequence. Extracting the base key ensures that each step of the
  time sequence goes through the same normalization steps.
  The base key obeys the following naming pattern: '([a-zA-Z]+)'
  For instance, for an input key 'variable_1', this function returns 'variable'.
  For an input key 'variable', this function simply returns 'variable'.

  Args:
    key: Input key.

  Returns:
    The corresponding base key.

  Raises:
    ValueError when `key` does not match the expected pattern.
  """
  match = re.match(r'([a-zA-Z]+)', key)
  if match:
    return match.group(1)
  raise ValueError(
      'The provided key does not match the expected pattern: {}'.format(key))


def _clip_and_rescale(inputs: tf.Tensor, key: Text) -> tf.Tensor:
  """Clips and rescales inputs with the stats corresponding to `key`.

  Args:
    inputs: Inputs to clip and rescale.
    key: Key describing the inputs.

  Returns:
    Clipped and rescaled input.

  Raises:
    ValueError if there are no data statistics available for `key`.
  """
  base_key = _get_base_key(key)
  if base_key not in DATA_STATS:
    raise ValueError(
        'No data statistics available for the requested key: {}.'.format(key))
  min_val, max_val, _, _ = DATA_STATS[base_key]
  inputs = tf.clip_by_value(inputs, min_val, max_val)
  return tf.math.divide_no_nan((inputs - min_val), (max_val - min_val))


def _clip_and_normalize(inputs: tf.Tensor, key: Text) -> tf.Tensor:
  """Clips and normalizes inputs with the stats corresponding to `key`.

  Args:
    inputs: Inputs to clip and normalize.
    key: Key describing the inputs.

  Returns:
    Clipped and normalized input.

  Raises:
    ValueError if there are no data statistics available for `key`.
  """
  base_key = _get_base_key(key)
  if base_key not in DATA_STATS:
    raise ValueError(
        'No data statistics available for the requested key: {}.'.format(key))
  min_val, max_val, mean, std = DATA_STATS[base_key]
  inputs = tf.clip_by_value(inputs, min_val, max_val)
  inputs = inputs - mean
  return tf.math.divide_no_nan(inputs, std)

def _get_features_dict(
    sample_size: int,
    features: List[Text],
) -> Dict[Text, tf.io.FixedLenFeature]:
  """Creates a features dictionary for TensorFlow IO.

  Args:
    sample_size: Size of the input tiles (square).
    features: List of feature names.

  Returns:
    A features dictionary for TensorFlow IO.
  """
  sample_shape = [sample_size, sample_size]
  features = set(features)
  columns = [
      tf.io.FixedLenFeature(shape=sample_shape, dtype=tf.float32)
      for _ in features
  ]
  return dict(zip(features, columns))

# Modified

def _parse_fn(
    example_proto: tf.train.Example, data_size: int, sample_size: int,
    num_in_channels: int, clip_and_normalize: bool,
    clip_and_rescale: bool, random_crop: bool, center_crop: bool,
) -> Tuple[tf.Tensor, tf.Tensor, tf.Tensor]:
  """Reads a serialized example.

  Args:
    example_proto: A TensorFlow example protobuf.
    data_size: Size of tiles (square) as read from input files.
    sample_size: Size the tiles (square) when input into the model.
    num_in_channels: Number of input channels.
    clip_and_normalize: True if the data should be clipped and normalized.
    clip_and_rescale: True if the data should be clipped and rescaled.
    random_crop: True if the data should be randomly cropped.
    center_crop: True if the data should be cropped in the center.

  Returns:
    (input_img, output_img) tuple of inputs and outputs to the ML model.
  """
  if (random_crop and center_crop):
    raise ValueError('Cannot have both random_crop and center_crop be True')
  input_features, output_features = INPUT_FEATURES, OUTPUT_FEATURES
  feature_names = input_features + output_features
  features_dict = _get_features_dict(data_size, feature_names)
  features = tf.io.parse_single_example(example_proto, features_dict)

  if clip_and_normalize:
    inputs_list = [
        _clip_and_normalize(features.get(key), key) for key in input_features
    ]
  elif clip_and_rescale:
    inputs_list = [
        _clip_and_rescale(features.get(key), key) for key in input_features
    ]
  else:
    inputs_list = [features.get(key) for key in input_features]

  inputs_stacked = tf.stack(inputs_list, axis=0)
  input_img = tf.transpose(inputs_stacked, [1, 2, 0])

  outputs_list = [features.get(key) for key in output_features]
  assert outputs_list, 'outputs_list should not be empty'
  outputs_stacked = tf.stack(outputs_list, axis=0)

  outputs_stacked_shape = outputs_stacked.get_shape().as_list()
  assert len(outputs_stacked.shape) == 3, ('outputs_stacked should be rank 3'
                                            'but dimensions of outputs_stacked'
                                            f' are {outputs_stacked_shape}')
  output_img = tf.transpose(outputs_stacked, [1, 2, 0])

  if random_crop:
    input_img, output_img = random_crop_input_and_output_images(
        input_img, output_img, sample_size, num_in_channels, 1)
  if center_crop:
    input_img, output_img = center_crop_input_and_output_images(
        input_img, output_img, sample_size)

  weights = tf.cast(tf.greater_equal(output_img, tf.zeros_like(output_img)), tf.int32)

  return input_img, output_img, weights


def get_dataset(file_pattern: Text, data_size: int, sample_size: int,
                batch_size: int, num_in_channels: int, compression_type: Text,
                clip_and_normalize: bool, clip_and_rescale: bool,
                random_crop: bool, center_crop: bool) -> tf.data.Dataset:
  """Gets the dataset from the file pattern.

  Args:
    file_pattern: Input file pattern.
    data_size: Size of tiles (square) as read from input files.
    sample_size: Size the tiles (square) when input into the model.
    batch_size: Batch size.
    num_in_channels: Number of input channels.
    compression_type: Type of compression used for the input files.
    clip_and_normalize: True if the data should be clipped and normalized, False
      otherwise.
    clip_and_rescale: True if the data should be clipped and rescaled, False
      otherwise.
    random_crop: True if the data should be randomly cropped.
    center_crop: True if the data shoulde be cropped in the center.

  Returns:
    A TensorFlow dataset loaded from the input file pattern, with features
    described in the constants, and with the shapes determined from the input
    parameters to this function.
  """
  if (clip_and_normalize and clip_and_rescale):
    raise ValueError('Cannot have both normalize and rescale.')
  dataset = tf.data.Dataset.list_files(file_pattern)
  dataset = dataset.interleave(
      lambda x: tf.data.TFRecordDataset(x, compression_type=compression_type),
      num_parallel_calls=tf.data.experimental.AUTOTUNE)
  dataset = dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
  dataset = dataset.map(
      lambda x: _parse_fn(  # pylint: disable=g-long-lambda
          x, data_size, sample_size, num_in_channels, clip_and_normalize,
          clip_and_rescale, random_crop, center_crop),
      num_parallel_calls=tf.data.experimental.AUTOTUNE)
  dataset = dataset.batch(batch_size)
  dataset = dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
  return dataset

"""Depending on the cutoff, we could report ~100% precision or 100% accuracy, trading one off for the other.

This function returns the precision and recall that maximize the F1-score, for consistency.

For certain cutoffs, the precision is undefined, so it is recorded as 0.
"""

def get_metrics(precs, recs):
  f1s = np.nan_to_num(2*np.nan_to_num(precs)*recs/(np.nan_to_num(precs) + recs))
  return precs[np.argmax(f1s)], recs[np.argmax(f1s)]

"""Define the features in the dataset"""

TITLES = [
  'Elevation',
  'Wind\ndirection',
  'Wind\nvelocity',
  'Min\ntemp',
  'Max\ntemp',
  'Humidity',
  'Precip',
  'Drought',
  'Vegetation',
  'Population\ndensity',
  'Energy\nrelease\ncomponent',
  'Previous\nfire\nmask',
  'Fire\nmask'
]

"""# 3. Load the dataset

Enter the file pattern of the dataset.

If you are running this notebook locally, and your data is not stored in Google Drive, change the file_pattern below to where your data is stored locally.
"""

file_pattern = 'next_day_wildfire_spread_train*'
#Location within MY GDrive. Might not be the same for you. I don't know if you can link to my drive this way...
val_file_pattern = 'next_day_wildfire_spread_eval*'

test_file_pattern = 'next_day_wildfire_spread_test*'

"""Get the training, validation, and testing datasets


We randomly crop the training data, so each epoch of the neural network gets a new set of 15,000 fire images to train off of.

We center crop the images for validation and testing.
"""

one_batch = get_dataset(
      file_pattern,
      data_size=64,
      sample_size=32,
      batch_size=32, #We don't go through the whole dataset at once. It takes 468 loops to do the whole thing.
      num_in_channels=12,
      compression_type=None,
      clip_and_normalize=True,
      clip_and_rescale=False,
      random_crop=True,
      center_crop=False)

dataset = get_dataset(
      file_pattern,
      data_size=64,
      sample_size=32,
      batch_size=14979,
      num_in_channels=12,
      compression_type=None,
      clip_and_normalize=True,
      clip_and_rescale=False,
      random_crop=True,
      center_crop=False)

valset = get_dataset(
      val_file_pattern,
      data_size=64,
      sample_size=32,
      batch_size=1877,
      num_in_channels=12,
      compression_type=None,
      clip_and_normalize=True,
      clip_and_rescale=False,
      random_crop=False,
      center_crop=True)

testset = get_dataset(
      test_file_pattern,
      data_size=64,
      sample_size=32,
      batch_size=1877,
      num_in_channels=12,
      compression_type=None,
      clip_and_normalize=True,
      clip_and_rescale=False,
      random_crop=False,
      center_crop=True)

"""# 4. UNET-Style Convolutional Neural Network

More imports! Fun!
"""

from tensorflow import keras
from tensorflow.keras import layers
from keras.layers import Input, Dense, Reshape, Flatten, Dropout, LeakyReLU
from keras.layers import BatchNormalization, Activation, MaxPooling2D
from keras.layers import UpSampling2D, Conv2D, Conv2DTranspose
from keras.models import Sequential, Model
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping
import os

"""We double the number of filters each layer of the encoder, and halve them for the decoder.
![UNET.png](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA9MAAALlCAYAAADHWbVBAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAHYYAAB2GAV2iE4EAAKiVSURBVHhe7N0HeFNVA8bxt+y995CNILJFEGQvmaIMEQFREXDi3gPBrbg+FMWtOFAUEBmC7C2IyFb2FMreG76c21Oatmlp2rTNbf6/58nDuaMhTdub896zwi54CAAAAAAAJFg6+y8AAAAAAEggwjQAAAAAAH4iTAMAAAAA4CfCNAAAAAAAfiJMAwAAAADgJ8I0AAAAAAB+IkwDAAAAAOAnwjQAAAAAAH4iTAMAAAAA4CfCNAAAAAAAfiJMAwAAAADgJ8I0AAAAAAB+IkwDAAAAAOAnwjQAAAAAAH4iTAMAAAAA4CfCNAAAAAAAfiJMAwAAAADgJ8I0AAAAAAB+IkwDAAAAAOAnwjQAAAAAAH4iTAMAAAAA4CfCNAAAAAAAfiJMAwAAAADgJ8I0AAAAAAB+IkwDAAAAAOAnwjQAAAAAAH4iTAMAAAAA4CfCNAAAAAAAfiJMAwAAAADgJ8I0AAAAAAB+IkwDAAAAAOAnwjQAAAAAAH4iTAMAAAAA4CfCNAAAAAAAfiJMAwAAAADgJ8I0AAAAAAB+IkwDAAAAAOAnwjQAAAAAAH4Ku+Bhy0ig3yZN0gMd29qtCI8N/1i39e1rtxCf7du3a/GiRbqhc2e7BwAAAIF09uxZbd60SSuWL9fqFSv0386dWr96tc6fP6eylSqpeMnLVK1GDVWucoXKli2nDBky2K8MDmm9vkh9OG2gZRop5vjx4/r+m2/UpuoV+nftWrsXAAAAgWJC9OyZM9WlbVt1uKKinureRSNfekHTPv9YWxbN07bFCzXr6y/07cuD9US3G3V9lUrq07275s+b53xtakvr9UXqw2kLYRrJznR+WPzHH+p54416oU9PnT16xB4BAABAoBw+fFjPP/WU+rdsqn9mTLV7L+3PcT/pjibX6tnHH9fBgwft3pSV1uuL1IfTJsI0kt2ePXvUu0FdrZn2m90DAACAQDrkCcH39u2rn99+w+7x39j33lK/Xj21e9cuuyflpPX6IvXhtIkwDQAAALjY6dOn9dILL2jxmB/tnij1unbXx9Nna87OcP197JRWnDij+eH79fX8P9Th3gfsWVFWTJ6g5554QidOnLB7AMSFMA0AAAC42KQJEzR+2Dt2K8rjH36iEV9+pWsbNlSBggWVKVMmZ6KxvHnz6qo6dfTq0KEaOma8PTvK7G++1NdffGG3AMSFMJ2M5s2dq8oZw6I9Dh484Bw7cuSIpv/+uwY/95xuvqGTGteornvu7OtMSLBjxw7nnLiMHzcu1vOeOXPGObZu3Tp9/eUXurdfP7Woe7W6tGurIc8/rzmzZjl3LeMzdcqUWM/7x6JF9mhsM2fMiHW++Z4jRX7/jYsXtnuifDHomWhfF/m+AAAAIOH279+vlx99xG5Fuf/t/+nW229XxowZ7Z7Y0qVLp7bt2+uVUT/ZPVHevv9uhe/ebbeiBEt9kfowggFhOhWYP6rOrVvpnjYt9d0rQ7Ts13EKX7Vc07/41JmQoEXpEhr788/27IQ5deqUhr37rjpeUVEv973NmbFxx9LFWjVlkjNbY78WTdS/z63asnmz/QoAAAC43bw5c3R4y0a7FaF4rTrqfdttCgsLs3vi175jRzXo3tNuRTHLwboJ9WGkNMJ0Cvvhu+/Ut2lDZ1mC+Dx5U2fNnjXLbl3a8P/9T+8/Envci7eFP36v3p2u16aN0S+4AAAAcKcJ48baUpS+9w9U9uzZ7dalma7ft/TpY7eijPvxB2cWaregPoyURphOYW/ff48tXdqrzz2b4PX+PnvuKVuKn2kBf+bRR5w17gAAAOBeR48eddaMjqlm7dq2lHBXVKliS1FMi66ZhdotqA8jpRGmU8nzX4zU7J3hzoyKZnbFAa++aY9E2TR/jt/dUF789gfN271PK0+edf41/09MS38Zo2lTp9it5NPg2mu15swFzdoRe7xNn0EvOsciH3ny5LVHAAAAkBD79u61peiKFStmSwlnJijLW76i3Yqy67//bCl5JEd9kfowUgphOhW8O36Sut9yiwp6LlqmW425eN0zcKDqdu5mz4iy28fED3EZNnGKOnftqnz58il9+vTOv+b/edXHpBIf/+9/CW71BgAAQPA5dOiQLUXJkCOncuTMabcSztQdL69Zy25FOXb0qC25A/VhpCTCdAqr1raDmrVoYbeimFB9fZeudivK0SNHbCl+1/bopabNm9ut6Np17KjLm7a0WxHWzZqunZeYNRwAAADBy0y4FVOpmrUTPPFYTAULF7GlKKYruVtQH0ZKI0ynsObXtXGCsy8FC8eeMj9yiv9Lad/pBmd5A1/M/9flllvsVpStW7faEgAAANzGV2g+f+6cLfnvnI9WWjdNQEZ9GCmNMJ3CCheJfccvUpYsWWwpyvnz520pfiVKlrQl30qVLm1LUQ7s329LieSiiysAAEBa42vGbjPnTmID8B4fwwsT02U8mhSsL1IfRkojTKewbPEsU2DGdSRW1qxZbcm37Dli/79HjyagC3k8F4iEBn0AAAAEXrZs2WwpusM+xlJfiukNuXrRArsVJUFLbAVJfZH6MFIaYTqFxdXF24irW0pCXGryBF/XgPTp434tkc7Hc/FgwgYAAIDUYyax9WVHIsYBm0lvj+3cbreiFImnV2WkYKkvUh9GSiNMp7DETghxKYcPH7Yl344fO2ZLURJyp9HX2JlIJ06csCUAAACkNFOXazvgXrsVZdGC2C3Ml7Js6VJbimIm7CrkY06fmIKlvkh9GCmNMJ1GbFi3zpZ82759my1FyV+ggC1FSOcj6J/0MUtkpP379tkSAAAAUkOTFrFnr/7w1Vd08OABu3VpJ0+e1Fcfj7BbUa6/qVushqBgri9SH0ZKI0ynEd999pnP5REMM5ZjwpixdivKZZddZksRMmbMaEtR4pqUwTzn/Dmz7Vb8fM40yfgSAACAJGvUpKlylSprtyIc3rJRw/83TOcSOLP3qG+/1YrJE+xWlOvatLWlKMFcX6Q+jJRGmE4jtiyap9GjRtmt6GbPnKk/x0VfqL5WxxtizSyeM1cuW4oyadw4n11b5s2Zo7nffm234udrLPiJ48dtCQAAAImVO3duPTTkRbsV5avBz+n9d991Wp3jYsb7fv/NN3q1/x12T5R73nxHRYsVs1tRgrm+SH0YKY0wnYa8eMet+vjDDxW+e7dzJ/LQoUOaMH687modu/vPrXf2izV7uK8JJub/8K2GDxumvXv2OBeRffv2acxPP6lfiyb2jEvLnCmTLUWZ/usvziL5p0+f1sYNG3Qqngs9AAAA4nZD584+x04Pf/xh9e7aRTOmT1d4eLhT7zIBev/+/Vq4YIHu799fL/Tpac+OUrdzN93Wt6/dii7Y64vUh5GSwi64aSX2IPHbpEl6oGP0bi+PDf841kVn3ty56tu0od2KMHzKdDVp2tRuRff3smXqXqem3Yrw+uix6nD99XYrwvhx4/RYl052y3/X9uilYSM+VubMme2eCOZX4fZbemjhj9/bPf77ZMYcNbj2WrsVwTxv6wb1tW3xQrsntt83bVPxEiXsFgAAAPxhAt5ATziO2frqr3INm+ijr76Os14WLPVF6sMIBrRMpxEDXn1TmQsUsltxK1W3gZ5/6eVYFw7DjOV4+Mmn7Nal3f/2/2wpfuZ5b7wl9l1Pb+auIQAAABInf/78Gv7557rp8YTX5WJqfedd+vLH0fEGumCuL1IfRkojTKcRjZo21agZs5wlDOLSuFcffTpqlErEc4G8smpVfTh1ujLkyGn3xGYuUq+O+kk9esZ/QfDWuWtXVWjczG7FFtfEDgAAAEiYnDlz6tkXBuvz2fNVr2t3u/fSqrRqo+G/TdPr77zjhPJLCdb6IvVhpDS6eSdCMHbz/nbRn6pZq5aOHj2qWTNmaMbUqVq2aKHyFCigmlfXVZPmzXV13bo+Zyj0ZdeuXZo1fboWeL6Hv/9YpPyFC6ty1Wqq16CB8zwFCxXS4UOHVLdAHvsVEXx1a4lk7rZNmTxZ036brJWL/1Cx0mVUruLluvqaa9SgYcMErWMIAACASzNjezdt2qQ1q1dr+V9/advWLdq4dq3OnD6tcpWvUPHLSqpajZq6okoVlStfXpl8jOm9lNSsL1IfRjAgTLtQfBcPAAAAIK2jPoxgQDdvAAAAAAD8RJgGAAAAAMBPhGkAAAAAAPxEmAYAAAAAwE+EaQAAAAAA/ESYBgAAAADATyyNBQAAAACAn2iZBgAAAADAT4RpAAAAAAD8RJgGAAAAAMBPhGkAAAAAAPxEmAYAAAAAwE+EaQAAAAAA/ESYBgAAAADATwEL0+fOndNjDz6oyhnDnMePo0bZI5d24sQJNa5R/eLXmsfevXvt0Us7deqUFv+xSB998L7uvLW3WtS9Wk2vqq2+vXrp/ffe04J585xzAsksz/33smUX/0/z/7Vt3Ej33NlXw4cN07w5c+yZ7rJ9+3aN+eknu4Wk+PH77y/+Pj/+0EPO3wgAAGmNv3XADRs26JuvvtK9/fo5dbZOrVo5n5Pjx43T3j177Fkpb+2aNRe/h8jHjdddp5MnT9oz4jfs3Xdjff3RI0fs0eCxetWqWK8zMQ/zfnn7Y9GiWOf8NmmSPRrakpp1Aomff2Dr6AEL03NmzdL4Ye/YLalZixa2dGnma8NXLbdb/vlzyRLd1KGDejeop3cG3qu5336tHUsXa9ffSzXv+5Ea9vBA3d7kWnVt11Yrlifu/4jp7Nmzeu2ll9S9Ts2L/6f5/zbNn6PpX3yq9x68T5+PGGHPdofjx4/r+2++UZuqV+jftWvtXiRFU6+/gV/+97Z+nzLFbgEAkHYktA54+vRpp8GhfaXyevGOWzXt84+dOts/M6Y6n5OPdemkdtfU09TffrNfkfrWTPtN06ZOtVtA4iQl6yDwAllHD0iYPnDggF547FG7Jd3zxtvKnz+/3YrfnvBwvfTE43bLP+Zi2/OaOs5F+FLWzZqubrWrO63USbVwwQJ9+cKzdsu3q+rVs6XgZlrYF//xh3reeKNe6NNTZ48G3x1UtypQoIDuem2o3ZKeu+9e7du3z24BAOB+Ca0DmpafN155xWlwiM/hLRt1f/vr9MvYsXZP6nvlqSd0+NAhuwX4JylZB8kjkHX0gIRp06JpWmYjtbzuOluK35EjR/T8k08m6k7Nls2bnYutv/q1b6P//vvPbiXO33/9ZUtxK1e+vC0Ftz179qh3g7rOnVcEXqs2bWwpooJg/lYAAEgrEloHnD1rlka+OMhuXdrjXW/Qun//tVupa9/a1Ro3dozdAhIuKVkHyStQdfQkh+nw8PBodxnrdu6mChUr2q24mTExjz/wgGZ89Znd458fvv3WlqK06jtAv6z+V38dOaElB49q1JJlqta2gz0awbS8/vzjj3YrcXyN5/l4+mz9feyUVp48q0V7D6r+tdfaIwhlFS+/XHVu6Gq35Aw72Lljh90CAMC9EloHNEPJBnu1Xkf6cOp0LfPU2f7Yd0hPffy53Rvls48+sqXU9/oD92v3rl12K+0xdeg1Zy749ahUubL96ghX160b65zWXoEl1CQ166SkUPz5B6qOnuQw/dukibYUoUuPW5QuXfxPu/TPJepxfcdE/3IdOXxYX73xqt2KULJOPb30xhuqUKGCsmTJouzZs6ta9ep69e2oMTyRvhn+vs6cOWO3/HfS86EQU/UaNZQpUyalT59euXLndv5/wPwtdL2lh92KEExd1wAASKyE1gFXrlgRrfXaePbzr9W4SVNl9tTZcubKpVt691brO++yRyOMfe+toLkBbRpjvhs50m4B8Utq1kHyC1QdPUlh+tChQ3r3uehjh2vXqWNLsW3etEmvDBmiW+rV0bbFC+1e/5kZp2OO7e3Vv79y5Mhht6KUKVtW9bp2t1sRDqz/V4c9gdwf437++eKsb+biHtPV+XJdPP7Cs77HU58/f96ZBG3E8OEacPttzqx+Xdq1dWaRGzN6tNN13R+m+9Oob7/VM48/7sw2Wbd8OV1btYq6dWjv7Bv13XfauGGDPTu6eXPnOq+1cfHCdk+ULwY9c/F7MY+DBw/YI9LUKVOiHTMPM3tfXGbOmBHrfPN/x2S6VnifY94bw/ys//f22873Z763px59xOkq5utmSCDfX3MX3YyvNxOlmOcyM7XXKFpYrepf48wSbyagmzB+fII+5GtfFf1v4v1nntShgwftFgAA7uNPHXC2py4Q07WNGtpSBFOxvbFbN7sVJa7JY82ETt71BvMw+5LTR08+qg3r19utwDET2y776y998tFHuvuOO5wVYkx9w8x2PmL4B1qyeLEzeVuwS+hszsFW5wukQGWdSKnxe55Ybvz5B6KOnqQwvXDBfB3bud1uSfW79VDRokXtVnT79+9Xm4pl9dXg5+yeCLlKldXlTVvarYQxrb6DvvpW9w59V10efly1r++ssuXiHqNcoVL0bgjGBc8PISXt3r1bTz/6qDMJ2tv3361ZX3/hjJ9YNWWSM4vcUzd31XUVyui9t9665DIK5kbA4OeeU8cql2vQrbfop7ded8Y8m/7+ZlzPiskTnH2DevdQu0rlnQuxmZLfbXZ4guot7dvpg8cecr4/872NeWeo+rdoEusmQSDfX/OB1s3z/5pZ4E33NfNcZqb2U3vDnQujmSXe3HB45MaOal66hBO4T8WzbEax4sWd39FI5kZQfDcgAAAIdgmtA5qJTieP+dluRcherISKFytut6KYBpCYli9bZkup486XXrOlCJ9+9KHzPQXK8r//Vp/u3XXz1bU09N4BTkumacU39Q0z2/nb99+jXvWv1q03dXNaO9Oq1KrzBVIgs06oSa2ffyDq6EkK0xPGRG8Kb9W+vS0lTMvb+2nM7Dm6pnFjuydhLitVSjfdfLPuuf9+DXn1VY0cPVoN4hmjvGlD7LuI2X20YieXbVu36rZuXX22aMc0/PGH9fB99zmzY/pi1jp8xvML9N0rQ+yeSzMX4g89gS+QF//kdubUSb086HmfEzaYLv3eE7wF8v01H2rmA23DnJl2z6WZwP36K684d8ni0rZTJ1uK8CtdvQEALpbQOuChQwed5a+81WzSVOkzZLBbUfLmzWtLURakcitcjVq19OB779stORV8c9M9EMb+/LNuuqqG/hz3k90Tt2W/jnNaO828P26qzyVEatX5UkJis04oSe2ff1Lr6IkO02aa96mfRV9LuULFCrYUvyqt2mj4lOl6+/33VaxYMbs3eZg7HWYdaG/t77lfWbNmtVvJ69ixY3riwQecls2Emv3Nl3p36Js+w9nkiRNjve8JMeKpx+Ls8h2MTFd8s2a3L91vu10Z7IdwIN9f041k0OPRly644YGHNfGfDVp29KRWnTqnxQeO6NtFfzq/w96+fXmwlvzxh92KLebfxpRPPtS+VFqsHwCApPCnDrh3T+zPuhKXlbKl6LJmy2ZLUUwr1alTp+xW6ujc7SanNT3S+2+/7XTNToqZ06fryZuiWsQS6uke3YJqHe5ASI06X3JLyazjdqn9809qHT3RYXrTxo22FKVo0bh/WcLCwtT7ucH6at5CfTd2nJo09X1XMpDMnbuRX3xht6K0aR99hu+EuP7GGy/OTNfp/ofs3iiL9x++ePz5IVGtxmas9dJfoi+nYGbMG7dyrZYfP+3MAD5m+Wpd26OXPRph1Gsv688l0bvzmPEyw16LPvFahhw59f6kqc5MmCbsmdA3ed0mtR1wrz0jivc4H9OSb17rrB277Z4ofQa9ePF7MY88eWLfKU5NV3ut4R3I99fcbDAf2t7uffAhp9tZ5syZnfFcZlx+zVq19Mb/hqlB95569IMRzkzuUzZsUc3ate1XxVbUR3e25Bh3BQBAcvOnDmjmIIkpd+7cthSdmcQ1f6Ur7FYUX8+Rksy62U+8EbUmrRnuNW9uwiv0MZmK+uP97rRbUa7rf7dTZzF1OVOHmfTvRvV4KnqXYePhm7tp69YtdiswTIDwHsca3+PH77+3X5X8kqvOlxxSI+sESij//JNaR090mP7nn7W2FCFzgUIqULCg3YrNdN158tlnVefqusqYMaPdm7x+GTPGGdvqzYxZaNAw+qQXycXcQRn28ot2K0KN9tfr5TffdKZjN++DmQHcTC3/5nv/U7mGTexZEcZ7Xr83c+4Pkybruz+Wasg3o5xW01e/+kbNWrRwZsI0Yc+EvlKlS+uu+++3XxUlfHfs4BzsmvW5w7k5YP5I5v63R6/9OMZ574xAv79mrEtMZuZ4X0zA/uTrr3X7nXfqWs/vU8nLLov397pQoUK2FOXff/6xJQAA3MOfOuCpU7HnFDEzeMclT8HYn5e+5iVp2LhxtBv/5mH2JZc27dqpVN0Gdksa+uKLiZ6PZuKvvzrz3HgzDTWvvjnUqbOYupypU5QuU0ZPPfec+r38uj0rghnXOWpk4tbEDWYpWedLDsmRdVL69zw1pdbPP6l19ESH6XVro/8njTp2CtgvTiBMmTxZT/joPjPotdeci1RKMD8I03XB2+0D7vK5bJa5S3vnvVFrNRo/vvlqrFnH8+XLpxo1a6pLt256+Y031a6D71b2gj5+MY4ePWpL7vHM4CHOzQHzu5W/QAF17NTJ+WMxAv3++vq6+26/TePHjdN///1n9ySOec2Ne/WxWxHWrFplSwAAuIc/dcBTp2LPQm1aoOOSxccwvLPnztlS6jF1hEcHDbJbnvdg1nSnrukv08vwo6Fv2K0o9z38sM+bDOa96tu/vzOJlbfPnn/aZyOAm6VknQ/BJ7V+/kmtoyc6TC9dFH2698JBNB7AXNwGdoi9SPgTH33qBNGU4uuuhmnBjEtpH7NY7t61y5YuzVygzZT8Zhr6QU8/ZfdGOeOCZRW8dXvsyThnhzcC/f6WNd25C0S/CWFm03ysSyc1u6yYbul8o7749FNniYrELG1VJMbfyF8x/oYAAHADf+qAKT1WNTk1atxYdW7oarek1556ItryoQlhluwxMxV763jfg/GOqzW9D297MPYQw/Xr1tmS+6V0nQ/BJbV//kmpoycqTJtJF2LOdpzL84ceDEwroq8gffvgl3VL7952K2Vs37rVlqLcUO0Kn+MPzKN7ndhBP74fvBlD9PeyZfrh+++dddWuLlXSmZL/gY5tNfmjD+xZqSwJM07WirH2W0yBfn9z5Myplz/2PQGCYcZpvDagr7NERb2CeZ317+bNmZPgtR9z5Yo+RsxMoOBr7TwAAIKVv3XAyMmDvMUXsI/76EWXIZ6W7JRkWszuf/RRuxUxcdKY0Zeeidubr55uteJYn9vb5ZVjL/P6344dtpR0ZuxpzO7EcT26du9uvypwUrrOh+hC/eeflDp6osK0ryfPkSunLaUes1yAaUWM6Y4hr+iBRx7xeUFPTgcC0P3mhI9xQuYuqFmkvFHly51flud73eysq2bWQY5PWLpEd0SIXzyBOSl3pE0Xj/gkx/trxkQNHTPemdjtUszyGH2bNVKPGzpp5YoVdm/czJ3lmAjTAAA38bcOmCVL7KF1p+OZnftgeOz5XeIbY53SatWurXZ3RXUhff2uO7Vz5067dWnHfNwsyJM3jy3FzdcNi4OJ6CUXrFKjzofgkdo//6TU0RPdMh1TtqyxlzNISaO++85ZLiCm+9/+nxOk4xrLk5wS2mIZn5gfOGb2xm5t2zqLlB/bud3ujdD8tjv17Gdf6ZuFS/T7pm12bxQzQVlyOB9PmE7K0hG+xkF4S47318zE2LZ9e834d4Ne/n60M7nBpZhF4rvWqqY1q6N324opm48lP84HwTgwAAASyt86YPbsOWwpypEjR2wpunOe5445LtLIlkLLmSaEqUvdeffddivCNz5WjolLuvSJq4v5Wlva1FnSitSo8yF4pPbPPyl19ET9Rftq4T19JunfZGKZRe8H9e5ht6KYYNnfc8FL6RbpSHnyxl5SasrGrT67TMT18J5gzPwiPT5woDOON5IZ42uWxlq096CGjRihHr16OXdNfd3BTK4wbT784pLYmS6NyEkH4hLo99ebmZX0hs6d9e3PY5znfO/Xyer17AuxJgDx9laMZcti8vVeZEiFmzwAACSWv3XA3Hlit7rG1T3ZzNgbU+XmrYOqZdq4vFIlZxnRSGYyMF9jOn3J4aPn28EDl25h9rW6iK96kFulZp0PqS+1f/5JqaMnKl1l8vHkJ1JpDcDpv//uc9H7V0f95ATL5AqQCVGiZElbiuLPIuAxLf/7by37dZzdijD064ilsXLFWLPxtI+uCenSJf0OZjofd0FPxnOnZ/++fbbkv/hm+zQC/f76Yu76lvT8Py1bt3aWp5i7Zq0m/rNBz3z6pT0jytxvv473/485aVn2YiVSbGZ5AAACwd86oFmjOebknkvnzNI5H60+Bw7EnszrmiBdBqjXbbfZUoSPh38Qb+NCpEKFC9tSlKWLF9tS3NauWWNLUUqULGFL7hcMdT6kntT++Seljp6opGkWIK99ffQAe+jgIVtKOaZb7T1tWtqtKK94gvT1N95ot1JP+YoVbSnK4kWLbMl/G3zM2liuXDlbim6XjwkuwsJi/7h9dRGKb5yzr+7ycY1jMM8zf85su+W/S3VfCvT7mxDm+zdrTJvJ7G5/4SW7N4qvu+qRDsaoJNRu2jxNddECAKR9/tYBzedmu1632q0Ipiu3r4m4Nm3aZEtRqtWoYUvBxcy+/djwj+2W9Ov772nUJyPsVtzMDfqYNxfMvDfxjbs2rdJfvPO23YpSrnwFW3K/YKzzIeWk9s8/KXX0RDfbVqle3ZYirE9g95ZAMeNtnnzgAbsVxXS7MeuSBYMrqlSxpSjvPfmYNm7YYLeimDu0ZnboV4YM0S9jxzqt0Pv27Ys2RubQodgfVut8BOyTJ0/qi0+iLvCRLlyIHZJ9tdzHd4fZ1wD9SePG+bwba2a6Nq21iXWpX+LkeH/NDZrJEyfq3aFDdcctt8Q5rsvw1erua8xFpPAYswhWqVbNlgAAcA9/64ANmzSxpSjzZke/2W5uwI//+We7FeXKIP6s7NS5s/KWj6rk+xrvHVOWLFnU94nYy5f+z1PvOOVjgiRTf/nko490eMtGuyfCPW+87aynm1akdJ0PwSW1f/5JqaMnOkzH/KYW/TbJefEpZfQPo/TPjKl2K8oXg55RlczpfU6T7v3wZ+bFxMqTJ4/uefMduxXh7NEj6tfjZs2fN89pxTQhdJfnBzjsnXec2aG/GvycHu96g266qoZubN4sWktnwULR72Qazw+8TwsXLHD6+pulssys0o8NHOjcIY3p5InYF+nMPsYoTP/1F+3cscMZo21+Sb0v7kWKFLGlKPN/+FbDhw3T3j17nO/H/MKO+ekn9WsR+8MzkAL5/prf3Tt73qIbq1fRg9e304dPPOJ8X48/8IBWLF+uo55Qbc456Xmft2/fro8//FBj33vL+dpIZu3JuGYjNBO2zB8XvZJQ4fLLbQkAAPfwtw54db16sVbJeOXhB52b7qdOnXJuXH/79dea+OEwezRCp/sfUvHixe1WdHNmzYpVtzP7UlLevHn1+Mvxz5fii6/ek6ZO8cQjDzvduc17YmYS3rxpk14ePFgjnnrMnhXBdEHtfNNNdis0BLpObfw2aVKs36ElCehyn5KC4fc8GCTHzz9SUuvoiQ7TZcuXt6UIZlmmQExbnhCmj/zrA+60W8Ht5ltuUaEq0e9u7Fi6WHc0uVZX5cmhK7NmVNOSRZ3wFtMzr72uHDmiZsGs6uMuibkLeluj+qqVK5tq587uzCo99TPf3Yz274/dkprd8/wl69SzWxH2rV2t5qVLqHr2zGpXqbz2eo1JKFK0qOp1jb2+3PuPPqiGxQo538+1RQroqe5d7JHkFaj314zVGPj4E07Z24yvPlO32tVVJ18uXZklg2p63ueWZUrqrfvusmdEGTBwYJx31vZ7/jbMH723snF00QcAIJj5WwfMly+fnnn/Q7sVwXyNWV6yRo4sutrzGftS3z72SJTb+vezpeDV6rrrVKFxM7uVMKartxmSGNPkjz5w1s4170m1bJnUpmJZffvyYHs0yttfjVRRT30s1ASyTg33Sa6ff1Lr6IkP057/JOZdxm3bYi/HlBxMS6xbmJbKEd+Pcu4i+sPcfTETi3krX6GCz3G6vjTo3lM3P/ms3YqwZP78WF0cTPi78Zaedss37+7l5vyHn4zdPSkuZmmy5BTI97d+gwZ64qNP7ZZ/HnzvA11Tv77dim37tuiLzZu/nVKlStktAADcIzF1wBu6dHFWxUgoEzYrVgz+HlxZs2bVw888Y7cSzgxJfOqTz+1Wwr019lc1DNJJ2ZJbIOt8cJ/k+vkntY6e6DBt1gPrel/0Mcvr/r30WJFAmDV9ui25g1lCYfTM2Wp5+6XvsJpfkNdHj9Fd997rc2a7ex54QN2fiP+ibQL32x98oOatWtk9ETbMmel0346pc9eu8d5VjXm3+cqqVfXh1OmxPki9mck1nBnVe8Yf1AMhUO+vuVHQ+7bbNOL3mSpTv6HdGz/zfb758y+6o1+/eMd7rPs3+tj2Hg89qixBtG4mAAAJlZg6oFn65pEnntBjH8ae08Wb+Zx+e9wEdQqCiWQTqsG1DZ1GDH+YOWt63dpH3yxcrFodb7B741a3czf98OffatOund0TmgJZp/YlvrocUl9y/PyTWkdPdJg2WrRubUsR5qVAH37Tr33K99/aLfcoXaaM3nr/ff24dLke//ATtR1wry5v2tJZt7ha2w7q/dxgvTfhN01dtlwdru8U5w/dTHD1zKBBGrlgse586TVVadXGmfyifrceeuh/wzVm+Wo9+tRTypkzp8+ZvufPnWtLUcxY7K9/+lmDR36vxr36KH+lK1T1unbOWKWXv/tRFXzMoNe4SVNNXfOvBn35jVrfeZeKVK/lvJYuDz/uhMupf69wxgSl1EUpUO+veb3mju/Pv03R1/P/cGbqbH/P/c7NBvNHabrEm/f6rteG6oPJv2v22n+ddesudZGe9fvvthShafPmtgQAgPskpg5oAvVtd/TVb+s36/kvRqpV3wEqXquOyjVs4nzWvvrDz5q0ZKmua9vWfoU7mLW3733oIbvln1q1r9JXo35wgrK50dD8tjudOpV5X5r2vl0Pvve+E7g//nqkz+F+oShQdT5fLrXeMVJfoH/+Sa2jh11IwtR2ZiB34ysq6djO7XaPNHfXXmdNQQARzLqZ9Qvls1tybn5M9VQWzJ19AADciDog0gozaZUZa2v8suofn41ISJsCUUdPUsu0+Y/uHxR9YoQ1q1bZEgBj5fLlthThniefJkgDAFyNOiDSil1ea54XKFjQlhAKAlFHT1KYNlq3aWNLEaZMmmRLAIypkyfbUoQWMcayAwDgRtQB4XZm+OhPo0Y5ZTNs0Sx3htARiDp6ksN04SJFnPEckX5881X953WHBwhl5m6n+ZuI9PCwD52/GQAA3I46INzM/K6++eqrGj30NWe73z33OP8iNASqjp7kMG107naTMzlTpBkxBnIDoWr6tGm2FDGr4A2dO9stAADcjzog3Gr82DH68oVnndVphk+ZriuqVLFHEAoCVUdP0gRk3saPG6fHunRyymbw9pTFf7I4OkLa0aNH1apObR1YH7FcyBs/jVP7jh2dMgAAaQV1QLiRaZn+4pNP1KNXL5UqXdruRSgIZB09IC3ThlnGwCyrZJgXNnvmTKcMhCrzNxD5R3ptj16xxpYBAJAWUAeEGxUtWlRPPvssQToEBbKOHrCWaQAAAAAAQkXAWqYBAAAAAAgVhGkAAAAAAPxEmAYAAAAAwE+EaQAAAAAA/ESYBgAAAADAT4RpAAAAAAD8RJgGAAAAAMBPhGkAAAAAAPxEmAYAAAAAwE+EaQAAAAAA/ESYBgAAAADAT4RpAAAAAAD8RJgGAAAAAMBPYRc8bBkAkuy/nTs19bffNGPqFP3z11JVrF5DTVu11nVt26pwkSL2rOj27d2r36dM0XTPY8WiBSpUspSuadxYzVu1Uu2rrlJYWJg9EwCSF9cwAEBCEaYBBMySxYvVt2N7ndobbvdEyVWqrD7+6WdVq17d7omwetUq9eveTfvWrrZ7ouv38uu678EHlSFDBrsHAJIH1zAAgD8I0wAC4sCBA2pZo5qO7dxu98SWt3xFTVywSHny5HG2Dx86pA6NGyl81XJnOy5v/DRO7Tt2tFsAEHhcwwAA/mLMNICAmD937sVKaKu+AzRj606tOHFGv6z+V4WqVHP2H1j/r1auWOGUjTmzZ1+shBapXks/LVup5cdPa/aO3er80GPOfmPEe+/q/PnzdgsAAo9rGADAX4RpAAGRM1cu9X3xVdXr2l133X+/ihQt6nRrrFChguo1a27Pks6dO2tL0rzZs2xJeuDpZ3RFlSrKmDGjChYqpNv69bNHpHWzpuv4sWN2CwACj2sYAMBfdPMGkCzMpeXkyZP6c8kS3dWxnc4ePaIMOXJq2tp1KlS4sHPOZx9/rM0bN2rd2jV69sWXnIpoJDMJULNSxe2WtOzoSWXOnNluAUDy4hoGALgUwjSAZDFh/Hg9cmPUGMHMBQrpw5/GqF79+nZP/KZNnap727Zyyh3ufUCvv/22UwaAlMA1DABwKXTzBpAswsN321KEFz74UFddfbXdil/47t167fnn7JbU9eabbQkAUgbXMADApRCmASSL/3bstKUIT3S7UY8/+KAz+218wsPDNXBAf21bvNDZ7vn08846rQCQkriGAQAuhTANIFncdd99zqy207fuVLu77nP2TfxwmEYMH+6Ufdm2bZv69eypZb+Oc7YbdO+p+x96SOnScakCkLK4hgEALoUx0wCS3ZbNm3VdhTJ2S5ofvl958+a1WxHW/fuv+vW4Wbv+XupsN+7VR6++9Zby5Il+HgCkNK5hAABfuFUKIMnOnTunUd99pzdeflk9u3TR7l277JEI+QsUsKUIBw8csKUIa9esUc+2bS5WQtvfc7/eePc9KqEAUgTXMABAYhCmASRZ+vTpNWncWH32/NP6c9xPWrlihT0S4b///rOlCFmzZbMlafOmTbr9xk46vGWjs931kSc0+JVXlTNnTmcbAJIb1zAAQGIQpgEERKduN9mSnFls16xerTNnzmjb1q16+9VX7RGp9vWdVdiu0Xr0yBE9cu89OrD+X2e7XtfueuLZZ5U1a1ZnGwBSCtcwAIC/GDMNICCOeCqVN1/fURvmzLR7fPt20Z+qWauWU/7x++/1XK+ELRmzYM9+ukwCSDZcwwAA/qJlGkBAmC6N//vkU5Wq28DuiW3YxCkXK6GnTp7U2y8875QBILVxDQMA+IuWaQABdeDAAU2ZNElTJkzQmqVLVOaKKmraqrVat2mjkpddZs+SNqxfr/aVK9itS6NVB0BK4BoGAEgowjSQAoYPH64+ffq4ahydG18zABhcc2H89ddfKlq0qAoUKKAMGTLYvQAQOIRpOFauXKkyZcooe/bsdg8CKSwszPl35syZaty4sVMOdm58zQBgcM2FMWvWLOffdOnSqVChQipSpIhy587t7AOAQGDMNBz79u3TkiVL9M8//+jUqVN2LwKpUaNGatKkifr166ctW7bYvcHNja8ZAAyuuYh0/vx57dq1S8uWLdPChQu1bds26joAAoKWaTgi795GKlGihC677DJlzJjR7kFSmBaHadOn6+DBg+p8443Ovi+++EK9evVy7pgHIze+ZgAwuObCiFm3iSlfvnxON3DzL+8xgMTgygGftm/f7ty93bp1q86dO2f3IqkaN2miLdu26ZVXX3XGxqVPn16LFi2yR4OTG18zABhccxGf/fv3a9WqVVqwYIE2bNigY8eO2SMAkDCEacTJdIvatGmT8yG+c+dO0YkhMMy49Dv79dOixYvVpm1b1atXT4888oh2795tzwg+bnzNAGBwzcWlnD171mlEMMPdzMPUecw+ALgUunnDcamuUEbmzJlVtmxZZxIP+Cey+171GjXsnigzZ8xQl86dnfIPP/ygrl27OuXU5sbXDAAG11wYCanbxKdgwYJON/C8eVnSDIBvtEwjwcxkHWvWrNHixYuddTgRGE2aNtXW7dv10ssvq1u3bk6F6u+//7ZHg5MbXzMAGFxzkVB79uzR8uXLNX/+fG3evJlJywDEQpiG344fP+58uJj1G48cOWL3IimyZcum/gMGOF36mjVvrho1amjw4ME6dOiQPSP4uPE1A4DBNRf+OHPmjDO7uplLxtR9wsPDnaFwAEA3bziS0hUqf/78KleunLJmzWr3IKb4uu/5MmPGDHW1XfrGjx+v9u3bO+WU5MbXDAAG11wYSe3mHR8z+3fhwoVVrFgx5ciRw+4FEGpomUaSmTWq//jjD61du5YuUAHS1HbpG/Lii+rQoYNq167trAEezNz4mgHA4JoLf5mW6f/++09//vmn02JtJjBj0jIg9BCmETBmllHzgWKWl+ADJelMl7677r7b6dKXOUsWVapUSW+99ZZOnjxpzwg+bnzNAGBwzUVimYYEU/eZN2+eVqxY4Sy5BSA0EKYRcOburFmz0axRzZiipDNd6Mf/+qt+GD1aDz/8sNOdfvr06fZocHLjawYAg2suksIEaROoTbDeuHEjNzaANI4wjWQRuUa1CdWmGxRD85OuWbNm2rZjhwYNHqzmzZurY8eOzg2LYObG1wwABtdcJIXpobdt2zYtWrTIWbva9N6jgQFIewjTSFbmw+Tff/91PkzMEhNIGtPacO+9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)
"""

def conv_block(prev_output, filters, kernel):
    x = Conv2D(filters, kernel, padding = "same")(prev_output)
    x = layers.BatchNormalization()(x)
    x = LeakyReLU(0.1)(x)
    x = Conv2D(filters, kernel, padding = "same")(x)
    x = layers.BatchNormalization()(x)
    return LeakyReLU(0.1)(x)

def up_conv_block(prev_output, filters, kernel):
    x = Conv2D(filters, kernel, padding = "same")(prev_output)
    x = layers.BatchNormalization()(x)
    x = LeakyReLU(0.1)(x)
    x = Conv2D(filters//2, kernel, padding = "same")(x)
    x = layers.BatchNormalization()(x)
    return LeakyReLU(0.1)(x)

sample_size = dataset.element_spec[0].shape[1]

# Create UNET style model - This first one is the same as the paper
model_input = keras.Input(shape=(sample_size, sample_size, 12), name="original_img") # input is 32*32

#Downsample
block_1_output = conv_block(model_input, 32, 3)
x = MaxPooling2D(2)(block_1_output) #output is 16 * 16
block_2_output = conv_block(x, 64, 3)
x = MaxPooling2D(2)(block_2_output) #output is 8*8
block_3_output = conv_block(x, 128, 3)
x = MaxPooling2D(2)(block_3_output) #output is 4*4

#bottom layer bottleneck
x = conv_block(x, 256, 3) # still 4x4

#upsample
# x = UpSampling2D()(x) #Optional, but you have to change stride = 1 below
x = Conv2DTranspose(128, 3, strides = 2, padding = "same")(x) # output is 8*8
x = layers.BatchNormalization()(x)
first_up_layer = layers.add([block_3_output, x])
x = up_conv_block(first_up_layer, 256, 3)
# x = UpSampling2D()(x) #Optional, but you have to change stride = 1 below
x = Conv2DTranspose(64, 3, strides = 2, padding = "same")(x) # output is 16*16
x = layers.BatchNormalization()(x)
second_up_layer = layers.add([block_2_output, x])
x = up_conv_block(second_up_layer, 128, 3)
# x = UpSampling2D()(x) #Optional, but you have to change stride = 1 below
x = Conv2DTranspose(32, 3, strides = 2, padding = "same")(x) # output is 32*32
x = layers.BatchNormalization()(x)
# Eliminating the skip connection from the input results in increased performance.
# This is reflected by a red X in the diagram above
# x = layers.add([block_1_output, x]) # Third_up_layer
x = up_conv_block(x, 64, 3)

predictions = Conv2D(1, 3, activation = "sigmoid", padding="same")(x) #Force output to be 0,1

# this is the model we will train
model = Model(inputs=model_input, outputs=predictions)

model.summary() # It's not as deep as Inception, but it'll do



# compile the model
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001), loss='binary_crossentropy', metrics = [tf.keras.metrics.AUC()])
# optimizer changed to adam from rmsprop because it's spoopier

# Save the best model.
checkpoint = ModelCheckpoint('best_default_model.keras', monitor='val_loss', save_best_only=True, save_freq=1)

# stop training if it's overfitting # may need to increase regularization
early = EarlyStopping(monitor='val_loss', min_delta=0, patience=5, verbose=1, mode='auto')
CALLBACKS=[checkpoint,early]

#Uncomment and turn sideways to see the beautiful U-shaped architecture.
keras.utils.plot_model(model, "UNet.png", show_shapes=True)

"""This randomly crops new 32*32 squares from the data and runs 1 epoch. Then it does it again.

We could have done model.fit with (inputs, labels) representing inputs and outputs to fit, but it would pick the SAME 15,000 inputs and outputs instead of taking advantage of the random cropping.

It shows a lot more data to the model, improving performance

Sometimes this doesn't run. This is a known bug. To fix, restart kernel and run fresh.

Alternatively, you can just use the same 15,000 fires over and over again without random cropping running the code chunk below
"""

# train the model on the new data for a few epochs
print("Model has started training")
EPOCHS = 25


history = model.fit(one_batch, #tf.data.dataset takes full advantage of the data generator above
          epochs = EPOCHS,
          validation_data = valset,
          callbacks = CALLBACKS)

# If the above code doesn't run, get a batch of inputs and labels, then run the below code:
# inputs, labels, weights = next(iter(dataset))
# history = model.fit(inputs, labels,
#                     sample_weight = sample_weight,
#                     epochs = EPOCHS,
#                     batch_size = 64,
#                     validation_data = (inputs_val, labels_val))

"""I like to save the model only after I made an archtecture change, or if it's SOTA on the validatoin set."""

model.save("predictions.keras")

history_dict = history.history
print(history_dict.keys())

"""Display AUC and losses. This quickly has limiting returns, which is why EarlyStopping is so helpful."""

length = len(history_dict['loss'])+1

plt.figure(figsize = (14,6))

plt.scatter(range(1,length), history_dict['auc'], label = "Training AUC")
plt.scatter(range(1,length), history_dict['val_auc'], marker='v', label = "Validation Set AUC")

plt.xlabel("Epoch", fontsize=18)
plt.ylabel("Area Under Curve (PR)", fontsize=18)

plt.xticks(fontsize=16)
plt.yticks(fontsize=16)

plt.legend(fontsize=18)

plt.show()


plt.figure(figsize = (14,6))

plt.scatter(range(1,length), history_dict['loss'], label = "Training Loss")
plt.scatter(range(1,length), history_dict['val_loss'], marker='v', label = "Validation Set Loss")

plt.xlabel("Epoch", fontsize=18)
plt.ylabel("Loss Function Value", fontsize=18)

plt.xticks(fontsize=16)
plt.yticks(fontsize=16)

plt.legend(fontsize=18)

plt.show()

"""# 5. Metrics: Precision, Recall, AUC (PR)

This section of code takes the predictions and labels, and returns a bunch of metrics.

In order to run it, you have to specifiy whether you want the metrics for the training data, validation data, or test data.

To start, import the confusion matrix so we can get the actual fires and predicted fires
"""

## now we can import the confusion matrix
from sklearn.metrics import confusion_matrix

"""TF Datasets are loaded lazily, so materialize the first batch of inputs (11 environmental features) and labels (fire mask).


"""

inputs, labels, weights = next(iter(dataset))

inputs_val, labels_val, _ = next(iter(valset))

inputs_test, labels_test, _ = next(iter(testset))

"""Reshape the data in the next two cells for predictions and to remove "no data" files"""

X = inputs
y = tf.reshape(labels, [-1]).numpy() #len(labels)*32*32

y_val = tf.reshape(labels_val, [-1]).numpy()

y_test = tf.reshape(labels_test, [-1]).numpy()

#Leave these commented if you want the training accuracy
#Uncomment one or the other if you want the val/test data
# X, y = inputs_val, y_val
X, y = inputs_test, y_test

#Don't bother learning where no-data is during training.
#makes training quicker and binary (thank fuck)
y_pred = model.predict(X).reshape(-1)
y_pred = y_pred[np.where(y >= 0)]
y = y[np.where(y >= 0)]

"""Get the actual fire and predicted fire values"""

## just like mse, actual then prediction
cum = confusion_matrix(y, np.round(y_pred))
cum

"""Get the True Negative (TN), False Positive (FP), False Negative (FN), and True Positive (TP)


"""

## Calculate the confusion matrix here

TN = cum[0,0]
FP = cum[0,1]
FN = cum[1,0]
TP = cum[1,1]

"""Get the baseline precision and recall


The baseline precision is with a cutoff of 0.5 (>0.5 means fire and <0.5 means no fire).

This isn't always ideal, as the model regularly predictions regions are on fire with, say 30% confidence.
"""

## calculate recall and precision here
print("The baseline precision is",
         np.round(TP/(FP + TP), 4))

print("The baseline recall is",
         np.round(TP/(FN + TP), 4))

"""So we sweep through all the cutoffs to see which combination of precision/recall is best."""

## Now plot how the accuracy (sensitivity/specificity) changes with the cutoff
cutoffs = np.arange(0.001,.975,.001)
precs = []
recs = []
y = y.astype(int)

for cutoff in cutoffs:
    TP = (1*(y_pred >= cutoff) & y).sum()
    PP = 1*(y_pred >= cutoff).sum() #predicted positives = # Denominator for precision
    AP = y.sum() #Actual positives # Denominator for recall
    precs.append(TP/PP)
    recs.append(TP/AP)

prec, rec = get_metrics(precs, recs)

auc = tf.keras.metrics.AUC(curve = 'PR')
auc.update_state(y, y_pred)

print("The best precision is", prec)
print("The best recall is", rec)
print("The auc is", auc.result().numpy())

"""# 6. Plot of Precision/Recall curves

Nothing fancy. Just seeing how they each change as the cutoff changes.
"""

plt.figure(figsize=(12,8))

plt.scatter(cutoffs,precs)

plt.xlabel("Cutoff",fontsize=16)
plt.ylabel("Training Precision",fontsize=16)

plt.show()

plt.figure(figsize=(12,8))

plt.scatter(cutoffs,recs)

plt.xlabel("Cutoff",fontsize=16)
plt.ylabel("Training Recall",fontsize=16)

plt.show()

plt.figure(figsize=(10,8))

plt.plot(recs, precs)

plt.xlabel("Recall", fontsize=16)
plt.ylabel("Precision", fontsize=16)

plt.xticks(fontsize=14)
plt.yticks(fontsize=14)

plt.show()

"""Remember, we report precision and recall that maximize the F1-score, which usually involves a relatively low threshold for fire."""

plt.figure(figsize=(12,8))

f1s = np.nan_to_num(2*np.nan_to_num(precs)*recs/(np.nan_to_num(precs) + recs))
plt.scatter(cutoffs,f1s)

plt.xlabel("Cutoff",fontsize=16)
plt.ylabel("F1-Score",fontsize=16)

plt.show()

"""# 7. Plotting function

Visualize the predicions on a few new inputs
"""

n_rows = 10
n_features = inputs.shape[3]
CMAP = colors.ListedColormap(['black', 'silver', 'orangered'])
BOUNDS = [-1, -0.1, 0.001, 1]
NORM = colors.BoundaryNorm(BOUNDS, CMAP.N)
keys = INPUT_FEATURES

pred = model.predict(inputs_test).reshape((len(inputs_test),32,32))
plt.imshow(pred[0], cmap='plasma')

"""Plot the Last fire, Actual fire, and Predicted fire for comparison to see how well this model did in predicting fire.

Note that for inputs with no fire (presumably, it was cropped out), it generally predicts there will be no fire (<2% chance).

For all other inputs, it generally predicts a larger bubble around the fire, accounting for wind/terrain.
"""

fig = plt.figure(figsize=(9,20))
n_rows = 8

for i in range(n_rows):
  fire_index = i +1000
  plt.subplot(n_rows,3, 3*i + 1)
  plt.title("Last fire", fontsize=13)
  plt.imshow(inputs_test[fire_index, :, :, -1], cmap=CMAP, norm=NORM)
  plt.axis('off')
  plt.subplot(n_rows,3, 3*i + 2)
  plt.title("Actual fire", fontsize=13)
  plt.imshow(labels_test[fire_index, :, :, 0], cmap=CMAP, norm=NORM)
  plt.axis('off')
  plt.subplot(n_rows,3, 3*i + 3)
  plt.title("Prediction", fontsize=13)
  plt.imshow(pred[fire_index], cmap='plasma')
  plt.colorbar()
  plt.axis('off')
plt.tight_layout()