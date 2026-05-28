import time
import os
import gc
import glob
import json
import numpy as np
import tifffile as tf
from pylablib.devices import Thorlabs 
from LaserController import CoboltLaser488, CoboltLaser561, OBISLaser640
from EmissionFilter import EmissionFilter
from StageController import StageController

class AcquisitionManager:
    def __init__(self, params):
        self.params = params
        self.DELTA_DIST = (self.params['refractiveIndex'] - 1.00) / self.params['refractiveIndex']
        self.lasers = {}
        laserList = []
        for i in range(6):
            if self.params['acqFlag'][i] == 1:
                laserList.append(self.params['laser'][i])
        laserList = set(laserList)
        if 1 in laserList:
            self.lasers[1] = CoboltLaser488("COM3")
        if 2 in laserList:
            self.lasers[2] = CoboltLaser561("COM10")
        if 3 in laserList:
            self.lasers[3] = OBISLaser640("COM7")
        self.emFilter = EmissionFilter("COM11")
        self.camera = Thorlabs.TLCamera.ThorlabsTLCamera('35512')
        self.stage1 = StageController("COM8")
        self.stage2 = StageController("COM9")
        self.stageCalibrationResult = self.loadAlignment()
        
        if not os.path.exists(self.params['outputPath']):
            os.makedirs(self.params['outputPath'])

    def loadAlignment(self):
        targetDir = "C:/Users/kazushi/Documents/JSON"
        jsonFiles = glob.glob(os.path.join(targetDir, "[0-9]"*6 + "_[0-9]"*6 + ".json"))

        if not jsonFiles:
            raise FileNotFoundError("JSON files not found. Please run AlignmentTool first")

        jsonFiles.sort()
        latestJSON = jsonFiles[-1]

        with open(latestJSON, "r", encoding="utf-8") as f:
            alignmentResult = json.load(f)

        return alignmentResult["relativeFocusPosition"]

    def runSequence(self):
        try:
            if self.params['sampleSize'] == 0:
                xNum = 2
                xStep = 5.0
                xStart = 2.0
            else:
                xNum = 3
                xStep = 6.6
                xStart = 0.0
            zNum = self.params['zNumber']
            zStep = self.params['zInterval']
            for x in range(xNum):
                targetX = x * xStep + xStart
                self.stage1.moveAt(1, targetX)
                self.stage1.waitMove(1)
                for z in range(zNum):
                    targetZ = z * zStep + self.params['zInitialPosition'] - 25
                    self.stage2.moveAt(1, targetZ)
                    self.stage2.waitMove(1)

                    for i in range(6):
                        if self.params['acqFlag'][i] == 0:
                            continue

                        print("--- Moving home position ---")
                        self.stage1.moveAt(2, -4)
                        self.stage2.moveAt(2, -10)            
                        self.stage1.waitMove(2)
                        self.stage2.waitMove(2)

                        self.emFilter.setPosition(i + 1)
                        currentLaser = self.lasers.get(self.params['laser'][i])
                        if currentLaser:
                            currentLaser.setPower(self.params['intensity'][i])
                            time.sleep(3)
                            self.stage1.move(2, self.params['distance'], self.params['stageVelocity'])
                            self.stage2.move(2, -1 * self.params['distance'] * self.DELTA_DIST, self.params['stageVelocity'] * self.DELTA_DIST)
                            stack = self.captureImages(self.params['exposure'][i])
                            self.stage1.waitMove(2)
                            self.saveMultiTIFF(stack, x, z, i)
                            del stack
                            gc.collect()
                            currentLaser.setPower(0)
        finally:
            self.stage1.moveAt(2, -4)
            self.stage2.moveAt(2, -10)            
            self.stage1.waitMove(2)
            self.stage2.waitMove(2)
            print("Completed")

    def captureImages(self, exposure):
        exposure = exposure / 1000    # sec -> ms
        self.camera.set_exposure(exposure)
        self.camera.setup_acquisition(nframes = 2000)
        
        imgs = []
        self.camera.start_acquisition()
        while True:
            self.camera.wait_for_frame()
            frame = self.camera.read_oldest_image()
            if frame is not None:
                frame = np.round(frame/4094*255).astype('u1')    #convert 8-bit
                imgs.append(frame)
            if self.stage1.sendCommand("AXI2:MOTION?") == '0':
                time.sleep(exposure)
                break

        self.camera.stop_acquisition()
        print("done")
        return imgs

    def saveMultiTIFF(self, data, x, z, ID):
        fileName = self.params.get('fileName', 'img')
        outputPath = self.params['outputPath']
        chunkSize = self.params.get('chunkSize', 100)
        if self.params['laser'][ID] == 1:
            laserName = "488 nm"
        elif self.params['laser'][ID] == 2:
            laserName = "561 nm"
        elif self.params['laser'][ID] == 3:
            laserName = "640 nm"
        channelName = self.params['filter'][ID]
        totalFrames = len(data)
        chunkNum = (totalFrames + chunkSize - 1) // chunkSize

        for chunk in range(chunkNum):
            start = chunk * chunkSize
            end = min((chunk + 1) * chunkSize, totalFrames)

            chunkData = np.array(data[start:end])
            file = f"{fileName}_X{x + 1}_Z{z + 1}_{laserName}_{channelName}_{chunk + 1}.tiff"
            fullPath = os.path.join(outputPath, file)

            tf.imwrite(fullPath, chunkData, photometric='minisblack')

    def cleanup(self):
        for laser in self.lasers.values():
            try:
                laser.close()
            except:
                pass
        self.emFilter.close()
        self.stage1.close()
        self.stage2.close()
        if self.camera:
            self.camera.close()
        print("If you want to restart, launch the coboltMonitor and press More>Restart")

def startAcquisition(gui_values):
    acq = AcquisitionManager(gui_values)
    acq.runSequence()