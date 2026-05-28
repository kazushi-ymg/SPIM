from pylablib.devices import Thorlabs
import time

class EmissionFilter:
    def __init__(self, port, name="EmissionFilter"):
        try:
            self.filter = Thorlabs.serial.FW(port)
            
            self.currentPos = self.getPosition()
            print(f"Current position is {self.currentPos}")
            
        except Exception as e:
            self.filter = None

    def setPosition(self, pos):
        if self.filter:
            self.filter.set_position(pos)
            
            while self.getPosition() != pos:
                time.sleep(0.1)
            
            self.currentPos = pos
            print(f"Moved to position {pos}")
            return True
        return False

    def getPosition(self):
        if self.filter:
            return self.filter.get_position()
        return None

    def close(self):
        if self.filter:
            self.filter.close()
            print(f"Filter wheel closed.")