import time
import multiprocessing as mp
import os
import cv2 as cv
import numpy as np;

width, height = 640, 480
size = width * height * 3
#fourcc = cv.VideoWriter_fourcc(*'XVID')
#out = cv.VideoWriter('Anh/' + str(datetime.now()) + '.avi', fourcc, 10.0, (640, 480))


def capture(imgq, imgqbuffer, readyin, readyproc, stop):

    cam = cv.VideoCapture(0, cv.CAP_DSHOW)
    cam.set(cv.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    cam.set(cv.CAP_PROP_FPS, 30)

    frameout = np.frombuffer(imgq.get_obj(), dtype=np.uint8).reshape(height, width, 3)
    frameoutbuffer = np.frombuffer(imgqbuffer.get_obj(), dtype=np.uint8).reshape(height, width, 3)

    while not stop.is_set():
        
        readyproc.wait()
        print("Getting Frame From Camera")
        check, frame = cam.read()
        if not check:
            continue

        np.copyto(frameout, frame)
        print("Frame Ready")
        readyproc.clear()
        readyin.set()
      
    cam.release()
            
      
def process(processedq, processedqbuffer, readyout, imgq, imgqbuffer, readyin, readyproc, stop):

    hog = cv.HOGDescriptor()
    hog.setSVMDetector(cv.HOGDescriptor_getDefaultPeopleDetector())
    boxes = None

    framein = np.frombuffer(imgq.get_obj(), dtype=np.uint8).reshape(height, width, 3)
    frameout = np.frombuffer(processedq.get_obj(), dtype=np.uint8).reshape(height, width, 3)
    frameoutbuffer = np.frombuffer(processedqbuffer.get_obj(), dtype=np.uint8).reshape(height, width, 3)


    while not stop.is_set():    
        
        readyin.wait()
        print("Copying Frame For HOG")      
        np.copyto(frameout, framein)
        readyproc.set()
        readyin.clear()
        print("Starting HOG")

        boxes, weights = hog.detectMultiScale(frameout, winStride=(8,8))
        boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])

        
        
        for (xA, yA, xB, yB) in boxes:
            cv.rectangle(frameout, (xA, yA, xB, yB), (0, 255, 0), 2)

        if not readyout.is_set():
            np.copyto(frameoutbuffer, frameout)
            readyout.set()

        
        print("HOG Done")
        
          

    return


if __name__ == "__main__":
    imgqbuffer = mp.Array('B', size)
    imgq = mp.Array('B', size)

    processedqbuffer = mp.Array('B', size)
    processedq = mp.Array('B', size)

    readyin = mp.Event()
    readyout = mp.Event()
    readyproc = mp.Event()

    readyproc.set()

    stop = mp.Event()
    
    captureproc = mp.Process (target = capture, args = (imgq, imgqbuffer, readyin, readyproc, stop))
    captureproc.start()

    processproc = mp.Process (target = process, args = (processedq, processedqbuffer, readyout, imgq, imgqbuffer, readyin, readyproc, stop))
    processproc.start()

    frame = np.frombuffer(processedq.get_obj(), dtype=np.uint8).reshape((height, width, 3))

    while True:     
        
        readyout.wait()
        print("Showing Frame")
        cv.imshow("image", frame)
        readyout.clear()
        #out.write(frame)

        key = cv.waitKey(1)
        if key == 27:
            break
        
       


    #out.release()
    stop.set()
    captureproc.join()
    processproc.join()
    cv.destroyAllWindows()