"""
Module related to Grad-CAM++ method
"""

import tensorflow as tf

from .grad_cam import GradCAM


class GradCAMPP(GradCAM):
    """
    Used to compute the Grad-CAM++ visualization method.

    Only for Convolutional Networks.

    Ref. Chattopadhyay & al., Grad-CAM++: Improved Visual Explanations for Deep Convolutional
    Networks (2017).
    https://arxiv.org/abs/1710.11063

    Parameters
    ----------
    model : tf.keras.Model
        Model used for computing explanations.
    output_layer_index : int, optional
        Index of the output layer, default to the last layer, it is recommended to use the layer
        before Softmax (often '-2').
    batch_size : int, optional
        Number of samples to explain at once, if None compute all at once.
    conv_layer : int or string or None
        Layer to target for Grad-CAM++ algorithm, if int, will be be interpreted as layer index,
        if string will look for the layer name.
    """

    # Avoid zero division during procedure. (the value is not important, as if the denominator is
    # zero, then the nominator will also be zero).
    EPSILON = tf.constant(1e-4)

    @staticmethod
    @tf.function
    def _compute_weights(feature_maps_gradients, feature_maps):
        """
        Compute the weights according to Grad-CAM++ procedure.

        Parameters
        ----------
        feature_maps_gradients : tf.Tensor (N, CW, CH, Filters)
            Gradients for the target convolution layer.
        feature_maps : tf.Tensor (N, CW, CH, Filters)
            Activations for the target convolution layer.

        Returns
        -------
        weights : tf.Tensor (N, 1, 1, Filters)
            Weights for each feature maps.
        """
        feature_maps_gradients_square = tf.pow(feature_maps_gradients, 2)
        feature_maps_gradients_cube = tf.pow(feature_maps_gradients, 3)

        feature_map_avg = tf.reduce_mean(feature_maps, axis=(1, 2), keepdims=True)

        nominator = feature_maps_gradients_square
        denominator = 2.0 * feature_maps_gradients_square + \
                      feature_maps_gradients_cube * feature_map_avg
        denominator += tf.cast(denominator == 0, tf.float32) * GradCAMPP.EPSILON

        feature_map_alphas = nominator / denominator * tf.nn.relu(feature_maps_gradients)
        weights = tf.reduce_mean(feature_map_alphas, axis=(1, 2))
        weights = tf.reshape(weights,
                             (weights.shape[0], 1, 1,
                              weights.shape[-1]))

        return weights