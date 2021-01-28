import sys
import os
from pycudadecon import RLContext, rl_decon
import tifffile
from pycudadecon.otf import make_otf, TemporaryOTF
import re
import glob
import argparse

"""
need to install https://github.com/tlambert03/pycudadecon
need to install tifffile
input_file < input tif file>
out_dir <output dir>
psf_file <for this channel>
"""

def alphanumeric_key(s):
    """ Taken from skimage io/collection.py
    Convert string to list of strings and ints that gives intuitive sorting.
    Parameters
    ----------
    s : string
    Returns
    -------
    k : a list of strings and ints
    Examples
    --------
    >>> alphanumeric_key('z23a')
    ['z', 23, 'a']
    >>> filenames = ['f9.10.png', 'e10.png', 'f9.9.png', 'f10.10.png',
    ...              'f10.9.png']
    >>> sorted(filenames)
    ['e10.png', 'f10.10.png', 'f10.9.png', 'f9.10.png', 'f9.9.png']
    >>> sorted(filenames, key=alphanumeric_key)
    ['e10.png', 'f9.9.png', 'f9.10.png', 'f10.9.png', 'f10.10.png']
    """
    k = [int(c) if c.isdigit() else c for c in re.split('([0-9]+)', s)]
    return k

def deconvolution(input_dir, output_dir, psf_dir, available_channels, dxpsf=0.104, dzpsf=0.104, na=1.25, nimm=1.3, n_iters=10):
    channel_files_map = {}
    channel_psf_map = {}

    # all_files = set(os.listdir(input_dir))
    # all_psf = set(os.listdir(psf_dir))
    

    for channel in available_channels:
        channel_files_map[channel] = glob.glob(os.path.join(input_dir, "*{}nm*.tif".format(channel)))
        channel_psf_map[channel] = glob.glob(os.path.join(psf_dir, "*{}*.tif".format(channel)))[0]
    
    # print(channel_files_map)
    # print(channel_psf_map)
    # potential for improving  
    for channel, files in channel_files_map.items():
        sorted_files = sorted(files, key=alphanumeric_key)
        current_psf = channel_psf_map[channel]
        print("current_psf", current_psf)
        for _file in sorted_files:
            decon(input_file=_file, out_dir=output_dir, psf_file=current_psf, dxpsf=0.104, dzpsf=0.210, na=1.25, nimm=1.3, n_iters=10)


def decon(input_file, out_dir, psf_file, dxpsf=0.104, dzpsf=0.210, na=1.25, nimm=1.3, n_iters=10):
    with TemporaryOTF(psf_file, dxpsf=dxpsf, dzpsf=dzpsf, na=na, nimm=nimm) as otf:
        # imlist = glob(image_folder + '*488*.tif')
        with tifffile.TiffFile(input_file) as tf:
            imshape = tf.series[0].shape
        with RLContext(shape=imshape, otfpath=otf.path, dz=dzpsf) as ctx:
            image = tifffile.imread(input_file)
            result = rl_decon(image, n_iters=n_iters, output_shape=ctx.out_shape)
            tifffile.imsave(os.path.join(out_dir, os.path.basename(input_file)), data=result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Deconvlution.')
    parser.add_argument('input_dir',  type=str, 
                        help='Input directory (assums psf directory is a child of this directory)')
    parser.add_argument('output_dir',  type=str, help='output directory')
    parser.add_argument('psf_dir',  type=str, help='psf directory')
    
    parser.add_argument('--channels',  nargs='+',
                        help='list channels being used separated by space')
    
    parser.add_argument('--dxpsf', nargs='?', type=float,  default=0.104, help='XY pixel size of psf microns')
    parser.add_argument('--dzpsf', nargs='?', type=float,  default=0.210, help='Z pixel size of psf microns')
    parser.add_argument('--na', nargs='?', type=float,  default=1.25, help='Numarical aparture')
    parser.add_argument('--nimm', nargs='?', type=float,  default=1.3, help='Rifrative index')
    parser.add_argument('--n_iters', nargs='?', type=float,  default=10, help='Rifrative index')

    args = parser.parse_args()
    
    deconvolution(args.input_dir, args.output_dir, args.psf_dir,
        available_channels = args.channels, dxpsf=args.dxpsf, dzpsf=args.dzpsf, na=args.na, nimm=args.nimm, n_iters=args.n_iters
     )
    # print(args.accumulate(args.integers))
