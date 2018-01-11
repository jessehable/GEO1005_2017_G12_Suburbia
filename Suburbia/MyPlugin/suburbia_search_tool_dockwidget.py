# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MyPluginDockWidget
                                 A QGIS plugin
 Green Housing Search
                             -------------------
        begin                : 2018-01-09
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Elias Vetter
        email                : vetterelias@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""



import os
from PyQt4.QtCore import pyqtSignal,pyqtSlot
from PyQt4 import QtGui, QtCore, uic
from qgis.core import *
from qgis.networkanalysis import *
from qgis.gui import *

import os.path

import resources

import os
import os.path
import random
import csv
import time

from . import utility_functions as uf


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'suburbia_search_tool_dockwidget_base.ui'))


class MyPluginDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    updateAttribute = QtCore.pyqtSignal(str)


    def __init__(self, iface, parent=None):
        """Constructor."""
        super(MyPluginDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.TabPreferences.setEnabled(False)
        self.TabMetrics.setEnabled(False)

        # define globals
        self.iface = iface
        self.pref =[0,0,0,0]
        self.plugin_dir = os.path.dirname(__file__)
        self.canvas = self.iface.mapCanvas()

        #data
        self.loadDataRotterdam()
        self.iface.projectRead.connect(self.updateLayers)
        self.iface.newProjectCreated.connect(self.updateLayers)
        self.layers = self.iface.legendInterface().layers()



        #input
        self.ButtonConfirm.clicked.connect(self.Confirm)
        self.ButtonExplore.clicked.connect(self.Explore)
        self.ButtonLocate.clicked.connect(self.Locate)
        self.ButtonAdjustPreferences.clicked.connect(self.Confirm)

        #setup GUI features
        self.SuburbiaLogo.setPixmap(QtGui.QPixmap(self.plugin_dir + '/graphics/SuburbiaLogo.png'))

        self.FieldGender.addItems([
            self.tr('Male'),
            self.tr('Female'),
            self.tr('Other'), ])

        self.FieldEducation.addItems([
            self.tr('High School'),
            self.tr('College'),
            self.tr('University'), ])

        self.SliderPeople.valueChanged.connect(self.setPrioritynumbers)
        self.SliderChild.valueChanged.connect(self.setPrioritynumbers)
        self.SliderAccess.valueChanged.connect(self.setPrioritynumbers)
        self.SliderAfford.valueChanged.connect(self.setPrioritynumbers)





    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

#######
#    Visulisation
#######
    def setPrioritynumbers(self):
        self.PriorityPeople.setNum(self.SliderPeople.value())
        self.PriorityChild.setNum(self.SliderChild.value())
        self.PriorityAccess.setNum(self.SliderAccess.value())
        self.PriorityAfford.setNum(self.SliderAfford.value())

    def displayContinuousStyle(self, attribute, layer):
        # ramp
        display_settings = {}
        # define the interval type and number of intervals
        # EqualInterval = 0; Quantile  = 1; Jenks = 2; StdDev = 3; Pretty = 4;
        display_settings['interval_type'] = 0
        display_settings['intervals'] = 5
        # define the line width
        display_settings['line_width'] = 0.5
        ramp = QgsVectorGradientColorRampV2(QtGui.QColor(0, 0, 255, 255), QtGui.QColor(255, 0, 0, 255), False)
        # any other stops for intermediate colours for greater control. can be edited or skipped
        ramp.setStops([QgsGradientStop(0.25, QtGui.QColor(0, 255, 255, 255)),
                       QgsGradientStop(0.5, QtGui.QColor(0, 255, 0, 255)),
                       QgsGradientStop(0.75, QtGui.QColor(255, 255, 0, 255))])
        display_settings['ramp'] = ramp

        uf.updateRenderer(layer, attribute, display_settings)

#######
#    Analysis functions
#######

    def Confirm(self):
        if self.ButtonAgree.isChecked():
            self.TabTerms.setEnabled(False)
            self.TabPreferences.setEnabled(True)
            self.TabMetrics.setEnabled(False)



    def Explore(self):

        layer_explore=  uf.getLegendLayerByName(self.iface, "Rotterdam_Selection")
        self.pref[0] = self.SliderPeople.value()
        self.pref[1] = self.SliderChild.value()
        self.pref[2] = self.SliderAccess.value()
        self.pref[3] = self.SliderAfford.value()
        self.TabPreferences.setEnabled(False)
        self.TabMetrics.setEnabled(True)

        uf.updateField(layer_explore,'B1', self.SliderPeople.value())
        uf.updateField(layer_explore, 'B2', self.SliderChild.value())
        uf.updateField(layer_explore, 'B3', self.SliderAccess.value())
        uf.updateField(layer_explore, 'Score', self.SliderAfford.value())

        #uf.updateField(layer_explore, 'Score', 'B2')

    def Locate(self):
        if not self.EnterPostalCode == "":
            self.pref[0] = self.SliderPeople.value()
            self.pref[1] = self.SliderChild.value()
            self.pref[2] = self.SliderAccess.value()
            self.pref[3] = self.SliderAfford.value()
            self.TabPreferences.setEnabled(False)
            self.TabMetrics.setEnabled(True)



#######
#   Data functions
#######

    def loadDataRotterdam(self, filename=""):
        scenario_open = False
        scenario_file = os.path.join(os.path.dirname(__file__), 'sampledata', '2018-01-09_Suburbia_2016_v3.qgs')
        # check if file exists
        if os.path.isfile(scenario_file):
            self.iface.addProject(scenario_file)
            scenario_open = True
        else:
            last_dir = uf.getLastDir("SDSS")
            new_file = QtGui.QFileDialog.getOpenFileName(self, "", last_dir, "(*.qgs)")
            if new_file:
                self.iface.addProject(unicode(new_file))
                scenario_open = True
        if scenario_open:
            self.updateLayers()

    def updateLayers(self):
        layers = uf.getLegendLayers(self.iface, 'all', 'all')
        if layers:
            layer_names = uf.getLayersListNames(layers)
            self.setSelectedLayer()
        else:
            self.clearChart()

    def baseAttributes(self):
        # get summary of the attribute
        layer = uf.getLegendLayerByName(self.iface, "Rotterdam_gridStatistics")
        summary = []
        self.scenarioAttributes["Rotterdam"] = summary
        # send this to the table
        self.clearTable()
        self.updateTable()

    def setSelectedLayer(self):
        layer_name = "2018-01-09_Rotterdam Selection"
        layer = uf.getLegendLayerByName(self.iface, layer_name)
        self.updateAttributes(layer)

    def updateAttributes(self, layer):
        if layer:
            fields = uf.getNumericFieldNames(layer)

            if fields:
                # send list to the report list window
                print






