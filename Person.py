from random import randint
import time

class MyPerson:
    def __init__(self, i, xi, yi, max_age):
        self.i = i
        self.x = xi
        self.y = yi
        self.originx = xi
        self.originy = yi
        self.R = randint(0,255)
        self.G = randint(0,255)
        self.B = randint(0,255)
        self.done = False
        self.age = 1
        self.max_age = max_age
        self.dir = None
        self.counted = False
    def getRGB(self):
        return (self.R,self.G,self.B)
    def getId(self):
        return self.i
    def getState(self):
        return self.state
    def getDir(self):
        if (self.y < self.originy):
            self.dir = 1
        else:
            self.dir = -1
        return self.dir
    def getX(self):
        return self.x
    def getY(self):
        return self.y
    def updateCoords(self, xn, yn):
        self.age = 0
        self.x = xn
        self.y = yn
    def age_one(self):
        self.age += 1
        if self.age > self.max_age:
            self.done = True
        return True