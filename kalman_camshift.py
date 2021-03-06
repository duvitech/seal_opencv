#!/usr/bin/env python

import cv2
import numpy as np
import time
import imutils
import datetime


scaling_factor = 1.0
    

def frame_diff(prev_frame, cur_frame, next_frame):
    diff_frames1 = cv2.absdiff(next_frame, cur_frame)
    diff_frames2 = cv2.absdiff(cur_frame, prev_frame)
    return cv2.bitwise_and(diff_frames1, diff_frames2)

def get_frame(cap):
    ret, frame = cap.read()
    frame = cv2.resize(frame, None, fx=scaling_factor, 
            fy=scaling_factor, interpolation=cv2.INTER_AREA)
    return cv2.applyColorMap(frame, cv2.COLORMAP_JET)


cap = cv2.VideoCapture("videos/Nov_19_2.mov")
ret,frame = cap.read()

# setup initial location of window
r,h,c,w = 300,200,400,300  # simply hardcoded the values
track_window = (c,r,w,h)

roi = frame[r:r+h, c:c+w]
hsv_roi =  cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv_roi, np.array((160., 30.,32.)), np.array((180.,120.,255.)))
roi_hist = cv2.calcHist([hsv_roi],[0],mask,[180],[0,180])
cv2.normalize(roi_hist,roi_hist,0,255,cv2.NORM_MINMAX)
term_crit = ( cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1 )

kalman = cv2.KalmanFilter(4,2)
kalman.measurementMatrix = np.array([[1,0,0,0],[0,1,0,0]],np.float32)
kalman.transitionMatrix = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]],np.float32)
kalman.processNoiseCov = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],np.float32) * 0.03

measurement = np.array((2,1), np.float32) 
prediction = np.zeros((2,1), np.float32)

def center(points):
    x = (points[0][0] + points[1][0] + points[2][0] + points[3][0]) / 4.0
    y = (points[0][1] + points[1][1] + points[2][1] + points[3][1]) / 4.0
    return np.array([np.float32(x), np.float32(y)], np.float32)


while(True):
    ret, frame = cap.read()
    if ret is False:
        break;
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    dst = cv2.calcBackProject([hsv],[0],roi_hist,[0,180],1)
    
    ret, track_window = cv2.CamShift(dst, track_window, term_crit)
    
    pts = cv2.boxPoints(ret)
    pts = np.int0(pts)
    (cx, cy), radius = cv2.minEnclosingCircle(pts)
    kalman.correct(center(pts))
    img2 = cv2.polylines(frame,[pts],True, 255,2)
    prediction = kalman.predict()
    cv2.circle(frame, (prediction[0], prediction[1]), int(radius), (0, 255, 0))
    cv2.imshow('img2',img2)    

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
        
# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
