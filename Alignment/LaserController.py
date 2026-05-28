import serial
import time
from pycobolt import CoboltLaser

class OBISLaser640:
    def __init__(self, port):
        self.ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(0.5)
        flag = True
        while True:
            if self.checkInterlock():
                break
            else:
                if flag:
                    print("OBIS 640: Please turn the key ON")
                    flag = False
                time.sleep(1)
        
        self.on()
        self.setPower(0)

    def checkInterlock(self):
        try:
            self.ser.reset_input_buffer()
            self.ser.write(b"SYSTEM:LOCK?\r\n")
            response = self.ser.readline().decode().strip().upper()
            return "ON" in response
        except Exception as e:
            print(f"OBIS 640 Connection Error: {e}")
            return False

    def on(self):
        self.ser.write(b"SOURce:AM:STATe ON\r\n")
        time.sleep(0.1)
        return True

    def off(self):
        self.ser.write(b"SOURce:AM:STATe OFF\r\n")

    def setPower(self, mW):
        self.ser.write(f"SOURce:POW:LEV:IMM:AMPL {(mW * 0.001)}\r\n".encode())

    def close(self):
        self.off()
        self.ser.close()
        print("OBIS 640 closed")

class CoboltLaser488:
    def __init__(self, port):
        self.laser = CoboltLaser(port = port)
        state = self.laser.get_state()
        print(state)
        if state == "AutostartStandby":
            self.laser.turn_on()
            time.sleep(0.1)
            state = self.laser.get_state()
            print(state)
            if state == "AutostartWaitingForKeyOn":
                print("Cobolt 488: Please turn the key off -> on")
                while state == "AutostartWaitingForKeyOn":
                    time.sleep(1)
                    state = self.laser.get_state()
                    if state == "AutostartLaserOn":
                        break
        elif state == "AutostartWaitingForKeyOn":
            print("Cobolt 488: Please turn the key off -> on")
            while state == "AutostartWaitingForKeyOn":
                time.sleep(1)
                state = self.laser.get_state()
                if state == "AutostartLaserOn":
                    break

        self.laser.set_power(0)

    def setPower(self, mW):
        self.laser.set_power(mW)
        self.laser.send_cmd("l1")

    def getState(self):
        return self.laser.get_state()

    def off(self):
        self.laser.set_power(0)

    def close(self):
        self.laser.__exit__()
        print("Cobolt 488 closed")

class CoboltLaser561:
    def __init__(self, port):
        self.laser = CoboltLaser(port = port)
        state = self.laser.get_state()
        print(state)
        if state == "AutostartStandby":
            self.laser.turn_on()
            time.sleep(0.1)
            state = self.laser.get_state()
            if state == "AutostartWaitingForKeyOn":
                print("Please turn the key off -> on")
                while state == "AutostartWaitingForKeyOn":
                    time.sleep(1)
                    state = self.laser.get_state()
                    if state == "AutostartLaserOn":
                        break
        elif state == "AutostartWaitingForKeyOn":
            print("Please turn the key off -> on")
            while state == "AutostartWaitingForKeyOn":
                time.sleep(1)
                state = self.laser.get_state()
                if state == "AutostartLaserOn":
                    break

        self.laser.set_power(0)                

    def setPower(self, mW):
        self.laser.set_power(mW)
        self.laser.send_cmd("l1")

    def off(self):
        self.laser.set_power(0)

    def close(self):
        self.laser.__exit__()
