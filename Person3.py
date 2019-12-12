from random import randint
import time

class MyPerson:
    def __init__(self, idp, x, y):
        self.idp = idp
        self.posx = x
        self.posy = y
        self.inix = x
        self.iniy = y
        self.counted = False
        self.tracked = True
        self.age = 0

    def updateCoords(self, xn, yn):
        self.tracked = True
        self.age = 0
        self.posx = xn
        self.posy = yn