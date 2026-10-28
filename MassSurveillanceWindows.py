from ast import main
import time
import multiprocessing as mp
import os
import cv2 as cv
import numpy as np;
from pymavlink import mavutil
import ctypes

width, height = 640, 480
size = width * height * 3

print("Program Start")


def capture(imgq, imgqbuffer, readyin, readyproc, stop):
    print("Capture Loop Started")
    cam = cv.VideoCapture(0, cv.CAP_DSHOW)
    cam.set(cv.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv.CAP_PROP_FRAME_WIDTH, 1920)
    cam.set(cv.CAP_PROP_FRAME_HEIGHT, 1080)
    cam.set(cv.CAP_PROP_FPS, 30)

    frameout = np.frombuffer(imgq.get_obj(), dtype=np.uint8).reshape(height, width, 3)
    frameoutbuffer = np.frombuffer(imgqbuffer.get_obj(), dtype=np.uint8).reshape(height, width, 3)

    while not stop.is_set():
        if not cam.isOpened():
            stop.set()
            break
        
        readyproc.wait()
        print("Getting Frame From Camera")
        check, frame = cam.read()
        if not check:
            break
        frame = cv.resize(frame, (width, height), interpolation=cv.INTER_AREA)

        np.copyto(frameout, frame)
        print("Frame Ready")
        readyproc.clear()
        readyin.set()
    
    cam.release()
    return  

def mav(data):
    connection = mavutil.mavlink_connection('COM4', baud=115200)
    connection.wait_heartbeat()
    print("Heartbeat Found")
   
    
    print("Data Requested")
    while True:
        connection.mav.command_long_send(
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE,
        0,  
        74, 
        0, 
        0,  
        0,  
        0,  
        0,  
        0,  
        )
        data = connection.recv_match(type='VFR_HUD', blocking = True)
        print("Data Read")
        print(data)
    return
      
def process(processedq, readyout, imgq, imgqbuffer, readyin, readyproc, stop):
    print("HOG Loop Started")

    hog = cv.HOGDescriptor()
    hog.setSVMDetector(cv.HOGDescriptor_getDefaultPeopleDetector())
    boxes = None

    framein = np.frombuffer(imgq.get_obj(), dtype=np.uint8).reshape(height, width, 3)
    frameout = np.frombuffer(processedq.get_obj(), dtype=np.uint8).reshape(height, width, 3)

    while not stop.is_set():    
        
        readyin.wait()
        print("Copying Frame For HOG")
        people = framein.copy()
        readyproc.set()
        readyin.clear()
        print("Starting HOG")

        boxes, weights = hog.detectMultiScale(people, winStride=(90,90), padding=(0,0), scale=1.05, hitThreshold=0.4, groupThreshold=3)
        boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
        
        for (xA, yA, xB, yB) in boxes:
            cv.rectangle(people, (xA, int(yA+35), int(xB/4), int(yB/2)), (0, 255, 0), 2)

        if not readyout.is_set(): #if the frame in the buffer has been displayed
            np.copyto(frameout, people) #copies the most recent frame into the buffer
            readyout.set() #tells the loop to display the frame
             
        print("HOG Done")
        
    return


if __name__ == "__main__":
    #data = mp.Value(ctypes.c_wchar_p, "why")
    connection = mavutil.mavlink_connection('COM4', baud=115200)
    connection.wait_heartbeat()
    print("Heartbeat Found")
   
    prevtime = 0
    newtime = 0

    totaltime = 0
    counter = 0
    average = 0

    imgqbuffer = mp.Array('B', size)
    imgq = mp.Array('B', size)

    processedq = mp.Array('B', size)

    readyin = mp.Event()
    readyout = mp.Event()
    readyproc = mp.Event()
    readyin = mp.Event()

    readyproc.set()

    stop = mp.Event()


    captureproc = mp.Process (target = capture, args = (imgq, imgqbuffer, readyin, readyproc, stop))
    captureproc.start()

    #mavproc = mp.Process (target = mav, args = (data,))
    #mavproc.start()

    processproc = mp.Process (target = process, args = (processedq, readyout, imgq, imgqbuffer, readyin, readyproc, stop))
    processproc.start()

    frame = np.frombuffer(processedq.get_obj(), dtype=np.uint8).reshape((height, width, 3))

    while True: 
        






        #print(data.value)
        readyout.wait() #waits until a frame is ready

        newtime = time.time()

        elapsed = newtime - prevtime

        totaltime += elapsed
        counter +=1

        average = totaltime / counter

        if counter > 20:
            totaltime = 0
            counter = 0

        cv.putText(frame, str(average), (5, 70), cv.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 0), 1, cv.LINE_AA)

        prevtime = newtime

        cv.imshow("image", frame) #displays the frame

        connection.mav.command_long_send(
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE,
        0,  
        74, 
        0, 
        0,  
        0,  
        0,  
        0,  
        0,  
        )
        data = connection.recv_match(type='VFR_HUD', blocking = True)
        print("Data Read")
        print(data)

        readyout.clear() #allows another frame to be put in the buffer

        key = cv.waitKey(1)
        if key == 27:
            break


    stop.set()
    captureproc.join()
    processproc.join()
    cv.destroyAllWindows()
