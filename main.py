import camera
import cv2
import numpy as np
import time
import camera_config
#from Person import MyPerson as Person
#from Person2 import MyPerson as Person
from Person3 import MyPerson as Person
from datetime import datetime


class CameraManager():
    """docstring for CameraManager"""
    def __init__(self, cameraConfig):
        self.pMOG2 = cv2.createBackgroundSubtractorMOG2(
            history=cameraConfig['history'], 
            varThreshold=cameraConfig['mogthreshold'], 
            detectShadows=cameraConfig['trackshadows'])
        self.pMOG2.setShadowThreshold(cameraConfig['shadowpixelratio'])
        self.cam = camera.iniciarCamera(cameraConfig)
        self.erodeamount = cameraConfig['erode']
        self.dilateamount = cameraConfig['dilate']
        self.kernelErode = np.ones((cameraConfig['erode'],cameraConfig['erode']),np.uint8) #matrix that  defines the area to use when calculating the value of each pixel.
        self.kernelDilate = np.ones((cameraConfig['dilate'],cameraConfig['dilate']),np.uint8)
        self.kernelSmallErode = np.ones((2,2),np.uint8)
        self.threshold = cameraConfig['threshold']
        self.blur = cameraConfig['blur']
        self.moglearnrate = cameraConfig['moglearnrate']
        self.bgray = cameraConfig['gray']


    def initMOG(self):
        for x in range(self.pMOG2.getHistory()):
            self.processMog()


    def processMog(self):
        frame = self.cam.read()
        if self.bgray:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        gray = cv2.GaussianBlur(gray, (self.blur, self.blur), 0)

        mask = self.pMOG2.apply(gray, learningRate=self.moglearnrate)

        _, mask = cv2.threshold(mask, self.threshold, 255, cv2.THRESH_BINARY)
        mask = cv2.GaussianBlur(mask, (self.blur, self.blur), 0)
        '''mask = cv2.dilate(mask, self.kernelDilate)
        mask = cv2.erode(mask, self.kernelErode)
        mask = cv2.dilate(mask, self.kernelDilate)'''
        mask = cv2.dilate(mask, None, iterations=self.dilateamount)
        mask = cv2.erode(mask, None, iterations=self.erodeamount)
        mask = cv2.dilate(mask, None, iterations=self.dilateamount)
        mask = cv2.GaussianBlur(mask, (self.blur, self.blur), 0)

        _, mask = cv2.threshold(mask, 50, 255, cv2.THRESH_BINARY)
        mask = cv2.erode(mask, None, 2)

        return frame, mask


    def draw(self, frame):
        (h, w) = frame.shape[:2]
        cv2.line(frame, (0, int(h/2)), (w, int(h/2)),(13,151,255),thickness=2)


    def exit(self):
        cv2.destroyAllWindows()
        self.cam.stop()
        

class Tracking():
    """docstring for Tracking"""
    def __init__(self, trackingConfig):
        self.maxage = trackingConfig['maxage']
        self.minarea = trackingConfig['minarea']
        self.maxarea = trackingConfig['maxarea']
        self.oneBlob = trackingConfig['minsizeone']
        self.twoBlob = trackingConfig['minsizetwo']
        self.threeBlob = trackingConfig['minsizethree']
        self.startposy = trackingConfig['startposy']
        self.offsettop = int(trackingConfig['startposy'] - (trackingConfig['offset']/2))
        self.offsetbot = int(trackingConfig['startposy'] + (trackingConfig['offset']/2))
        self.persons = []
        self.idp = 0

    def update(self, mask):
        _, contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        activity = []
        now = datetime.now()

        for cnt in contours:
            area = cv2.contourArea(cnt)

            if area > self.minarea and area < self.maxarea:
                M = cv2.moments(cnt)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                x,y,w,h = cv2.boundingRect(cnt)
        
                new = True
                for i in self.persons:
                    if i.age == 0:
                        continue
                    if (abs(x-i.getX()) <= w and abs(y-i.getY()) <= h): #Si el objeto esta cerca de uno detectado previamente
                        new = False #No es una nueva persona
                        i.updateCoords(cx,cy) #Actualizar coordenadas de la personas
                        if (i.counted == False and cy >= self.offsettop and cy <=self.offsetbot):
                            #se estiver na area de contagem, realizar contagem
                            cnt = 0
                            if (i.getDir()): # entrada
                                if w > self.threeBlob:
                                    cnt = 3
                                elif w > self.twoBlob:
                                    cnt = 2
                                elif w > self.oneBlob:
                                    cnt = 1
                            else:
                                if w > self.threeBlob:
                                    cnt = -3
                                elif w > self.twoBlob:
                                    cnt = -2
                                elif w > self.oneBlob:
                                    cnt = -1
                            if cnt != 0:
                                i.counted = True
                                activity.append((now, cnt))
                                print(str(now)+": "+str(cnt))
                        break


                if(new ==True):
                    p = Person(self.idp,cx,cy,self.maxage)
                    self.persons.append(p)
                    self.idp += 1

        for i in self.persons:
            i.age_one() #age every person one frame
            if(i.done == True):
                #sacar i de la lista persons
                index = self.persons.index(i)
                self.persons.pop(index)
                del i     #liberar la memoria de i

        return activity

    def draw(self, frame):
        for i in self.persons:
            cv2.putText(frame, str(i.getId()),(i.getX(),i.getY()),cv2.FONT_HERSHEY_SIMPLEX,0.3,i.getRGB(),1,cv2.LINE_AA)

        return frame


class TrackingV2():
    """docstring for Tracking"""
    def __init__(self, trackingConfig):
        self.maxage = trackingConfig['maxage']
        self.minarea = trackingConfig['minarea']
        self.maxarea = trackingConfig['maxarea']
        self.oneBlob = trackingConfig['minsizeone']
        self.twoBlob = trackingConfig['minsizetwo']
        self.threeBlob = trackingConfig['minsizethree']
        self.startposy = trackingConfig['startposy']
        self.offsettop = int(trackingConfig['startposy'] - (trackingConfig['offset']/2))
        self.offsetbot = int(trackingConfig['startposy'] + (trackingConfig['offset']/2))
        self.persons = []
        self.idp = 0
        self.line_up = int((self.startposy*0.47))
        self.line_down   = int(self.startposy*0.53)
        self.up_limit = int((self.startposy*2*0.20))
        self.down_limit = int((self.startposy*2*0.80))

    def update(self, mask):
        _, contours0, hierarchy = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        for cnt in contours0:
            area = cv2.contourArea(cnt)

            if area > self.minarea :
                #realizar tracking#
                M = cv2.moments(cnt)
                cx = int(M['m10']/M['m00']) #sacar el centro de la figura
                cy = int(M['m01']/M['m00'])
                x,y,w,h = cv2.boundingRect(cnt)

                new = True
                for i in self.persons:
                    #print len(personas)
                    i.age_one() #age every person one frame
                    if (abs(x-i.getX()) <= w and abs(y-i.getY()) <= h): #Si el objeto esta cerca de uno detectado previamente
                        new = False #No es una nueva persona
                        i.updateCoords(cx,cy) #Actualizar coordenadas de la personas
                        if (i.going_UP(self.offsettop) == True):
                            print('up')
                            #i.counted = True
                            if (w > 1.5*self.minarea):
                                print('up2')
                            #print ("ID:",i.getId(),'subiu em: ',time.strftime("%c"))

                        elif(i.going_DOWN(self.offsetbot) == True):
                            print('down')
                            #i.counted = True
                            if (w > 1.5*self.minarea):
                                print('down2')
                            #print ("ID:",i.getId(),'desceu em: ',time.strftime("%c"))
                        break

                    if(i.getState() == '1'):
                        if(i.getDir() == 'down' and i.getY() > self.down_limit):
                            i.setDone()
                        elif(i.getDir() == 'up' and i.getY() < self.up_limit):
                            i.setDone()

                    if(i.done == True):
                        #sacar i de la lista persons
                        index = self.persons.index(i)
                        self.persons.pop(index)
                        del i     #liberar la memoria de i


                if(new ==True):
                    p = Person(self.idp,cx,cy,self.maxage)
                    self.persons.append(p)
                    self.idp += 1


    def draw(self, frame):
        for i in self.persons:
            cv2.putText(frame, str(i.getId()),(i.getX(),i.getY()),cv2.FONT_HERSHEY_SIMPLEX,0.3,i.getRGB(),1,cv2.LINE_AA)

        return frame


class TrackingV3():
    """docstring for Tracking"""
    def __init__(self, trackingConfig):
        self.maxage = trackingConfig['maxage']
        self.minarea = trackingConfig['minarea']
        self.maxarea = trackingConfig['maxarea']
        self.oneBlob = trackingConfig['minsizeone']
        self.twoBlob = trackingConfig['minsizetwo']
        self.threeBlob = trackingConfig['minsizethree']
        self.startposy = trackingConfig['startposy']
        self.offsettop = int(trackingConfig['startposy'] - (trackingConfig['offset']/2))
        self.offsetbot = int(trackingConfig['startposy'] + (trackingConfig['offset']/2))
        self.persons = []
        self.idp = 0
        #self.up_limit = int((self.startposy*2*0.20))
        #self.down_limit = int((self.startposy*2*0.80))
        self.up_limit = trackingConfig['stoppostop']
        self.down_limit = trackingConfig['stopposbot']

    def update(self, mask):
        _, contours0, hierarchy = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        now = datetime.now()
        activity = []
        for cnt in contours0:
            area = cv2.contourArea(cnt)

            if area >= self.minarea:
                #realizar tracking
                M = cv2.moments(cnt)
                cx = int(M['m10']/M['m00']) #sacar el centro de la figura
                cy = int(M['m01']/M['m00'])
                x,y,w,h = cv2.boundingRect(cnt)

                new = True
                for i in self.persons:
                    #print len(personas)
                    if (abs(x-i.posx) <= w and abs(y-i.posy) <= h and not i.tracked): #Si el objeto esta cerca de uno detectado previamente
                        new = False #No es una nueva persona
                        i.updateCoords(cx,cy) #Actualizar coordenadas de la personas
                        
                        if cy > self.offsettop and cy < self.offsetbot and not i.counted:
                            cnt = 0
                            if cy > i.iniy: #going down
                                print(str(now), "going down")
                                if w > self.threeBlob:
                                    cnt = -3
                                elif w > self.twoBlob:
                                    cnt = -2
                                elif w > self.oneBlob:
                                    cnt = -1
                            elif cy < i.iniy:
                                print(str(now), "going up")
                                if w > self.threeBlob:
                                    cnt = 3
                                elif w > self.twoBlob:
                                    cnt = 2
                                elif w > self.oneBlob:
                                    cnt = 1
                            if cnt != 0:
                                i.counted = True
                                activity.append((now, cnt))
                        break
                if new:
                    p = Person(self.idp, cx, cy)
                    self.persons.append(p)
                    self.idp += 1

        for i in self.persons:
            if not i.tracked:
                i.age += 1
                if i.age > self.maxage:
                    index = self.persons.index(i)
                    self.persons.pop(index)
                    del i   #liberar la memoria de i
            else:
                i.tracked = False
                if i.posy < self.up_limit and i.posy > self.down_limit and i.counted:
                    index = self.persons.index(i)
                    self.persons.pop(index)
                    del i
        return activity

    def draw(self, frame):
        h, w = frame.shape[:2]
        for i in self.persons:
            cv2.putText(frame, str(i.idp),(i.posx,i.posy),cv2.FONT_HERSHEY_SIMPLEX,0.3,(255,0,0),1,cv2.LINE_AA)
        cv2.line(frame, (0, self.offsettop), (w, self.offsettop),(255,151,255),thickness=1)
        cv2.line(frame, (0, self.offsetbot), (w, self.offsetbot),(255,151,255),thickness=1)
        cv2.line(frame, (0, self.up_limit), (w, self.up_limit),(13,13,255),thickness=1)
        cv2.line(frame, (0, self.down_limit), (w, self.down_limit),(13,13,255),thickness=1)

        return frame


if __name__ == "__main__":
    try:
        conf = camera_config.readJsonFile()
        cm = CameraManager(conf['Footfall']['CameraConfig'])
        tck = TrackingV3(conf['Footfall']['TrackingConfig'])
        cm.initMOG()
        x = 0
        while True:

            start_time = time.time() 
            frame, mask = cm.processMog()
            facts = tck.update(mask)
            cm.draw(frame)
            tck.draw(frame)
            cv2.imshow('frame', cv2.resize(frame, (640, 480)))
            cv2.imshow('mask', mask)
            #cv2.imwrite(str(x)+'.jpg', frame)
            time.sleep(0.05)
            x+=1

            #print("FPS: ", 1.0 / (time.time() - start_time))
            k = cv2.waitKey(1) & 0xFF
            if k == 27 or k == ord('q'):
                break  # esc to quit

    finally:
        cv2.destroyAllWindows()
        cm.exit()