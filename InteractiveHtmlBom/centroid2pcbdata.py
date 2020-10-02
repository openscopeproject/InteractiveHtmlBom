import json
import argparse
from ecad.generic import GenericCentroidParser
from version import version

import os
import sys

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Parse centroid file')
    parser.add_argument('-i',
                        '--input',
                        metavar='board.xy',
                        type=str,
                        required=True,
                        help='Input centroid file')
    parser.add_argument('-W',
                        '--width',
                        metavar='W',
                        type=float,
                        required=True,
                        help='Width of image, in mm')
    parser.add_argument('-H',
                        '--height',
                        metavar='H',
                        type=float,
                        required=True,
                        help='Height of image, in mm')
    parser.add_argument(
        '-M',
        '--mpp',
        metavar='M',
        type=float,
        required=True,
        help='micrometer per pixel of photorealistic PCB images')
    parser.add_argument('-o',
                        '--output',
                        metavar='pcbdata.json',
                        type=str,
                        required=True,
                        help='Output pcbdata file')

    args = parser.parse_args()

    config = None
    LOGGER = None
    centroid_file = GenericCentroidParser(args.input, config, LOGGER,
                                          args.width, args.height, args.mpp)

    pcbdata, components = centroid_file.parse()
    pcbdata['ibom_version'] = version

    with open(args.output, 'w') as f:
        json.dump(pcbdata, f, indent=2)
