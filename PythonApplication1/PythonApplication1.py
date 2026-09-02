import time
import multiprocessing as mp
import os
import cv2 as cv
import numpy as np;

width, height = 640, 480
size = width * height * 3
#hog = cv.HOGDescriptor()
#hog.setSVMDetector(cv.HOGDescriptor_getDefaultPeopleDetector())
#boxes = None
#fourcc = cv.VideoWriter_fourcc(*'XVID')
#out = cv.VideoWriter('Anh/' + str(datetime.now()) + '.avi', fourcc, 10.0, (640, 480))


def capture(imgq, readyin, readyproc, stop):

    cam = cv.VideoCapture(0, cv.CAP_DSHOW)
    cam.set(cv.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    cam.set(cv.CAP_PROP_FPS, 30)

    shareframe = np.frombuffer(imgq.get_obj(), dtype=np.uint8).reshape(height, width, 3)

    while not stop.is_set():
        if readyproc.value == 1:
            check, frame = cam.read()
            if not check:
                continue

            np.copyto(shareframe, frame)
            readyproc.value = 0
            readyin.value = 1
        else:
            time.sleep(0.001)

    cam.release()
            
      
def process(processedq, readyout, imgq, readyin, readyproc, stop):

    hog = cv.HOGDescriptor()
    hog.setSVMDetector(cv.HOGDescriptor_getDefaultPeopleDetector())
    boxes = None

    framein = np.frombuffer(imgq.get_obj(), dtype=np.uint8).reshape(height, width, 3)
    frameout = np.frombuffer(processedq.get_obj(), dtype=np.uint8).reshape(height, width, 3)

    while not stop.is_set():    
        if readyin.value == 1:
            print("process")
            readyin.value = 0
            np.copyto(frameout, framein)
            readyproc.value = 1

            boxes, weights = hog.detectMultiScale(frameout, winStride=(8,8))
            boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
        
            for (xA, yA, xB, yB) in boxes:
                people = cv.rectangle(frameout, (xA, yA, xB, yB), (0, 255, 0), 2)

            readyout.value = 1
        else:
            time.sleep(0.001)
          

    return


if __name__ == "__main__":

    imgq = mp.Array('B', size)
    processedq = mp.Array('B', size)

    readyin = mp.Value('b', 0)
    readyout = mp.Value('b', 0)
    readyproc = mp.Value('b', 1)

    stop = mp.Event()

    captureproc = mp.Process (target = capture, args = (imgq, readyin, readyproc, stop))
    captureproc.start()

    processproc = mp.Process (target = process, args = (processedq, readyout, imgq, readyin, readyproc, stop))
    processproc.start()

    frame = np.frombuffer(processedq.get_obj(), dtype=np.uint8).reshape((height, width, 3))

    while True:     
        if readyout.value == 1:
            readyout.value = 0
            cv.imshow("image", frame)

       
           


        #boxes, weights = hog.detectMultiScale(frame, winStride=(8,8))
        #boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
        
        #for (xA, yA, xB, yB) in boxes:
                #people = cv.rectangle(frame, (xA, yA, xB, yB), (0, 255, 0), 2)
       
        #out.write(frame)
        key = cv.waitKey(1)
        if key == 27:  # ESC Key
            break
        
       


    #out.release()
    stop.set()
    captureproc.join()
    processproc.join()
    cv.destroyAllWindows()