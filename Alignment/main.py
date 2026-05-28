import sys
import os
import time
import numpy as np
import json
import subprocess
import serial
import pycobolt
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QComboBox, QMessageBox, 
                             QHBoxLayout, QPushButton, QWidget, QDoubleSpinBox, QGridLayout, QRadioButton, QGroupBox)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from pylablib.devices import Thorlabs 

from StageController import StageController
from LaserController import CoboltLaser488, OBISLaser640

class LasersMonitor(QThread):
    statusChanged = Signal(str, bool)

    def __init__(self, lasers):
        super().__init__()
        self.lasers = lasers
        self.running = True

    def run(self):
        self.msleep(500)
        while self.running:
            allPassed = True
            errorMessages = []

            laser488 = self.lasers.get(0)
            if laser488:
                try:
                    state = laser488.getState()
                    if "AutostartLaserOn" not in state:
                        allPassed = False
                        errorMessages.append("488 nm")
                except Exception as e:
                    allPassed = False
                    errorMessages.append("488 nm (Error)")

            self.msleep(300)
            if not self.running: break

            laser640 = self.lasers.get(1)
            if laser640:
                try:
                    interlock = laser640.checkInterlock()
                    if not interlock:
                        allPassed = False
                        errorMessages.append("640 nm")
                except Exception as e:
                    allPassed = False
                    errorMessages.append("640 nm (Error)")
                    
            self.msleep(300)

            if allPassed:
                self.statusChanged.emit("Laser key status: OK", True)
            else:
                missing = ",".join(errorMessages)
                self.statusChanged.emit(f"Laser key status: turn the key on [{missing}]", False)
            self.msleep(1000)

    def stop(self):
        self.running = False

class AlignmentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alignment Tool")
        self.resize(400, 650)

        self.stage1 = None
        self.stage2 = None
        self.lasers = {}
        self.thorcamProcess = None
        self.lasersMonitor = None
        self.offsets = {
            "X": 0.0,
            "Stage": 0.0,
            "Z": 0.0,
            "Camera": 0.0
        }
        
        try:
            self.filter = Thorlabs.serial.FW("COM11")
        except Exception as e:
            print(f"Filter Wheel Error: {e}")
            self.filter = None

        self.initUI()
        self.Timer = QTimer()
        self.Timer.timeout.connect(self.updateAllPositions)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, self.startSequence)

    def startSequence(self):
        self.initStages()
        self.initLasers()

        self.startLasersMonitor()
        
        self.Timer.start(500)
        self.launchThorCam()

    def launchThorCam(self):
        thorcamPath = "C:/Program Files/Thorlabs/Scientific Imaging/ThorCam/ThorCam.exe"
        if os.path.exists(thorcamPath):
            try:
                print("Launching ThorCam...")
                exeDir = os.path.dirname(thorcamPath)
                self.thorcamProcess = subprocess.Popen([thorcamPath], cwd=exeDir)        

                time.sleep(2.0) 
            except Exception as e:
                print(f"Failed to launch ThorCam: {e}")
        else:
            print(f"ThorCam.exe not found at: {thorcamPath}")
            QMessageBox.warning(self, "Launch Error", f"ThorCam shortcut not found.\nPlease launch it manually.")

    def initStages(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Calibration")
        msg.setText("Stages are calibrating... Please wait.")
        msg.setStandardButtons(QMessageBox.NoButton)
        msg.show()
        QApplication.processEvents()

        try:
            self.stage1 = StageController("COM8")
            QApplication.processEvents()
            self.stage2 = StageController("COM9")
            QApplication.processEvents()
            
            self.xc, self.sc = self.stage1.calibrate()
            self.offsets["X"] = self.xc
            self.offsets["Stage"] = self.sc
            self.zc, self.cc = self.stage2.calibrate()
            self.offsets["Z"] = self.zc
            self.offsets["Camera"] = self.cc
        except Exception as e:
            print(f"Stage Error: {e}")
            self.stage1 = None
            self.stage2 = None
        msg.accept()

    def initLasers(self):
        self.lasers = {}
        try:
            self.lasers[0] = CoboltLaser488("COM3")
        except Exception as e:
            print(f"488 nm Laser Error: {e}")
            self.laser488Label.setText("CoboltLaser488: Connection Error")
        
        try:
            self.lasers[1] = OBISLaser640("COM7")
        except Exception as e:
            print(f"Laser Error: {e}")
            self.laser640Label.setText("OBISLaser640: Connection Error")
    
    def initUI(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        statusGroup = QGroupBox("Laser Key Status")
        statusLayout = QVBoxLayout()
        self.laserStatusLabel = QLabel("Laser key status: turn the key on")
        self.laserStatusLabel.setStyleSheet("color: #FF5722; font-weight: bold; font-size: 12px;")
        statusLayout.addWidget(self.laserStatusLabel)
        
        statusGroup.setLayout(statusLayout)
        layout.addWidget(statusGroup)

        filterGroup = QGroupBox("Filter Wheel")
        filterLayout = QHBoxLayout()
        filters = ["525-50", "595-50", "706-95", "Empty", "Empty", "Empty"]
        
        self.fw = QComboBox()
        self.fw.addItems([filters[i] for i in range(6)])
        self.fw.currentIndexChanged.connect(self.changeFilter)
        filterLayout.addWidget(QLabel("Select: "))
        filterLayout.addWidget(self.fw)
        filterGroup.setLayout(filterLayout)
        layout.addWidget(filterGroup)

        laserGroup = QGroupBox("Laser Control")
        laserLayout = QVBoxLayout()
        
        self.laserRadios = {}
        wavelengths = [488, 640]
        
        for i, wavelength in enumerate(wavelengths):
            rb = QRadioButton(f"{wavelength} nm")
            self.laserRadios[i] = rb
            laserLayout.addWidget(rb)
        self.laserRadios[0].setChecked(True)
        
        laserLayout.addWidget(QLabel("Laser power [mW]:"))
        self.laserPower = QDoubleSpinBox()
        self.laserPower.setRange(0.0, 10.0)
        laserLayout.addWidget(self.laserPower)
        
        self.laserOnButton = QPushButton("ON")
        self.laserOnButton.setCheckable(True)
        self.laserOnButton.clicked.connect(self.toggleLaser)
        laserLayout.addWidget(self.laserOnButton)
        
        laserGroup.setLayout(laserLayout)
        layout.addWidget(laserGroup)

        stageGroup = QGroupBox("Stage Movement")
        stageLayout = QVBoxLayout()
        
        stageLayout.addWidget(QLabel("Step size [mm]"))
        self.step = QDoubleSpinBox()
        self.step.setRange(0.002, 1.000)
        self.step.setValue(0.100)
        self.step.setSingleStep(0.100)
        self.step.setDecimals(3)
        stageLayout.addWidget(self.step)
        
        grid = QGridLayout()
        self.posLabels = {}
        axesConfig = [
            ("X", 1, 1, 0),
            ("Stage", 1, 2, 1),
            ("Z", 2, 1, 2),
            ("Camera", 2, 2, 3)
        ]

        def makeMoveSlot(stageID, axis, direction):
            if stageID == 1:
                return lambda: self.moveStage(self.stage1, axis, direction)
            else:
                return lambda: self.moveStage(self.stage2, axis, direction)

        for name, stageNum, nAxis, row in axesConfig:
            minusButton = QPushButton("<")
            minusButton.setFixedSize(50, 45)
            minusButton.clicked.connect(makeMoveSlot(stageNum, nAxis, -1))
            
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
            
            plusButton = QPushButton(">")
            plusButton.setFixedSize(50, 45)
            plusButton.clicked.connect(makeMoveSlot(stageNum, nAxis, 1))

            posLabel = QLabel("0.000 mm")
            posLabel.setAlignment(Qt.AlignCenter)
            self.posLabels[name] = posLabel
            
            grid.addWidget(minusButton, 2 * row, 0)
            grid.addWidget(lbl, 2 * row, 1)
            grid.addWidget(plusButton, 2 * row, 2)
            grid.addWidget(posLabel, 2 * row + 1, 0, 1, 3)

        stageLayout.addLayout(grid)
        stageGroup.setLayout(stageLayout)
        layout.addWidget(stageGroup)
        layout.addStretch()

        self.setCentralWidget(widget)

    def changeFilter(self, index):
        if self.filter:
            pos = index + 1
            try:
                self.filter.set_position(pos)
            except Exception as e:
                print(f"Filter Wheel Error: {e}")
    
    def toggleLaser(self):
        selectedWavelength = 488
        for wl, rb in self.laserRadios.items():
            if rb.isChecked():
                selectedWavelength = wl
                break
        
        laser = self.lasers.get(selectedWavelength)
        if not laser: return

        if self.laserOnButton.isChecked():
            power = self.laserPower.value()
            laser.setPower(power)
            self.laserOnButton.setText("OFF")
            self.laserOnButton.setStyleSheet("background-color: #55ff55; color: black; font-weight: bold;")
        else:
            laser.setPower(0)
            self.laserOnButton.setText("ON")
            self.laserOnButton.setStyleSheet("background-color: #ddd;")

    def startLasersMonitor(self):
        if self.lasers:
            self.lasersMonitor = LasersMonitor(self.lasers)
            self.lasersMonitor.statusChanged.connect(self.updateLaserStatusLabel)
            self.lasersMonitor.start()
            
    def updateLaserStatusLabel(self, message, flag):
        self.laserStatusLabel.setText(message)
        if flag:
            self.laserStatusLabel.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 12px;")
        else:
            self.laserStatusLabel.setStyleSheet("color: #FF5722; font-weight: bold; font-size: 12px;")

    def updateAllPositions(self):
        configs = [
            ("X", self.stage1, 1),
            ("Stage", self.stage1, 2),
            ("Z", self.stage2, 1),
            ("Camera", self.stage2, 2)
        ]
        
        for name, controller, axis in configs:
            if controller:
                try:
                    pos = controller.getPosition(axis) / 500
                    pos = pos - self.offsets[name]
                    self.posLabels[name].setText(f"{pos:.3f} mm")
                except:
                    self.posLabels[name].setText("Error")
                    
    def moveStage(self, controller, axis, direction):
        if not controller:
            print("Stage controller not connected.")
            return
            
        step = self.step.value() * direction
        controller.move(axis, step, 0.2)
        QTimer.singleShot(100, self.updateAllPositions)

    def createJSON(self):
        focusPosition = {}
        configs = [
            ("X", self.stage1, 1),
            ("Stage", self.stage1, 2),
            ("Z", self.stage2, 1),
            ("Camera", self.stage2, 2)
        ]

        for name, controller, axis in configs:
            if controller:
                try:
                    pos = controller.getPosition(axis) / 500
                    pos = pos - self.offsets[name]
                    focusPosition[name] = round(pos, 3)
                except:
                    focusPosition[name] = None
            else:
                focusPosition[name] = None
                
        saveData = {
            "relativeFocusPosition": focusPosition,
            "calibrationOffsets": self.offsets.copy()
        }
        fileName = time.strftime("%y%m%d_%H%M%S.json")
        targetDir = "C:/Users/kazushi/Documents/JSON"
        if not os.path.exists(targetDir):
            os.makedirs(targetDir)
            
        try:
            with open(os.path.join(targetDir, fileName), "w", encoding="utf-8") as f:
                json.dump(saveData, f, indent = 4, ensure_ascii = False)
        except Exception as e:
            print(f"Failed to save JSON: {e}")

    def closeEvent(self, event):
        if self.lasersMonitor and self.lasersMonitor.isRunning():
            self.lasersMonitor.stop()
            self.lasersMonitor.wait()
            
        if hasattr(self, 'Timer'):
            self.Timer.stop()

        self.createJSON()

        if self.thorcamProcess:
            try:
                self.thorcamProcess.terminate()
            except Exception as e:
                print(f"Failed to close ThorCam: {e}")
                
        for laser in self.lasers.values():
            try:
                laser.setPower(0)
                laser.close()
            except:
                pass
        if self.stage1:
            self.stage1.close()
        if self.stage2:
            self.stage2.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AlignmentWindow()
    window.show()
    sys.exit(app.exec())
