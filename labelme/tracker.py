import cv2
import numpy as np
import copy
import labelme.utils.opencv as ocvutil

class Tracker():
    
    def __init__(self, *args, **kwargs):
        self.tracker = None
        self.shape = None
        
    def isRunning(self):
        return (self.tracker != None)
    
    def getRectForTracker(self, shape):        
        qrect = shape.boundingRect()
        tl = qrect.topLeft()
        h = qrect.height()
        w = qrect.width()
        rect = (tl.x(), tl.y(),w,h)
        
        return rect
    
    def getAffineTransform(self, srect, drect):
        #x0 y1 w2 h3
        sp_1 = [srect[0],srect[1]]
        sp_2 = [srect[0]+srect[2],srect[1]]
        sp_3 = [srect[0],srect[1]+srect[3]]
        spts = np.float32([sp_1,sp_2,sp_3])
        
        dp_1 = [drect[0],drect[1]]
        dp_2 = [drect[0]+drect[2],drect[1]]
        dp_3 = [drect[0],drect[1]+drect[3]]
        dpts = np.float32([dp_1,dp_2,dp_3])
        
        M = cv2.getAffineTransform(spts,dpts)
        return M
            
        
    def initTracker(self, qimg,shape):        
        status = False
        if qimg.isNull() or not shape:
            return status
        else:
            mat = ocvutil.qtImg2CvMat(qimg)
            srect = self.getRectForTracker(shape)
            self.tracker = cv2.TrackerCSRT_create()
            self.shape = shape
            status = self.tracker.init(mat, srect)
            if not status:
                #print("Init failed")
                self.__reset__()
                
        return status        
    
    def updateTracker(self, qimg, shape):
        
        assert (shape and shape.label == self.shape.label),"Inalid tracker state!"
        
        status = False
        
        result = shape
        
        if self.tracker is None or qimg.isNull():
            return result, status
        
        mat = ocvutil.qtImg2CvMat(qimg)
        rval, drect = self.tracker.update(mat)
        #print("Tracking for shape {} status {}".format(shape.label,rval))
        if(rval):
            srect = self.getRectForTracker(self.shape)
            T = self.getAffineTransform(srect,drect)
            result = copy.deepcopy(shape)
            result.transform(T)
            status = True
        
        return result , status
    
    def __reset__(self):
        self.tracker = None
        self.shape = None
        
    def stopTracker(self):
        self.__reset__()