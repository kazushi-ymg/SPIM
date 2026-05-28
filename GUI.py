from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QFileDialog, QLabel, QLineEdit, QCheckBox, QComboBox, QSpinBox, QDoubleSpinBox, QGridLayout, QVBoxLayout, QPushButton

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()

        labelVector = ["Emission filter", "Acquisition", "Excitation", "Intensity [mW]", "Exposure [msec]"]
        emFilterVector = ["525-50", "595-50", "706-95"]

        self.setWindowTitle("Set Parameters")
        layout = QVBoxLayout()
        layout_odPath = QGridLayout()
        layout_ChunkSize = QGridLayout()
        layout_acqParams = QGridLayout()

        self.folderPath = ""
        self.odLabel = QLabel("Output Directory")
        self.od = QLineEdit(self)
        self.od.setMaxLength(1000)
        self.od.setText("C:/Users/kazushi/Pictures")
        self.refButton = QPushButton("Browse")
        self.refButton.pressed.connect(self.getPath)
        self.fnLabel = QLabel("File Name (prefix)")
        self.fn = QLineEdit(self)
        self.fn.setMaxLength(500)
        self.fn.setText("img")
        layout_odPath.addWidget(self.odLabel, 0, 0)
        layout_odPath.addWidget(self.od, 0, 1)
        layout_odPath.addWidget(self.refButton, 0, 2)
        layout_odPath.addWidget(self.fnLabel, 1, 0)
        layout_odPath.addWidget(self.fn, 1, 1)
        layout.addLayout(layout_odPath)

        self.csLabel = QLabel("File Chunk Size")
        self.cs = QLineEdit(self)
        self.cs.setText("100")
        self.cs.setMaximumSize(75, 50)
        self.svLabel = QLabel("Sample Stage Velocity [mm / sec]")
        self.sv = QDoubleSpinBox(self)
        self.sv.setRange(0.001, 1)
        self.sv.setValue(0.10)
        self.sv.setSingleStep(0.10)
        self.sv.setMaximumSize(75, 50)
        self.diLabel = QLabel("Move Distance [mm]")
        self.di = QDoubleSpinBox(self)
        self.di.setRange(0.01, 30)
        self.di.setValue(12)
        self.di.setSingleStep(0.10)
        self.di.setMaximumSize(75, 50)
        self.ssLabel = QLabel("Cuvette Size")
        self.ss = QComboBox()
        self.ss.addItems(["10 mm", "20 mm"])
        self.ss.setCurrentIndex(1)
        self.riLabel = QLabel("Sample Refractive Index")
        self.ri = QDoubleSpinBox(self)
        self.ri.setRange(1.00, 1.60)
        self.ri.setValue(1.52)
        self.ri.setSingleStep(0.01)
        self.ri.setMaximumSize(75, 50)
        self.znLabel = QLabel("Z Position Numbers")
        self.zn = QSpinBox()
        self.zn.setRange(1, 3)
        self.zn.setValue(1)
        self.zn.setSingleStep(1)
        self.zn.setMaximumSize(75, 50)
        self.zpLabel = QLabel("Z Initial Shift [mm]")
        self.zp = QDoubleSpinBox(self)
        self.zp.setRange(0.01, 30)
        self.zp.setValue(12)
        self.zp.setSingleStep(0.10)
        self.zp.setMaximumSize(75, 50)
        self.ziLabel = QLabel("Z Interval [mm]")
        self.zi = QDoubleSpinBox(self)
        self.zi.setRange(0.001, 10)
        self.zi.setValue(5)
        self.zi.setSingleStep(0.10)
        self.zi.setMaximumSize(75, 50)
        self.emptyLabel = QLabel("                             ")
        layout_ChunkSize.addWidget(self.csLabel, 0, 0)
        layout_ChunkSize.addWidget(self.cs, 0, 1)
        layout_ChunkSize.addWidget(self.emptyLabel, 0, 2)
        layout_ChunkSize.addWidget(self.svLabel, 1, 0)
        layout_ChunkSize.addWidget(self.sv, 1, 1)
        layout_ChunkSize.addWidget(self.diLabel, 1, 3)
        layout_ChunkSize.addWidget(self.di, 1, 4)
        layout_ChunkSize.addWidget(self.ssLabel, 2, 0)
        layout_ChunkSize.addWidget(self.ss, 2, 1)
        layout_ChunkSize.addWidget(self.riLabel, 2, 3)
        layout_ChunkSize.addWidget(self.ri, 2, 4)        
        layout_ChunkSize.addWidget(self.znLabel, 3, 0)
        layout_ChunkSize.addWidget(self.zn, 3, 1)
        layout_ChunkSize.addWidget(self.zpLabel, 4, 0)
        layout_ChunkSize.addWidget(self.zp, 4, 1)
        layout_ChunkSize.addWidget(self.ziLabel, 4, 3)
        layout_ChunkSize.addWidget(self.zi, 4, 4)
        layout_ChunkSize.addWidget(self.emptyLabel, 5, 5)
        layout.addLayout(layout_ChunkSize)

        self.labels = [QLabel(self) for i in range(5)]
        for i, label in enumerate(self.labels):
            label.setText(labelVector[i])
            layout_acqParams.addWidget(label, i, 0)

        self.emFilters = [QLabel(self) for i in range(3)]
        for i, emFilter in enumerate(self.emFilters):
            emFilter.setText(emFilterVector[i])
            layout_acqParams.addWidget(emFilter, 0, (i + 1))

        self.subFilters = [QLineEdit(self) for i in range(3)]
        for i, subFilter in enumerate(self.subFilters):
            subFilter.setPlaceholderText("Enter the filter info")
            subFilter.setMaxLength(12)
            layout_acqParams.addWidget(subFilter, 0, (i + len(emFilterVector) + 1))

        self.acqs = [QComboBox(self) for i in range(6)]
        for i, combobox in enumerate(self.acqs):
            combobox.addItems(["No", "Yes"])
            layout_acqParams.addWidget(combobox, 1, (i + 1))

        self.laserlines = [QComboBox(self) for i in range(6)]
        for i, combobox in enumerate(self.laserlines):
            combobox.addItems(["488 nm", "561 nm", "640 nm"])
            if i == 1:
                combobox.setCurrentIndex(1)
            elif i == 2:
                combobox.setCurrentIndex(2)
            elif i == 3:
                combobox.setCurrentIndex(1)

            combobox.currentIndexChanged.connect(lambda index, col=i: self.updatePowerLimit(col))
            layout_acqParams.addWidget(combobox, 2, (i + 1))

        self.dspinboxes = [QDoubleSpinBox(self) for i in range(6)]
        for i, dspinbox in enumerate(self.dspinboxes):             
            dspinbox.setSingleStep(0.10)
            dspinbox.setValue(10.0)
            layout_acqParams.addWidget(dspinbox, 3, (i + 1))
            self.updatePowerLimit(i)

        self.spinboxes = [QSpinBox(self) for i in range(6)]
        for i, spinbox in enumerate(self.spinboxes):
            spinbox.setRange(33, 10000)
            spinbox.setValue(200)
            spinbox.setSingleStep(10)
            layout_acqParams.addWidget(spinbox, 4, (i + 1))

        self.PB1 = QPushButton("Cancel")
        self.PB1.pressed.connect(self.close)
        self.PB2 = QPushButton("OK")
        self.PB2.pressed.connect(self.returnValues)

        layout_acqParams.addWidget(self.PB1, 5, 5)
        layout_acqParams.addWidget(self.PB2, 5, 6)

        layout.addLayout(layout_acqParams)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

    def getPath(self):
        path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if path:
            self.folderPath = path
            self.od.setText(self.folderPath)

    def updatePowerLimit(self, col):
        laser = self.laserlines[col].currentText()
        target = self.dspinboxes[col]

        limits = {
            "488 nm": 60.0,
            "561 nm": 25.0,
            "640 nm": 100.0
        }
        newMax = limits.get(laser, 50.0)
        
        target.setRange(0.0, newMax)
        
        if target.value() > newMax:
            target.setValue(newMax)

    def selectSwitch(self):
        if self.ss1.clicked():
            self.ss1.setChecked(True)
            self.ss2.setChecked(False)
        elif self.ss2.clicked():
            self.ss1.setChecked(False)
            self.ss2.setChecked(True)

    def returnValues(self):
        self.outputPath = self.od.text()
        self.fileName = self.fn.text()
        self.chunkSize = int(self.cs.text())
        self.stageVelocity = self.sv.value()
        self.distance = self.di.value()
        self.sampleSize = self.ss.currentIndex()
        self.refractiveIndex = self.ri.value()
        self.zNumber = self.zn.value()
        self.zInitialPosition = self.zp.value()
        self.zInterval = self.zi.value()
        self.filter = []
        self.acqFlag = []
        self.laser = []
        self.intensity = []
        self.exposure = []
        for i in range(6):
            if i >= len(self.emFilters):
                self.filter.append(self.subFilters[i - len(self.emFilters)].text())
            else:
                self.filter.append(self.emFilters[i].text())

            if self.acqs[i].currentText() == "Yes":
                self.acqFlag.append(1)
            else:
                self.acqFlag.append(0)

            if self.laserlines[i].currentText() == "488 nm":
                self.laser.append(1)
            elif self.laserlines[i].currentText() == "561 nm":
                self.laser.append(2)
            else:
                self.laser.append(3)

            self.intensity.append(self.dspinboxes[i].value())
            self.exposure.append(self.spinboxes[i].value())
