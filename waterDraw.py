import evdev
from threading import Thread
from threading import Lock
import tkinter as tk
from time import sleep, time

# Constants
REFRESH = 1.0/1000
BRUSHSIZE = 5.0
BLANKSECONDS = 2.0
SCREENX = "800"
SCREENY = "500"
STICKTIME = 0.05

# Define a touchpad
class MyTouchpad:
    def __init__(self, path, maxX, maxY):
        self.path = path
        self.maxX = maxX
        self.maxY = maxY
        self.xPos = 0
        self.oldXPos = 0
        self.yPos = 0
        self.oldYPos = 0
        self.eventX = False
        self.eventY = False
    def setX(self, newX):
        self.xPos = newX
    def setOldX(self):
        self.oldXPos = self.xPos
    def getX(self):
        return self.xPos
    def getOldX(self):
        return self.oldXPos
    def setY(self, newY):
        self.yPos = newY
    def setOldY(self):
        self.oldYPos = self.yPos
    def getY(self):
        return self.yPos
    def getOldY(self):
        return self.oldYPos
    def getMaxX(self):
        return self.maxX
    def getMaxY(self):
        return self.maxY
    def newEventX(self):
        self.eventX = True
    def newEventY(self):
        self.eventY = True
    def endEvent(self):
        self.eventX = False
        self.eventY = False

# Find all devices and search for one called "Touchpad"
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
for device in devices:  
    if "Touchpad" in device.name:
        break
else:
    print("Touchpad not found")
    exit()

# Create touchpad object
touchpad = MyTouchpad(device, device.absinfo(0).max, device.absinfo(1).max)
touchpadLock = Lock()


# Begin TKinter canvas
root = tk.Tk()
root.title('Water Paint')
root.geometry(SCREENX+"x"+SCREENY)

canvas = tk.Canvas(root, width=touchpad.getMaxX(), height=touchpad.getMaxY(), bg='white')
canvas.pack()


running = True

# Alert when touchpad changes
def getEvent():
    for event in touchpad.path.read_loop():
        if not running:
            break
        if event.code == 53:
            touchpadLock.acquire()
            ### Touchpad object is locked

            touchpad.setX(event.value)
            touchpad.newEventX() 

            ### Touchpad object is released
            touchpadLock.release()
        elif event.code == 54:
            touchpadLock.acquire()
            ### Touchpad object is locked

            touchpad.setY(event.value)
            touchpad.newEventY() 

            ### Touchpad object is released 
            touchpadLock.release()
         
def drawLines():
    lastTouch = time() 
    while running:
        if (time() - lastTouch) > (BLANKSECONDS):
            canvas.delete("all")

        touchpadLock.acquire()
        ### Touchpad object is locked

        if touchpad.eventX and touchpad.eventY:
            
            tempX = touchpad.getX() * int(SCREENX) / touchpad.getMaxX()
            tempY = touchpad.getY() * int(SCREENY) / touchpad.getMaxY()
            canvas.create_oval(tempX - BRUSHSIZE, tempY - BRUSHSIZE, tempX + BRUSHSIZE, tempY + BRUSHSIZE, fill='black')
            if (time() - lastTouch) < STICKTIME:
                tempOldX = touchpad.getOldX() * int(SCREENX) / touchpad.getMaxX()
                tempOldY = touchpad.getOldY() * int(SCREENY) / touchpad.getMaxY()
                canvas.create_line(tempOldX, tempOldY, tempX, tempY, width=2*BRUSHSIZE, fill='black')
            touchpad.setOldX()
            touchpad.setOldY()
            lastTouch = time()
            touchpad.endEvent()

        ### Touchpad object is released
        touchpadLock.release()
        sleep(REFRESH)


def main():
    eventLoop = Thread(target=getEvent, daemon = True)
    drawLoop = Thread(target=drawLines, daemon = True)
    try:
        eventLoop.start()
        drawLoop.start()
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        eventLoop.join(timeout=1)
        drawLoop.join(timeout=1)
        exit()

if __name__=="__main__":
    main()
