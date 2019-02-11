import numpy as np
import numpy.ma as ma

# A dictionary for values to use in masking the QA band
pixel_flags = {
    "pixel_qa": {
        "L47": {
            "Fill": [1],
            "Clear": [66, 130],
            "Water": [68, 132],
            "Cloud Shadow": [72, 136],
            "Snow": [80, 112, 144, 176],
            "Cloud": [96, 112, 160, 176, 224],
            "Low Cloud Confidence": [66, 68, 72, 80, 96, 112],
            "Medium Cloud Confidence": [130, 132, 136, 144, 160, 176],
            "High Cloud Confidence": [224],
        },
        "L8": {
            "Fill": [1],
            "Clear": [322, 386, 834, 898, 1346],
            "Water": [324, 388, 836, 900, 1348],
            "Cloud Shadow": [328, 392, 840, 904, 1350],
            "Snow": [336, 368, 400, 432, 848, 880, 912, 944, 1352],
            "Cloud": [352, 368, 416, 432, 480, 864, 880, 928, 944, 992],
            "Low Cloud Confidence": [
                322,
                324,
                328,
                336,
                352,
                368,
                834,
                836,
                840,
                848,
                864,
                880,
            ],
            "Medium Cloud Confidence": [
                386,
                388,
                392,
                400,
                416,
                432,
                900,
                904,
                928,
                944,
            ],
            "High Cloud Confidence": [480, 992],
            "Low Cirrus Confidence": [
                322,
                324,
                328,
                336,
                352,
                368,
                386,
                388,
                392,
                400,
                416,
                432,
                480,
            ],
            "Medium Cirrus Confidence": [],
            "High Cirrus Confidence": [
                834,
                836,
                840,
                848,
                864,
                880,
                898,
                900,
                904,
                912,
                928,
                944,
                992,
            ],
            "Terrain Occlusion": [1346, 1348, 1350, 1352],
        },
    }
}


def _create_mask(mask_arr, vals):
    """Take an input single band mask layer such as a pixel_qa
    layer for MODIS or Landsat and apply a mask given a range of values to mask.

    Parameters
    -----------
    mask_arr : numpy array
        An array of the pixel_qa or mask raster of interest.

    vals : list of numbers either int or float
        A list of values from the pixel qa layer that will be used to create
        the mask for the final return array.

    Returns
    -----------
    arr : numpy array
        A numpy array populated with 1's where the mask is applied (a Boolean True)
        and a 0 where no masking will be done.
    """

    # Make sure vals is a list
    try:
        vals.sort()
    except AttributeError:
        raise AttributeError("Values should be provided as a list")

    try:
        mask_arr.ndim
        temp_mask = np.isin(mask_arr, vals)
    except AttributeError:
        raise AttributeError("Input arr should be a numpy array")

    # Mask the values
    mask_arr[temp_mask] = 1
    mask_arr[~temp_mask] = 0

    return mask_arr


def _apply_mask(arr, input_mask):
    """Applies a single dimension mask to the provided array.

    Parameters
    -----------
    arr : numpy array
        The original numpy array that needs a mask applied.

    input_mask : numpy array
        A numpy array containing O's and 1's where the 1's indicate where the
        mask is applied.

    Returns
    -----------
    numpy array
        The original numpy array with the mask applied to cover up issue pixels.
    """

    # Test if input_mask is numpy array w values == 1 for masked
    if not np.any(input_mask == 1):
        raise ValueError("Mask requires values of 1 (True) to be applied.")

    try:
        # Create a mask for all bands in the landsat scene
        cover_mask = np.broadcast_to(input_mask == 1, arr.shape)
    except AttributeError:
        raise AttributeError("Input arr should be a numpy array")

    # If the user provides a masked array, combine masks
    if isinstance(arr, np.ma.MaskedArray):
        cover_mask = np.logical_or(arr.mask, cover_mask)

    # Return combined mask
    return ma.masked_array(arr, mask=cover_mask)


def mask_pixels(arr, mask_arr, vals=None):
    """Take an input array to be masked, single band mask layer such as a
    pixel_qa layer for MODIS or Landsat, and apply a mask given a range of
    values to mask. This function can also be passed a previously created
    mask in place of a qa layer and a list of values.

    Parameters
    -----------
    arr : numpy array
        The desired array to mask.
    mask_arr : numpy array
        An array of either the pixel_qa or mask of interest.
    vals : list of numbers either int or float (optional)
        A list of values from the pixel qa layer that will be used to create
        the mask for the final return array. If vals are not passed in,
        it is assumed the mask_arr given is the mask of interest.

    Returns
    -------
    arr : numpy array
        A numpy array populated with 1's where the mask is applied (a Boolean True)
        and the original numpy array's value where no masking was done.

    Example
    -------
    >>> import numpy as np
    >>> from earthpy.mask import mask_pixels
    >>> im = np.arange(9).reshape((3, 3))
    >>> im
    array([[0, 1, 2],
           [3, 4, 5],
           [6, 7, 8]])
    >>> im_mask = np.array([1, 1, 1, 0, 0, 0, 1, 1, 1]).reshape(3, 3)
    >>> im_mask
    array([[1, 1, 1],
           [0, 0, 0],
           [1, 1, 1]])
    >>> mask_pixels(im, mask_arr=im_mask, vals=[1])
    masked_array(
      data=[[--, --, --],
            [3, 4, 5],
            [--, --, --]],
      mask=[[ True,  True,  True],
            [False, False, False],
            [ True,  True,  True]],
      fill_value=999999)
    """
    if vals:
        mask_vals = np.unique(mask_arr)
        if vals not in mask_vals:
            raise ValueError("Values to mask are not in provided mask layer.")
        else:
            cover_mask = _create_mask(mask_arr, vals)
    else:
        # Check to make sure the mask_arr is a mask raster and not a pixel_qa layer
        if np.array_equal(mask_arr, mask_arr.astype(bool)):
            raise AttributeError(
                "Please provide either a masked array or a Pixel QA layer with values to mask."
            )
        else:
            cover_mask = mask_arr
    return _apply_mask(arr, cover_mask)