import time
import multiprocessing as mp
import os
import cv2 as cv
import numpy as np;


#hog = cv.HOGDescriptor()
#hog.setSVMDetector(cv.HOGDescriptor_getDefaultPeopleDetector())
#boxes = None
#fourcc = cv.VideoWriter_fourcc(*'XVID')
#out = cv.VideoWriter('Anh/' + str(datetime.now()) + '.avi', fourcc, 10.0, (640, 480))

def capture(imgq, stop):

    cam = cv.VideoCapture(0, cv.CAP_DSHOW)
    cam.set(cv.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    cam.set(cv.CAP_PROP_FPS, 30)

    while not stop.is_set():
        check, frame = cam.read()
        frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        if imgq.full():
            try: 
                imgq.get_nowait()
            except Exception:
                pass

        imgq.put(frame)

    cam.release()
            
      
def process(processedq, imgq, stop):
    while not stop.is_set():    
        if not imgq.empty():
            print("process")
            frame = imgq.get()
            
            if processedq.full():
                try: 
                    processedq.get_nowait()
                except Exception:
                    pass
            processedq.put(frame)

    return




if __name__ == "__main__":

    imgq = mp.Queue(maxsize = 3)
    stop = mp.Event()

    captureproc = mp.Process (target = capture, args = (imgq, stop))
    captureproc.start()

    processedq = mp.Queue(maxsize = 3)
    processproc = mp.Process (target = process, args = (processedq, imgq, stop))
    processproc.start()

    while True:     
        if not processedq.empty():
            frame = processedq.get()
            cv.imshow("image", frame)

       
           


        #boxes, weights = hog.detectMultiScale(frame, winStride=(8,8))
        #boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
        
        #for (xA, yA, xB, yB) in boxes:
                #people = cv.rectangle(frame, (xA, yA, xB, yB), (0, 255, 0), 2)
       
        #out.write(frame)
        
       



    #stop.set()
    #capture.join()
    #out.release()
    #cv.destroyAllWindows()
