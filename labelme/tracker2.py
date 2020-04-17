import cv2
import numpy as np
import copy
import labelme.utils.opencv as ocvutil

class Tracker():

    def __init__(self, *args, **kwargs):
        self.criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 1000,1e-10)
        self.ref_img = None
        self.shape = None

    @property
    def isRunning(self):
        return (self.ref_img is not None)

    def getRectForTracker(self, img, shape):
        H = img.shape[0]
        W = img.shape[1]

        qrect = shape.boundingRect()
        tl = qrect.topLeft()
        h = qrect.height()
        w = qrect.width()

        x = 0 if (tl.x() -w/4) < 0 else tl.x() -w/4
        y = 0 if (tl.y() -h/4) < 0 else tl.y() -h/4

        w = 3*w/2 if (x + 3*w/2) < W else (W- x +1)
        h = 3*h/2 if (y + 3*h/2) < H else (H- y +1)

        rect = (x,y,w,h)

        return [int(_) for _ in rect]

    def initTracker(self, qimg,shape):
        status = False
        if qimg.isNull() or not shape:
            return status
        else:
            fimg = ocvutil.qtImg2CvMat(qimg)
            srect = self.getRectForTracker(fimg, shape)
            fimg = fimg[srect[1]:srect[1]+srect[3],srect[0]:srect[0]+srect[2]]
            fimg = cv2.resize(fimg, (0, 0), fx = 0.5, fy = 0.5)
            self.ref_img = cv2.cvtColor(fimg,cv2.COLOR_BGR2GRAY)
            self.shape = shape
            status = True

        return status

    def updateTracker(self, qimg, shape):

        assert (shape and shape.label == self.shape.label),"Inalid tracker state!"

        status = False

        result = shape

        if not self.isRunning or qimg.isNull():
            return result, status

        mimg = ocvutil.qtImg2CvMat(qimg)
        srect = self.getRectForTracker(mimg,self.shape)
        mimg = mimg[srect[1]:srect[1]+srect[3],srect[0]:srect[0]+srect[2]]
        mimg = cv2.resize(mimg, (0, 0), fx = 0.5, fy = 0.5)
        mimg = cv2.cvtColor(mimg,cv2.COLOR_BGR2GRAY)

        warp_matrix = np.eye(2, 3, dtype=np.float32)
        cc = False

        try:
            (cc, T) = cv2.findTransformECC (self.ref_img,mimg,warp_matrix,cv2.MOTION_AFFINE, \
                    self.criteria, None, 1)
        except:
            cc = False

        if(cc):
            result = copy.deepcopy(shape)
            result.transform(T)
            status = True
        else:
            print("Tracker failed")

        return result , status

    def __reset__(self):
        self.ref_img = None
        self.shape = None

    def stopTracker(self):
        self.__reset__()