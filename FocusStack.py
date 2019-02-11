"""

Simple Focus Stacker

    Re-Author : Thongvan Alexis (thongvan.alexis@gmail.com)

    Author:     Charles McGuinness (charles@mcguinness.us)
    Copyright:  Copyright 2015 Charles McGuinness
    License:    Apache License 2.0


This code will take a series of images and merge them so that each
pixel is taken from the image with the sharpest focus at that location.

The logic is roughly the following:

1.  Align the images.  Changing the focus on a lens, even
    if the camera remains fixed, causes a mild zooming on the images.
    We need to correct the images so they line up perfectly on top
    of each other.

2.  Perform a gaussian blur on all images

3.  Compute the laplacian on the blurred image to generate a gradient map

4.  Create a blank output image with the same size as the original input
    images

4.  For each pixel [x,y] in the output image, copy the pixel [x,y] from
    the input image which has the largest gradient [x,y]


This algorithm was inspired by the high-level description given at

http://stackoverflow.com/questions/15911783/what-are-some-common-focus-stacking-algorithms

Additional notes, OpenCv 3.1 has to be installed, inside there is a cv2.py file, you'll 
need tocopy it to : C:\Python27\Lib\site-packages


"""

import numpy as np
import cv2

def align_images(unaligned_images, warp_mode=cv2.MOTION_TRANSLATION):
    """
    Align all the images according to the first image in the folder
        -images : (list(image object)) unaligned images
        -return : (list(image object)) aligned images
    """
    number_of_iterations = 50;
    termination_eps = 0.0001;
    im_ref =  unaligned_images[0]
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, number_of_iterations,  termination_eps)

    aligned_images = []
    aligned_images.append(im_ref)

    im_ref_gray = cv2.cvtColor(im_ref, cv2.COLOR_BGR2GRAY)

    for index, image_to_align in enumerate(unaligned_images[1:]):
        image_to_align_gray = cv2.cvtColor(image_to_align, cv2.COLOR_BGR2GRAY)
         
        size = im_ref.shape

        if warp_mode == cv2.MOTION_HOMOGRAPHY :
            print "using MOTION HOMOGRAPHY for finding the ECC transform"
            warp_matrix = np.eye(3, 3, dtype=np.float32)
        else :
            print "using MOTION_TRANSLATION for finding the ECC transform"
            warp_matrix = np.eye(2, 3, dtype=np.float32)

        (cc, warp_matrix) = cv2.findTransformECC (im_ref_gray, image_to_align_gray, warp_matrix, warp_mode, criteria)
         
        print "Aligning image %s of %s" %(index+1, len(unaligned_images[1:]))
        if warp_mode == cv2.MOTION_HOMOGRAPHY :
            # Use warpPerspective for Homography 
            im2_aligned = cv2.warpPerspective (image_to_align, warp_matrix, (size[1], size[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
        else :
            # Use warpAffine for Translation, Euclidean and Affine
            im2_aligned = cv2.warpAffine(image_to_align, warp_matrix, (size[1], size[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP);
         
        # Show final results
        aligned_images.append(im2_aligned)
    return aligned_images
    
#
#   Compute the gradient map of the image
def doLap(image):

    # YOU SHOULD TUNE THESE VALUES TO SUIT YOUR NEEDS
    kernel_size = 5         # Size of the laplacian window
    blur_size = 5           # How big of a kernal to use for the gaussian blur
                            # Generally, keeping these two values the same or very close works well
                            # Also, odd numbers, please...

    blurred = cv2.GaussianBlur(image, (blur_size,blur_size), 0)
    return cv2.Laplacian(blurred, cv2.CV_64F, ksize=kernel_size)

#
#   This routine finds the points of best focus in all images and produces a merged result...
#
def focus_stack(unimages):
    images = align_images(unimages, cv2.MOTION_HOMOGRAPHY)

    print "Computing the laplacian of the blurred images"
    laps = []
    for i in range(len(images)):
        print "Lap {}".format(i)
        laps.append(doLap(cv2.cvtColor(images[i],cv2.COLOR_BGR2GRAY)))

    laps = np.asarray(laps)
    print "Shape of array of laplacians = {}".format(laps.shape)

    output = np.zeros(shape=images[0].shape, dtype=images[0].dtype)

    abs_laps = np.absolute(laps)
    maxima = abs_laps.max(axis=0)
    bool_mask = abs_laps == maxima
    mask = bool_mask.astype(np.uint8)
    for i in range(0,len(images)):
        output = cv2.bitwise_not(images[i],output, mask=mask[i])

    return  255-output

