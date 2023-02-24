from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

class RectROI(pg.RectROI):

    updated = QtCore.pyqtSignal()

    def __init__(self, pos, size, image_widget) -> None:
        super(RectROI, self).__init__(pos, size)

        self.image_widget = image_widget
        self.controller = ROIController(roi=self)
        self.bounds = dict((dim_lbl, None) for dim_lbl in image_widget.dim_labels)

        self.addScaleHandle((0, 0), (1, 1))
        self.addScaleHandle((0, 1), (1, 0))
        self.addScaleHandle((1, 0), (0, 1))
        self.show()

        self.sigRegionChanged.connect(self._update_bounds_from_roi)
        self.controller.updated.connect(self._update_roi)
        self.image_widget.direction_changed.connect(self._center)
        self._center()

    def _set_bounds(self, bounds_dict: dict) -> None:
        dim_order = self.image_widget.current_dim_order

        if set(bounds_dict.keys()) == set(self.bounds.keys()):
            for i, dim in zip(range(3), dim_order):
                dim_bounds = bounds_dict[dim]
                if dim_bounds is None or (len(dim_bounds) == 2 and dim_bounds[-1] >= dim_bounds[0]):
                    self.bounds.update({dim: dim_bounds})

        print(f"SELF.BOUNDS({dim_order}): {self.bounds}")
                
    def _update_roi(self) -> None:
        x_pos, y_pos, x_size, y_size = None, None, None, None
        dim_order = self.image_widget.current_dim_order
        x_dim, y_dim = dim_order[1], dim_order[2]

        x_pos, y_pos = self.bounds[x_dim][0], self.bounds[y_dim][0]
        x_size = self.bounds[x_dim][1] - x_pos
        y_size = self.bounds[y_dim][1] - y_pos

        self.setPos(pos=(x_pos, y_pos))
        self.setSize(size=(x_size, y_size))

    def _update_bounds_from_roi(self) -> None:
        dim_order = self.image_widget.current_dim_order
        bounds = {}

        h_2, h_1 = self.getSceneHandlePositions()[:2]
        pos_1 = self.mapSceneToParent(h_1[1])
        pos_2 = self.mapSceneToParent(h_2[1])
        
        x_1, y_1 = pos_1.x(), pos_1.y()
        x_2, y_2 = pos_2.x(), pos_2.y()

        for i, dim in zip(range(3), dim_order):
            if i == 0:
                bounds.update({dim: None})
            elif i == 1:
                bounds.update({dim: (x_1, x_2)})
            else:
                bounds.update({dim: (y_1, y_2)})

        self._set_bounds(bounds_dict=bounds)
        self.controller._update_controller_bounds_from_roi()

    def _center(self) -> None:
        coords = self.image_widget.current_coords
        dim_order = self.image_widget.current_dim_order
        bounds = {}

        for dim, dim_coords in zip(dim_order, coords):
            bounds.update({dim: (dim_coords[0], dim_coords[-1])})

        self._set_bounds(bounds_dict=bounds)
        self._update_roi()
        self.controller._update_controller_bounds_from_roi()

        self.image_widget.image_widget.autoRange()

    def _remove(self) -> None:
        self.controller.deleteLater()
        self.image_widget._remove_roi(self)

class ROIController(QtWidgets.QWidget):

    updated = QtCore.pyqtSignal()

    def __init__(self, roi) -> None:
        super(ROIController, self).__init__()

        self.roi = roi
        self.dims = roi.image_widget.dim_labels

        self.roi_type_lbl = QtWidgets.QLabel("Rectangular ROI")
        self.roi_type_lbl.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.show_roi_chkbx = QtWidgets.QCheckBox("Show")
        self.show_roi_chkbx.setChecked(True)
        self.center_roi_btn = QtWidgets.QPushButton("Center")
        self.remove_roi_btn = QtWidgets.QPushButton("Remove")
        self.output_type_cbx = QtWidgets.QComboBox()
        self.output_type_lbl = QtWidgets.QLabel("Output:")
        self.output_type_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.show_output_btn = QtWidgets.QPushButton("Show Output")
        self.color_btn = pg.ColorButton()

        self.dim_lbls = [QtWidgets.QLabel(f"{dim}:") for dim in self.dims]
        for lbl in self.dim_lbls:
            lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.min_sbxs = [QtWidgets.QDoubleSpinBox() for dim in self.dims]
        self.max_sbxs = [QtWidgets.QDoubleSpinBox() for dim in self.dims]

        for sbx in self.min_sbxs + self.max_sbxs:
            sbx.setDecimals(5)
            sbx.setSingleStep(0.1)
            sbx.setRange(-1000, 1000)
        
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.roi_type_lbl, 0, 0, 1, 4)
        self.layout.addWidget(self.show_roi_chkbx, 0, 4, 1, 3)
        self.layout.addWidget(self.color_btn, 1, 0, 1, 7)
        self.layout.addWidget(self.center_roi_btn, 2, 0, 1, 7)
        self.layout.addWidget(self.remove_roi_btn, 3, 0, 1, 7)
        self.layout.addWidget(self.dim_lbls[0], 4, 0, 1, 1)
        self.layout.addWidget(self.dim_lbls[1], 5, 0, 1, 1)
        self.layout.addWidget(self.dim_lbls[2], 6, 0, 1, 1)
        self.layout.addWidget(self.min_sbxs[0], 4, 1, 1, 3)
        self.layout.addWidget(self.min_sbxs[1], 5, 1, 1, 3)
        self.layout.addWidget(self.min_sbxs[2], 6, 1, 1, 3)
        self.layout.addWidget(self.max_sbxs[0], 4, 4, 1, 3)
        self.layout.addWidget(self.max_sbxs[1], 5, 4, 1, 3)
        self.layout.addWidget(self.max_sbxs[2], 6, 4, 1, 3)
        '''self.layout.addWidget(self.output_type_lbl, 1, 0, 1, 2)
        self.layout.addWidget(self.output_type_cbx, 1, 2, 1, 2)
        self.layout.addWidget(self.show_output_btn, 1, 4, 1, 2)'''

        for i in range(6):
            self.layout.setColumnStretch(i, 1)

        self.layout.setRowStretch(7, 5)

        self.show_roi_chkbx.stateChanged.connect(self._toggle_roi_visibility)
        self.center_roi_btn.clicked.connect(self.roi._center)
        self.remove_roi_btn.clicked.connect(self.roi._remove)
        for sbx in self.min_sbxs + self.max_sbxs:
            sbx.editingFinished.connect(self._update_roi_from_controller_bounds)

    def _toggle_roi_visibility(self):
        if self.show_roi_chkbx.isChecked():
            self.roi.show()
        else:
            self.roi.hide()

    def _validate_controller_bounds(self):
        for i in range(3):
            if self.min_sbxs[i].value() > self.max_sbxs[i].value():
                self.min_sbxs[i].setValue(self.max_sbxs[i].value())

    def _update_controller_bounds_from_roi(self):
        bounds = self.roi.bounds
        dim_order = self.roi.image_widget.current_dim_order
        
        for dim, min_sbx, max_sbx in zip(self.dims, self.min_sbxs, self.max_sbxs):
            dim_bounds = bounds[dim]
            if dim_bounds is None or dim_order.index(dim) == 0:
                min_sbx.setValue(0)
                min_sbx.setEnabled(False)
                max_sbx.setValue(0)
                max_sbx.setEnabled(False)
            else:
                min_sbx.setEnabled(True)
                max_sbx.setEnabled(True)
                min_sbx.setValue(dim_bounds[0])
                max_sbx.setValue(dim_bounds[-1])

    def _update_roi_from_controller_bounds(self):
        self._validate_controller_bounds()

        bounds = {}
        for i in range(3):
            bounds.update({self.dims[i]: (self.min_sbxs[i].value(), self.max_sbxs[i].value())})

        self.roi._set_bounds(bounds)
        self.roi._update_roi()
        
    def _remove_roi(self):
        ...