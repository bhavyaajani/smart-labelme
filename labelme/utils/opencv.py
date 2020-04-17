import numpy as np
import cv2
from qtpy import QtGui

def qtImg2CvMat(inImage):
    inImage = inImage.convertToFormat(13) #format QImage::Format_RGB888

    width = inImage.width()
    height = inImage.height()

    ptr = inImage.bits()
    ptr.setsize(inImage.byteCount())
    mat = np.array(ptr).reshape(height, width, 3)  #  Shape the data

    rgb = cv2.cvtColor(mat, cv2.COLOR_BGR2RGB)
    #cv2.imwrite('tmp.png', rgb)
    return rgb

def cvMask2QImg(inMat):
    assert len(inMat.shape) == 2 and inMat.dtype == np.uint8
        
    arr2 = np.require(inMat, np.uint8, 'C')
    qImg = QtGui.QImage(arr2, inMat.shape[1], inMat.shape[0], inMat.shape[1], QtGui.QImage.Format_Indexed8)
    return qImg

#height, width, channel = cvImg.shape
#bytesPerLine = 3 * width
#qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()