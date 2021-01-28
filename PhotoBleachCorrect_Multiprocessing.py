import numpy as np
from timeit import default_timer as timer
from pathlib import Path
import os
import tifffile
import glob
import argparse
import re
import multiprocessing
from functools import partial

"""
need to install tifffile, numpy
ref_file: always the first image in the time series
input_file: everyfile in time series except the 1st 

"""

def pbleach(input_file, ref_file, out_dir):
    ref_image = tifffile.imread(ref_file)
    input_image = tifffile.imread(input_file)
    result = hist_match(input_image, ref_image)
    result = np.asanyarray(result, dtype=ref_image.dtype)
    tifffile.imsave(os.path.join(out_dir, os.path.basename(input_file)), data=result)


def hist_match(source, template):
    """
    Adjust the pixel values of a grayscale image such that its histogram
    matches that of a target image

    Arguments:
    -----------
        source: np.ndarray // target
            Image to transform; the histogram is computed over the flattened
            array
        template: np.ndarray // referance
            Template image; can have different dimensions to source
    Returns:
    -----------
        matched: np.ndarray
            The transformed output image
    """

    oldshape = source.shape
    source = source.ravel()
    template = template.ravel()

    # get the set of unique pixel values and their corresponding indices and
    # counts
    s_values, bin_idx, s_counts = np.unique(source, return_inverse=True,
                                            return_counts=True)
    t_values, t_counts = np.unique(template, return_counts=True)

    # take the cumsum of the counts and normalize by the number of pixels to
    # get the empirical cumulative distribution functions for the source and
    # template images (maps pixel value --> quantile)
    s_quantiles = np.cumsum(s_counts).astype(np.float64)
    s_quantiles /= s_quantiles[-1]
    t_quantiles = np.cumsum(t_counts).astype(np.float64)
    t_quantiles /= t_quantiles[-1]

    # interpolate linearly to find the pixel values in the template image
    # that correspond most closely to the quantiles in the source image
    interp_t_values = np.interp(s_quantiles, t_quantiles, t_values)

    return interp_t_values[bin_idx].reshape(oldshape)

def alphanumeric_key(s):
    """ Taken from skimage io/collection.py
    """
    k = [int(c) if c.isdigit() else c for c in re.split('([0-9]+)', s)]
    return k

def photo_bleach_correct(input_dir, out_dir, available_channels):
    channel_files_map = {}
    

    for channel in available_channels:
        channel_files_map[channel] = glob.glob(os.path.join(input_dir, "*{}*.tif".format(channel)))
    
    # potential for improving  
    with multiprocessing.Pool() as pool:
        for channel, files in channel_files_map.items():
            sorted_files = sorted(files, key=alphanumeric_key)
            ref_file = sorted_files[0]
            # save the ref file as it is 
            _data = tifffile.imread(ref_file)
            print("File 0 path", os.path.join(out_dir, os.path.basename(ref_file)))
            tifffile.imsave(os.path.join(out_dir, os.path.basename(ref_file)), data=_data)
            pbleach_partial = partial(pbleach,ref_file= ref_file, out_dir=out_dir)
            pool.map(pbleach_partial, sorted_files[1:])
            #pool.imap_unordered(pbleach_partial, sorted_files[1:])

        # for _file in sorted_files[1:]:
        #     pbleach(ref_file=ref_file, input_file=_file, out_dir=out_dir)
    
    # for channel, files in channel_files_map.items():
    #     sorted_files = sorted(files, key=alphanumeric_key)
    #     ref_file = sorted_files[0]
    #     # save the ref file as it is 
    #     _data = tifffile.imread(ref_file)
    #     print("File 0 path", os.path.join(out_dir, os.path.basename(ref_file)))
    #     tifffile.imsave(os.path.join(out_dir, os.path.basename(ref_file)), data=_data)
    #     # pbleach_partial = partial(pbleach,ref_file= ref_file, out_dir=out_dir)
    #     # pool.map(pbleach_partial, sorted_files[1:])

    #     for _file in sorted_files[1:]:
    #         pbleach(ref_file=ref_file, input_file=_file, out_dir=out_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Photobleach Correction.')
    parser.add_argument('input_dir',  type=str, help='Input directory')
    parser.add_argument('output_dir',  type=str, help='output directory')
    
    parser.add_argument('--channels',  nargs='+',
                        help='list channels being used separated by space')

    args = parser.parse_args()
    
    photo_bleach_correct(args.input_dir, args.output_dir, available_channels = args.channels )
            
