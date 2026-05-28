import sys
import os
import datetime
import glob
from PySide6.QtWidgets import QApplication, QMessageBox
from GUI import GUI
from AcquisitionManager import AcquisitionManager

def main():
    app = QApplication(sys.argv)
    targetDir = "C:/Users/kazushi/Documents/JSON"
    today = datetime.datetime.now().strftime("%y%m%d")
    todayFiles = glob.glob(os.path.join(targetDir, f"{today}_*.json"))
    if not todayFiles:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Alignment Data Not Found")
        msg.setText("Run AlignmentTool first.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
        sys.exit(0)

    gui = GUI()
    gui.show()
    
    def okClicked():
        gui.returnValues()
        
        if sum(gui.acqFlag) == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Parameter error")
            msg.setText("Select at least one laser.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            return
            
        try:
            saveDir = gui.outputPath
            if not os.path.exists(saveDir):
                os.makedirs(saveDir)

            timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
            prefix = gui.fileName if gui.fileName else "img"
            fullPath = os.path.join(saveDir, f"{prefix}_{timestamp}.png")
            pic = gui.grab()
            pic.save(fullPath, "PNG")

        except Exception as e:
            print(f"Failed to save screenshot: {e}")
            
        params = {
            'outputPath': gui.outputPath,
            'chunkSize': gui.chunkSize,
            'stageVelocity': gui.stageVelocity,
            'distance': gui.distance,
            'sampleSize': gui.sampleSize,
            'refractiveIndex': gui.refractiveIndex,
            'zNumber': gui.zNumber,
            'zInitialShift': gui.zInitialShift,
            'zInterval': gui.zInterval,
            'filter': gui.filter,
            'acqFlag': gui.acqFlag,
            'laser': gui.laser,
            'intensity': gui.intensity,
            'exposure': gui.exposure,
            'fileName': gui.fileName
        }
        gui.close()
        print("Initializing Acquisition Manager and Devices...")
        manager = None
        try:
            manager = AcquisitionManager(params)
            print("Starting Sequence...")
            manager.runSequence()
            print("Sequence Completed Successfully.")
        except Exception as e:
            print(f"Error during acquisition: {e}")
        finally:
            if manager:
                manager.cleanup()
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Completed")
                msg.setText("Please turn the all key off.")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()


    if hasattr(gui, 'PB2'):
        gui.PB2.clicked.connect(okClicked)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
