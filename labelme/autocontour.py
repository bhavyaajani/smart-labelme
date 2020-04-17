import cv2
import numpy as np
from qtpy.QtCore import Qt
from qtpy import QtCore
from qtpy import QtGui
from labelme.shape import Shape

import labelme.utils.opencv as ocvutil

CURSOR_MOVE = QtCore.Qt.ClosedHandCursor
CURSOR_DRAW = QtCore.Qt.CrossCursor
CURSOR_WAIT = QtCore.Qt.BusyCursor
CURSOR_EDIT = QtCore.Qt.PointingHandCursor

class AutoContour(object):

    START, DEFINE, EDIT = 0, 1, 2

    CONTOUR_EPSILON = 5
    SCALE = 0.5

    line_color = QtGui.QColor(0, 255, 0, 128)
    invalid_rect_color = QtGui.QColor(255, 0, 0, 128)

    def __init__(self, canvas):
        self.canvas = canvas

        self.img = None
        self.mask = None
        self.prevmask = None
        self.rect = None
        self.contours = None
        self.state = self.START
        self.mask_background = False

    def init(self):
        self.reset()

        self.canvas.overrideCursor(CURSOR_DRAW)
        w = self.canvas.pixmap.width()

        self.img = ocvutil.qtImg2CvMat(self.canvas.pixmap.scaledToWidth(w*self.SCALE).toImage())
        self.mask = np.zeros(self.img.shape[:2], dtype = np.uint8)

    @property
    def minContourArea(self):
        assert self.img is not None
        return (self.img.shape[0] * self.img.shape[1]) / 50

    @property
    def isShapeRestorable(self):
        return self.prevmask is not None

    def segment(self):
        if self.img is None or self.rect is None:
            return

        bgdmodel = np.zeros((1, 65), np.float64)
        fgdmodel = np.zeros((1, 65), np.float64)

        rf = self.SCALE
        rect = [self.rect.x(),self.rect.y(),self.rect.width(),self.rect.height()]
        rect = list(map(int,rect))
        rect = [p*rf for p in rect]

        self.canvas.overrideCursor(CURSOR_WAIT)

        if self.state == self.DEFINE:
            try:
                cv2.grabCut(self.img, self.mask, rect, bgdmodel, fgdmodel, 2, cv2.GC_INIT_WITH_RECT)
            except:
                pass
        elif self.state == self.EDIT:
            try:
                cv2.grabCut(self.img, self.mask, rect, bgdmodel, fgdmodel, 1, cv2.GC_INIT_WITH_MASK)
            except:
                pass

        self.getContourFromMask()

    def paint(self, painter):
        pen = QtGui.QPen(self.line_color)
        pen.setWidth(5)

        line_path = QtGui.QPainterPath()

        if self.state == self.EDIT:
            mask2 = np.where((self.mask==2)|(self.mask==0),0,1).astype('uint8')
            img = ocvutil.cvMask2QImg(mask2)
            img.setColorCount(2)
            img.setColor(0, QtGui.qRgb(0, 0, 0))
            img.setColor(1, QtGui.qRgb(255, 255, 255))
            #img.save('Mask.png')

            osize = self.canvas.pixmap.size()
            pixmap = QtGui.QPixmap.fromImage(img)
            pixmap = pixmap.scaled(osize, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.setOpacity(0.25)
            painter.drawPixmap(0, 0, pixmap)
            painter.setOpacity(1.0)

        if self.state == self.DEFINE and self.rect:
            #print("GrabCut: Paint")
            area = self.rect.height()*self.rect.width()

            color = self.invalid_rect_color if area < self.minContourArea \
            else self.line_color

            pen.setStyle(Qt.DashLine)
            pen.setColor(color)
            line_path.addRect(self.rect)

        elif self.state in [self.EDIT] and self.contours:
            for contour in self.contours:
                line_path.moveTo(contour[0])
                for p in contour:
                    line_path.lineTo(p)
                line_path.lineTo(contour[0])
        else:
            pass

        painter.setPen(pen)
        painter.drawPath(line_path)

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            if self.state == self.START:
                #print("GrabCut: Mouse Pressed")
                pos = self.canvas.event_point_in_image(ev)
                self.rect = QtCore.QRectF(pos.x(), pos.y(),1,1)
                self.state = self.DEFINE
                self.canvas.update()
                return
            elif self.state == self.EDIT:
                self.prevmask = self.mask.copy()
                self.mask_background = False
                return

        if ev.button() == QtCore.Qt.RightButton:
            if self.state == self.EDIT:
                self.prevmask = self.mask.copy()
                self.mask_background = True
                return

    def mouseMoveEvent(self, ev):
        if QtCore.Qt.LeftButton & ev.buttons():
            if self.state == self.START:
                #print("Draw Cursor")
                self.canvas.overrideCursor(CURSOR_DRAW)
                return

            if self.state == self.DEFINE:
                #print("GrabCut: Mouse Moved")
                self.canvas.overrideCursor(CURSOR_MOVE)
                pos = self.canvas.event_point_in_image(ev)
                self.rect = QtCore.QRectF(min(self.rect.x(), pos.x()), min(self.rect.y(), pos.y()),
                    abs(self.rect.x() - pos.x()), abs(self.rect.y() - pos.y()))
                self.canvas.update()
                return

        if (QtCore.Qt.LeftButton | QtCore.Qt.RightButton) & ev.buttons():
            if self.state == self.EDIT:
                self.canvas.overrideCursor(CURSOR_EDIT)
                pos = self.canvas.event_point_in_image(ev)
                rf = self.SCALE
                if self.mask_background:
                    cv2.circle(self.mask, (int(rf*pos.x()), int(rf*pos.y())), 2, 0, -1)
                else:
                    cv2.circle(self.mask, (int(rf*pos.x()), int(rf*pos.y())), 2, 1, -1)

                self.canvas.update()
                return

    def mouseReleaseEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton and self.state == self.DEFINE:
            #print("GrabCut: Mouse Released")
            pos = self.canvas.event_point_in_image(ev)
            rect = QtCore.QRectF(min(self.rect.x(), pos.x()), min(self.rect.y(), pos.y()),
                    abs(self.rect.x() - pos.x()), abs(self.rect.y() - pos.y()))

            area = rect.height()*rect.width()
            if area < self.minContourArea:#safe guard against premature release
                return

            self.rect = rect
            self.segment()
            self.state = self.EDIT
            self.canvas.overrideCursor(CURSOR_EDIT)
            self.canvas.update()
            return

        if self.state == self.EDIT:
            self.segment()
            self.canvas.drawingPolygon.emit(False)
            self.canvas.overrideCursor(CURSOR_EDIT)
            self.canvas.update()
            return

    def mouseDoubleClickEvent(self, ev):
        pass

    def keyPressEvent(self, ev):
        key = ev.key()
        if key == QtCore.Qt.Key_Escape:
            pass
            #self.reset()
            #self.canvas.update()
        elif key == QtCore.Qt.Key_Return and self.state == self.EDIT:
            self.finalise()
            self.canvas.overrideCursor(CURSOR_DRAW)

    def getContourFromMask(self):
        if self.mask is None:
            return

        self.contours = []

        mask2 = np.where((self.mask==2)|(self.mask==0),0,1).astype('uint8')
        #img = img*mask2[:,:,np.newaxis]
        #cv2.imwrite('grab.png',mask2)

        rf = self.SCALE
        rb = 1.0/rf
        area_threshold = self.minContourArea * rf * rf
        approx_contours = []

        if np.count_nonzero(mask2 == 1) > area_threshold:
            contours, hierarchy = cv2.findContours(mask2, cv2.RETR_EXTERNAL , cv2.CHAIN_APPROX_SIMPLE)
            approx_contours = [cv2.approxPolyDP(c,self.CONTOUR_EPSILON,True) for c in contours if cv2.contourArea(c) > area_threshold]
            #cv2.contourArea(x)

        for cvcnt in approx_contours:
            qtcnt = []
            for p in cvcnt:
                qtcnt.append(QtCore.QPoint(p[0][0],p[0][1])*rb)
            self.contours.append(qtcnt)

    def finalise(self):
        if self.state == self.EDIT and self.contours:
            for contour in self.contours:
                shape = Shape(shape_type='polygon')
                for p in contour:
                    shape.addPoint(p)
                self.canvas.finalise(shape)

            self.reset()

    def undo(self):
        if self.prevmask is not None:
            self.mask = self.prevmask
            self.segment()
            self.prevmask = None
            self.canvas.update()

    def reset(self):
        if self.img is not None:
            self.mask = np.zeros(self.img.shape[:2], dtype = np.uint8)
        else:
            self.mask = None

        self.prevmask = None
        self.rect = None
        self.contours = None
        self.state = self.START
