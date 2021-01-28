from pycudadecon import deskewGPU
import cupy as cp
import numpy as np
import tifffile
import glob
import os
import argparse

"""
need to install https://github.com/tlambert03/pycudadecon
need to install tifffile, cupy numpy
"""

def deskew_noise_padding(input_file, out_dir, angle, dz, pixel_size):
    image = tifffile.imread(input_file)
    deskewed = deskewGPU(image, angle=angle, dzdata=dz, dxdata=pixel_size, pad_val=0)

    image_cp = cp.array(image)
    deskewed_cp = cp.array(deskewed)

    _, col, row = image_cp.shape
    noise_size = cp.ceil(cp.max(cp.array([row, col])) * 0.1)
    image_noise_patch = image_cp[0:noise_size, col - (noise_size + 1):col - 1, :]
    image_noise_patch = image_noise_patch.flatten()

    fill_length = deskewed_cp.size - cp.count_nonzero(deskewed_cp)
    repeat_frequency = cp.ceil(fill_length/image_noise_patch.size)
    repeat_frequency = cp.asnumpy(repeat_frequency).flatten().astype(dtype=np.uint16)[0]
    noise = cp.tile(image_noise_patch, repeat_frequency+1)
    noise = noise[0:fill_length]
    deskewed_cp[deskewed_cp == 0] = noise
    result =  cp.asnumpy(deskewed_cp)
    # print("saving", os.path.join(out_dir, os.path.basename(input_file)))
    tifffile.imsave(os.path.join(out_dir, os.path.basename(input_file)), data=result)

def deskew(input_dir, out_dir, angle, dz, pixel_size):
    all_files = glob.glob(os.path.join(input_dir, "*.tif"))
    for _file in all_files:
        deskew_noise_padding(input_file=_file, out_dir=out_dir, angle=angle, dz=dz, pixel_size=pixel_size)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Deskew.')
    parser.add_argument('input_dir',  type=str, 
                        help='Input directory (assums psf directory is a child of this directory)')
    parser.add_argument('output_dir',  type=str, help='output directory')
    
    parser.add_argument('--dx', nargs='?', type=float,  default=0.104, help='XY pixel size of psf microns')
    parser.add_argument('--dz', nargs='?', type=float,  default=0.4, help='z step size')
    parser.add_argument('--angle', nargs='?', type=float,  default=31.8, help='Deskew angle')
    
    args = parser.parse_args()
    
    deskew(args.input_dir, args.output_dir, pixel_size=args.dx, dz=args.dz, angle=args.angle)
