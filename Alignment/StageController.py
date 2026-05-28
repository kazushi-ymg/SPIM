# import libraries
import serial
import time

class StageController:
    def __init__(self, port, baudrate=38400, timeout=2):
        self.ser = serial.Serial(
            port,
            baudrate,
            timeout=timeout,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            rtscts=False,
            dsrdtr=False
        )
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.COEFF = 500    # 500 pulses / mm, 2 um / pulse
        print(f"Connecting to DS102 on {port}...")
        idn = self.sendCommand("*IDN?")
        if "SURUGA" in idn:
            print(f"Connected: {idn}")
        for axis in ['1', '2']:
            self.sendCommand(f"AXI{axis}:READY?")
            time.sleep(0.1)
        self.sendCommand("AXI1:UNIT 0:STANDARD 1:DRDIV 0")
        time.sleep(0.5)
        self.sendCommand("AXI2:UNIT 0:STANDARD 1:DRDIV 0")
        time.sleep(0.5)

    def sendCommand(self, command):
        if self.ser.is_open:
            self.ser.reset_input_buffer()
            fullCmd = (command + '\r').encode('utf-8')
            self.ser.write(fullCmd)
            self.ser.flush()
            time.sleep(0.2)

            if self.ser.in_waiting > 0:       
                read_data = self.ser.read_until(b'\r')
                response = read_data.decode('utf-8').strip()
                return response
            else:
                self.ser.write(b'\n')
                return ""
            return ""
            
    def move(self, axis, distance, velocity):    # distance [mm], velocity [mm / s]
        distance = int(distance * self.COEFF)
        direction = "CW" if distance >= 0 else "CCW"
        velocity = int(velocity * self.COEFF)
        command = (f"AXI{axis}:L0 100:R0 100:S0 100:F0 {int(velocity)}:PULS {abs(distance)}:GO {direction}")    # L0: initial speed (pps), R0: time for max velocity (ms), S0: shape for accelerate (%), F0: velocity (pps)
        self.sendCommand(command)

    def moveAt(self, axis, position):
        currentPos = self.getPosition(axis)
        distance = int(position * self.COEFF) - currentPos
        direction = "CW" if distance >= 0 else "CCW"
        command = (f"AXI{axis}:L0 100:R0 100:S0 100:F0 1000"
                    f":PULS {abs(distance)}:GO {direction}")    # 2 mm / sec
        self.sendCommand(command)
        
    def calibrate(self):
        self.sendCommand("AXI1:F0 2000")
        time.sleep(0.5)
        self.sendCommand("AXI2:F0 2000")
        time.sleep(0.5)
        self.sendCommand("AXI1:GO 5")
        time.sleep(0.5)
        self.sendCommand("AXI2:GO 5")
        self.waitMove(1)
        self.waitMove(2)
        CWlimit1 = self.getPosition(1)
        CWlimit2 = self.getPosition(2)

        self.sendCommand("AXI1:GO 6")      
        time.sleep(0.5)
        self.sendCommand("AXI2:GO 6")
        self.waitMove(1)
        self.waitMove(2)
        CCWlimit1 = self.getPosition(1)
        CCWlimit2 = self.getPosition(2)

        center1 = (CWlimit1 + CCWlimit1) / 2 / self.COEFF
        center2 = (CWlimit2 + CCWlimit2) / 2 / self.COEFF
        self.moveAt(1, center1)
        time.sleep(0.5)
        self.moveAt(2, center2)
        self.waitMove(2)
        return center1, center2
        
    def waitMove(self, axis):
        while True:
            status = self.sendCommand(f"AXI{axis}:MOTION?")
            if status == '0':
                break
            else:
                time.sleep(1)

    def getPosition(self, axis):
        position = self.sendCommand(f"AXI{axis}:POS?")
        return int(position)
        
    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            
# COM8: x[-503, 14894], stage[-5008, 10576]
# COM9: z[-15691, 2], cam[-15640, 4]

# mm scale
# COM8: x[-1, 29], stage[-10, 20]
# COM9: z[-30, 0], cam[-30, 0]

# direction
# COM8: + Back x Front -, + <- stage -> -
# COM9: + Down z Up -, - <- cam -> +
