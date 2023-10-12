import cv2
import numpy

from skimage.morphology import disk, white_tophat
from scipy.ndimage.filters import maximum_filter

def get_legend_mask(w, h, mask_rects):
    """
    mask_rects are array of ( rmin rmax cmin cmax )
        rmin or rmax and cmin or cmax can be None 
        i.e. (1000 None 0 140) or (1000 None None 140) are valid

    if w == 1024:
        mask[1000:, 0:140] = 1
        mask[980:, 900:] = 1
    elif w == 2048:
        mask[2000:, 0:280] = 1
        mask[1960:, 1800:] = 1
    """

    mask = numpy.zeros((w, h), dtype=bool)

    if mask_rects is not None:
        for mask_rect in mask_rects:
            rmin, rmax, cmin, cmax = mask_rect

            if rmin is None:
                rmin = 0
            if cmin is None:
                cmin = 0
            
            if rmax is None and cmax is None:
                mask[rmin:, cmin:] = 1
            elif rmax is None:
                mask[rmin:, cmin:cmax] = 1
            elif cmax is None:
                mask[rmin:rmax, cmin:] = 1
            else:
                mask[rmin:rmax, cmin:cmax] = 1

    return mask


def remove_legend(image, legend_mask):
    """
    Remove the legends from the raw images

    This filters out both the bottom left and bottom right corners.
    """

    if len(image.shape) == 3:
        blank_value = (0, 0, 0)
        w, h, d = image.shape
    elif len(image.shape) == 2:
        blank_value = 0
        w, h = image.shape
    else:
        e_message = ("Expected image shape 2 or 3, got: %s" % str(image.shape))
        raise Exception(e_message)

    image[legend_mask == 1] = blank_value

    return image


def convert_intensity(image, image_filter_type=None):
    """
    Convert color images to intensity values

    """

    image_working = image.copy()
    
    if image_filter_type == 100:
        image_working[:, :, 1] = 0
        image_working[:, :, 2] = 0
    elif image_filter_type == 10:
        image_working[:, :, 0] = 0
        image_working[:, :, 2] = 0
    elif image_filter_type == 1:
        image_working[:, :, 0] = 0
        image_working[:, :, 1] = 0
    
    image_intensity = cv2.cvtColor(image_working, cv2.COLOR_RGB2GRAY)
    
    return image_intensity

def generate_cost_image_perimeter(image):
    image_working = image.copy()
    
    image_intensity = cv2.cvtColor(image_working, cv2.COLOR_RGB2GRAY)

    cost_image = image_intensity.copy()
    cost_image = (numpy.max(cost_image) - cost_image)
    
    return cost_image

def generate_cost_image(image):
    """
    Convert an image to be used for A* route finding
    Generate an image where each pixel is a cost rather than an intensity. Since
    the path finding algorithms are designed to ascend gradients/follow high
    intensity paths, we need to invert the image before using it.
    """
    disk_size = 5
    original_scale = 10.0

    cost_image = image.copy()

    selem = disk(disk_size)
    image_processed = white_tophat(image, selem)

    # Cutoff anything over the max of the top-hatted image
    cost_image[cost_image > numpy.max(image_processed)] = numpy.max(image_processed)

    # Create a cost image scaled to 10% of the processed image
    cost_image = (cost_image / numpy.max(image_processed)) * (numpy.max(image_processed)/original_scale)

    # Add the cost image and the processed image together
    cost_image = cost_image + image_processed

    # Invert
    cost_image = (numpy.max(cost_image) - cost_image)

    return cost_image

def filter_image(input_image, mask_rects=None, image_filter_type=None):
    w, h, d = input_image.shape

    _lenged_mask = get_legend_mask(w, h, mask_rects)

    image_original = remove_legend(input_image, _lenged_mask)

    image_intensity = convert_intensity(image_original, image_filter_type)

    image_cost = generate_cost_image(image_intensity)

    return (image_intensity, image_cost)

def load_image(input_image_path, image_color_map="BGR"):
    """
    Return original image mapped to RGB
    """

    input_image = cv2.imread(input_image_path)

    if image_color_map == "BGR":
        input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)

    return input_image