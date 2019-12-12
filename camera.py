from threading import Thread
from threading import Lock
import cv2
import sys
import time

class PiVideoStream:
    """
    Pi Camera initialize then stream and read the first video frame from stream
    """
    def __init__(self, cameraConfig):
        try:
            from picamera.array import PiRGBArray
            from picamera import PiCamera
            self.camera = PiCamera()
        except:
            sys.exit(1)
        if cameraConfig['camerawidth'] != 0:
            self.camera.resolution = (cameraConfig['camerawidth'], cameraConfig['cameraheight'])
        self.camera.framerate = 32
        self.camera.rotation = 0
        self.camera.hflip = cameraConfig['flipvertically']
        self.camera.vflip = cameraConfig['fliphorizontally']
        self.camera.iso = cameraConfig['iso']
        time.sleep(2)
        self.camera.shutter_speed = self.camera.exposure_speed
        self.camera.exposure_mode = 'off'
        g = self.camera.awb_gains
        self.camera.awb_mode = 'off'
        self.camera.awb_gains = g

        self.rawCapture = PiRGBArray(self.camera, size=(cameraConfig['camerawidth'], cameraConfig['cameraheight']))
        self.stream = self.camera.capture_continuous(self.rawCapture,
                                                     format="bgr",
                                                     use_video_port=True)
        self.read_lock = Lock()
        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False

    def start(self):
        """ start the thread to read frames from the video stream """
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        """ keep looping infinitely until the thread is stopped """
        for f in self.stream:
            # if the thread indicator variable is set, stop the thread
            # and release camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            frame = f.array
            self.rawCapture.truncate(0)
            with self.read_lock:
                self.frame = frame

    def read(self):
        """ return the frame most recently read """
        with self.read_lock:
            frame = self.frame.copy()
        return frame

    def stop(self):
        """ indicate that the thread should be stopped """
        self.stopped = True
        time.sleep(1)

#------------------------------------------------------------------------------
class WebcamVideoStream:
    """
    WebCam initialize then stream and read the first video frame from stream
    """
    def __init__(self, cameraConfig):
        try:
            self.webcam = cv2.VideoCapture(cameraConfig['camerasource'])
        except:
            sys.exit(1)
        if cameraConfig['camerawidth'] == 0:
            self.width = int(self.webcam.get(3))
        else:
            self.width = cameraConfig['camerawidth']
            self.webcam.set(3, cameraConfig['camerawidth']) # set the resolution
        if cameraConfig['cameraheight'] == 0:
            self.height = int(self.webcam.get(4))
        else:
            self.height = cameraConfig['cameraheight']
            self.webcam.set(4, cameraConfig['cameraheight'])
        self.webcam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        (self.grabbed, self.frame) = self.webcam.read()
        self.cam_zoom = False
        self.read_lock = Lock()
        self.xIni = 0
        self.yIni = 0
        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False

    def start(self):
        """ start the thread to read frames from the video stream """
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        """ keep looping infinitely until the thread is stopped """
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                self.webcam.release()
                return
            # otherwise, read the next frame from the webcam stream
            grabbed, frame = self.webcam.read()
            '''if self.cam_zoom:
                frame = self.zoom(frame)'''
            with self.read_lock:
                self.grabbed = grabbed
                try:
                    #self.frame = cv2.resize(frame, (self.width, self.height))
                    self.frame = frame
                except:
                    None

    def read(self):
        """ return the frame most recently read """
        with self.read_lock:
            frame = self.frame.copy()
        return frame

    def stop(self):
        """ indicate that the thread should be stopped """
        self.stopped = True
        time.sleep(3)

    def zoom(self, frame):
        minX = int(self.webcam.get(3)*self.xIni/100)
        maxX = minX+int(self.webcam.get(3)*self.cam_zoom/100)
        minY = int(self.webcam.get(4)*self.yIni/100)
        maxY = minX+int(self.webcam.get(4)*self.cam_zoom/100)

        cropped = frame[minY:maxY, minX:maxX]
        resized_cropped = cv2.resize(cropped, (self.width, self.height))
        return resized_cropped


def iniciarCamera(cameraConfig):
    try:
        if str(cameraConfig['camerasource']).lower() == 'pi':
            print("Iniciando Pi Camera ....")
            cap = PiVideoStream(cameraConfig).start()
            time.sleep(1.5)  # Allow PiCamera time to initialize
        else:
            print("Iniciando Camera USB: ", str(cameraConfig['camerasource']))
            cap = WebcamVideoStream(cameraConfig).start()
            time.sleep(1.5) # Allow WebCam time to initialize
        return cap
    except:
        print("Erro em iniciar camera")
        sys.exit(0)


if __name__ == "__main__":
    cam = iniciarCamera(camera=1, width=300, height=300)
    cam.cam_zoom = 100
    #print(cam.width, cam.height)
    #cam = iniciarCamera('rtsp://192.168.0.187:554/user=yonface&password=yonface&channel=1&stream=0.sdp?')
    #cam = iniciarCamera(camera='PI')
    #cam = iniciarCamera(camera='PI', width=300, height=300)
    while True:
        frame = cam.read()
        #trabalhar com o frame...

        cv2.imshow("frame", frame)
        k = cv2.waitKey(1) & 0xFF

        if k == 27 or k == ord('q'):
            break  # esc to quit
        if k == ord('a'):
            cam.cam_zoom = cam.cam_zoom + 5
            print(cam.cam_zoom)
            #break  # esc to quit
    cv2.destroyAllWindows()
    cam.stop()
