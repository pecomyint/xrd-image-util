"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

from PyQt5 import QtWidgets
import pyqtgraph as pg


'''
Basic steps for a temporary window
app = pg.mkQApp()
w = QtWidgets.QWidget()
data = ...
iv = pg.ImageView()
iv.setImage(data)
l = QtWidgets.QGridLayout()
l.addWidget(iv)
w.setLayout(l)
w.raise_()
w.show()
app.exec_()
'''
