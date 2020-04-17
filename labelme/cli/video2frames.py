#!/usr/bin/env python

import argparse
import os
import os.path as osp
import sys
import cv2

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--video', help='input video to be converted to frames', required = True)
    parser.add_argument('--output_dir', help='output directory where frames to be saved', required=True)

    args = parser.parse_args()

    if osp.exists(args.output_dir):
        print('Output directory already exists:', args.output_dir)
        sys.exit(1)
    os.makedirs(args.output_dir)
    
    print('Extracting frames to :', args.output_dir)

    capture = cv2.VideoCapture(args.video)
    if (capture.isOpened()== False): 
        print("Error opening input video file")

    index = 0
    while(capture.isOpened()):
        ret, frame = capture.read()
        if ret == True:
            filepath = osp.join(args.output_dir,"frame{}.png".format(index))
            index = index+1
            cv2.imwrite(filepath, frame)
        else:
            break
    
    capture.release()

if __name__ == '__main__':
    main()
