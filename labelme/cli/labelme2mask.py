#!/usr/bin/env python

from __future__ import print_function

import argparse
import glob
import os
import os.path as osp
import sys

import PIL.Image as Image
import numpy as np

import labelme

def lblsave(filename, lbl):
    import imgviz
    
    if osp.splitext(filename)[1] != '.png':
        filename += '.png'
    # Assume label ranses [-1, 254] for int32,
    # and [0, 255] for uint8 as VOC.
    if lbl.min() >= 0 and lbl.max() < 255:
        lbl_pil = Image.fromarray(lbl.astype(np.uint8), mode='P')
        colormap = imgviz.label_colormap()
        lbl_pil.putpalette(colormap.flatten())
        lbl_pil.save(filename)
        
        numpy_file = osp.splitext(filename)[0] + '.npy'
        np.save(numpy_file, lbl)
    else:
        raise ValueError(
            '[%s] Cannot save the pixel-wise class label as PNG. '
            'Please consider using the .npy format.' % filename
        )
        
def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--input_dir', help='input annotated directory')
    parser.add_argument('--output_dir', help='output dataset directory')
    parser.add_argument('--labels', help='labels file', required=True)

    args = parser.parse_args()

    if osp.exists(args.output_dir):
        print('Output directory already exists:', args.output_dir)
        sys.exit(1)
    os.makedirs(args.output_dir)
    
    print('Creating masks:', args.output_dir)

    class_names = []
    class_name_to_id = {}
    for i, line in enumerate(open(args.labels).readlines()):
        class_id = i
        class_name = line.strip()
        class_name_to_id[class_name] = class_id
        class_names.append(class_name)
    class_names = tuple(class_names)
    print('class_names:', class_names)
    out_class_names_file = osp.join(args.output_dir, 'class_names.txt')
    with open(out_class_names_file, 'w') as f:
        f.writelines('\n'.join(class_names))
    print('Saved class_names:', out_class_names_file)

    for filename in glob.glob(osp.join(args.input_dir, '*.json')):
        print('Generating dataset from:', filename)

        label_file = labelme.LabelFile(filename=filename)

        base = osp.splitext(osp.basename(filename))[0]
        out_png_file = osp.join(args.output_dir, base + '.png')
        #img = labelme.utils.img_data_to_arr(label_file.imageData)

        size = [s for s in reversed(label_file.imgsize)] #Takes (height,width)
        lbl, _ = labelme.utils.shapes_to_label(
            img_shape=size,
            shapes=label_file.shapes,
            label_name_to_value=class_name_to_id,
        )
        lblsave(out_png_file, lbl)

if __name__ == '__main__':
    main()
