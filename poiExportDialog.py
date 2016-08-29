# -*- coding: utf-8 -*-
"""
/***************************************************************************
 POIExport
    A QIGS plugin for exporting GPS Points of Interest
                              -------------------
        begin                : 2016-08-29
        copyright            : (C) 2016 by
                               C. Hamilton
        email                : adenaculture@gmail.com
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
from PyQt4 import uic, QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *
from xml.sax.saxutils import escape, unescape
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'poiexportdialog.ui'))

        
class POIExportDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, iface):
        """Initialize the QGIS POI (Points of Interest) dialog window."""
        super(POIExportDialog, self).__init__(iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Export")
        self.outputFormatComboBox.addItems(['GPX', 'Garmin CSV'])
        
        self.fileButton.clicked.connect(self.getDirPath)
        self.vectorComboBox.activated.connect(self.initLayerFields)
        self.categoryComboBox.activated.connect(self.setEnabled)
        self.poiNameComboBox.activated.connect(self.setEnabled)
        self.epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        
        
    def accept(self):
        """Called when the OK button has been pressed."""
        if self.vectorComboBox.count() == 0:
            return
        # Read and get the state of all of the POI widgets
        base = self.fileLineEdit.text()
        categoryCol = self.categoryComboBox.currentIndex()
        poiNameCol = self.poiNameComboBox.currentIndex()
        descriptionCol = self.descriptionComboBox.currentIndex()
        defaultCategory = self.defaultCategoryLineEdit.text()
        defaultPOI = self.defaultPOILineEdit.text()
        
        outputFormat = self.outputFormatComboBox.currentIndex()
        
        # Set up a coordinate transform to make sure the output is always epsg:4326 
        layerCRS = self.selectedLayer.crs()
        self.transform4326 = QgsCoordinateTransform(layerCRS, self.epsg4326)
        
        
        if outputFormat == 0: # GPX output formt
            if categoryCol == 0:
                # Process the input data to one output category as GPX format
                self.processSingleCatGPX(self.selectedLayer, base, defaultCategory, poiNameCol, defaultPOI, descriptionCol)
            else:
                # The user has selected a column to be used as POI categories. This will create
                # multiple files with the names coming from this category. Output is GPX
                categoryName = unicode(self.categoryComboBox.currentText())
                self.processCatGPX(self.selectedLayer, base, categoryCol, categoryName, poiNameCol, defaultPOI, descriptionCol)
        else: # CSV output formt
            if categoryCol == 0:
                # Process the input data to one output category as CSV format
                self.processSingleCat(self.selectedLayer, base, defaultCategory, poiNameCol, defaultPOI, descriptionCol)
            else:
                # The user has selected a column to be used as POI categories. This will create
                # multiple files with the names coming from this category. Output is CSV
                categoryName = unicode(self.categoryComboBox.currentText())
                self.processCat(self.selectedLayer, base, categoryCol, categoryName, poiNameCol, defaultPOI, descriptionCol)
        QDialog.accept(self)
        
    def processSingleCat(self, layer, base, cat, poiNameCol, defaultPOI, descCol):
        """ Output the POIs into a CSV file with only one category. Note that it
            quotes the text."""
        filename = "{}.csv".format(cat)
        path = os.path.join(base, filename)
        defaultPOI = unicode(defaultPOI).replace(u'"', u'""')
        fp = open(path, "w")
        for f in layer.getFeatures(  ):
            point = self.transform4326.transform(f.geometry().asPoint())
            if poiNameCol == 0:
                # Format: longitude, latitude, default name
                line = u'{},{},"{}"'.format(point.x(), point.y(),defaultPOI)
            else:
                # Format: longitude, latitude, name from the specified column
                line = u'{},{},"{}"'.format(point.x(), point.y(),unicode(f[poiNameCol-1]).replace(u'"',u'""'))
            fp.write(line)
            if descCol > 0:
                # Add: , description to the line
                if f[descCol-1]:
                    line = u',"{}"'.format(unicode(f[descCol-1]).replace(u'"',u'""'))
                else:
                    line = u',""'
                fp.write(line)
            fp.write('\n')
        fp.close()
            
    def processCat(self, layer, base, categoryCol, categoryName, poiNameCol, defaultPOI, descCol):
        """ Output the POIs into multiple CSV files based on the unique categories specified by 
            categoryCol."""
        categories = layer.uniqueValues(categoryCol-1)
        defaultPOI = unicode(defaultPOI).replace(u'"', u'""')
        for cat in categories:
            if cat is None or str(cat) is 'NULL':
                continue
            cat = unicode(cat)
            filename = u"{}.csv".format(cat)
            path = os.path.join(base, filename)
            fp = open(path, "w")
            filter = u'"{}" = \'{}\''.format(categoryName, cat)
            request = QgsFeatureRequest().setFilterExpression( filter )
            for f in layer.getFeatures( request ):
                point = self.transform4326.transform(f.geometry().asPoint())
                if poiNameCol == 0:
                    # Format: longitude, latitude, default name
                    line = u'{},{},"{}"'.format(point.x(), point.y(),defaultPOI)
                else:
                    line = u'{},{},"{}"'.format(point.x(), point.y(),unicode(f[poiNameCol-1]).replace(u'"',u'""'))
                fp.write(line)
                if descCol > 0:
                    if f[descCol-1]:
                        line = u',"{}"'.format(unicode(f[descCol-1]).replace(u'"',u'""'))
                    else:
                        line = u',""'
                    fp.write(line)
                fp.write('\n')
            fp.close()
        
    def processSingleCatGPX(self, layer, base, cat, poiNameCol, defaultPOI, descCol):
        """ Output the POIs into a GPX file with only one category. Note that it
            quotes the text."""
        filename = "{}.gpx".format(cat)
        path = os.path.join(base, filename)
        # Make sure the defaultPOI string is XML friendly
        defaultPOI = escape( unescape( unicode(defaultPOI), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})

        fp = open(path, "w")
        fp.write('<?xml version="1.0" encoding="utf-8"?><gpx version="1.1" creator="QGIS POI Export" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')

        for f in layer.getFeatures(  ):
            point = self.transform4326.transform(f.geometry().asPoint())
            line = u'<wpt lat="{}" lon="{}">\n'.format(point.y(), point.x())
            fp.write(line)
            if poiNameCol == 0:
                line = u'<name>{}</name>\n'.format(defaultPOI)
            else:
                # Make sure the name string is XML friendly
                name = escape( unescape( unicode(f[poiNameCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                line = u'<name>{}</name>\n'.format(name)
            fp.write(line)
            if descCol > 0:
                if f[descCol-1]:
                    # Make sure the description string is XML friendly
                    desc = escape( unescape( unicode(f[descCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                    line = u'<cmt>{}</cmt>\n'.format(desc)
                    fp.write(line)
                    line = u'<desc>{}</desc>\n'.format(desc)
                    fp.write(line)
            fp.write('</wpt>\n')
        fp.write('</gpx>\n')
        fp.close()
            
    def processCatGPX(self, layer, base, categoryCol, categoryName, poiNameCol, defaultPOI, descCol):
        """ Output the POIs into multiple GPX files based on the unique categories specified by 
            categoryCol."""
        categories = layer.uniqueValues(categoryCol-1)
        defaultPOI = escape( unescape( unicode(defaultPOI), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
        for cat in categories:
            if cat is None or str(cat) is 'NULL':
                continue
            cat = unicode(cat)
            filename = u"{}.gpx".format(cat)
            path = os.path.join(base, filename)
            fp = open(path, "w")
            fp.write('<?xml version="1.0" encoding="utf-8"?><gpx version="1.1" creator="QGIS POI Export" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')
            filter = u'"{}" = \'{}\''.format(categoryName, cat)
            request = QgsFeatureRequest().setFilterExpression( filter )
            for f in layer.getFeatures( request ):
                point = self.transform4326.transform(f.geometry().asPoint())
                line = u'<wpt lat="{}" lon="{}">\n'.format(point.y(), point.x())
                fp.write(line)
                if poiNameCol == 0:
                    line = u'<name>{}</name>\n'.format(defaultPOI)
                else:
                    name = escape( unescape( unicode(f[poiNameCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                    line = u'<name>{}</name>\n'.format(name)
                fp.write(line)
                if descCol > 0:
                    if f[descCol-1]:
                        desc = escape( unescape( unicode(f[descCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                        line = u'<cmt>{}</cmt>\n'.format(desc)
                        fp.write(line)
                        line = u'<desc>{}</desc>\n'.format(desc)
                        fp.write(line)
                fp.write('</wpt>\n')
            fp.write('</gpx>\n')
            fp.close()

    def getDirPath(self):
        folder = askForFolder(self)
        if not folder:
            return
        self.fileLineEdit.setText(folder)

    def showEvent(self, event):
        """ Initialize the Dialog widgets when it is first displyaed """
        super(POIExportDialog, self).showEvent(event)
        self.populateLayerListComboBox()
        
    def populateLayerListComboBox(self):
        """ Populate the QComboBox with a list of all the QGIS point vector layers."""
        layers = self.iface.legendInterface().layers()
        self.vectorComboBox.clear()
        
        for layer in layers:
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QGis.Point:
                self.vectorComboBox.addItem(layer.name(), layer)

        self.initLayerFields()

    def initLayerFields(self):
        """ Populate the QComboBox fields box with a list of all the fields in the selected
            points vector layer"""
        self.categoryComboBox.clear()
        self.poiNameComboBox.clear()
        self.descriptionComboBox.clear()
        if self.vectorComboBox.count() == 0:
            return
        self.selectedLayer = self.vectorComboBox.itemData(self.vectorComboBox.currentIndex())
        
        self.categoryComboBox.addItem(u'[Use Default Category]', -1)
        self.poiNameComboBox.addItem(u'[Use Default POI Name]', -1)
        self.descriptionComboBox.addItem(u'[Select an Optional POI Description]', -1)
        for idx, field in enumerate(self.selectedLayer.fields()):
            self.categoryComboBox.addItem(field.name(), idx)
            self.poiNameComboBox.addItem(field.name(), idx)
            self.descriptionComboBox.addItem(field.name(), idx)
        
        self.setEnabled()
        
    def setEnabled(self):
        """ Depending on the settings some widgets are enabled and some are disabled. """
        categoryCol = self.categoryComboBox.currentIndex()
        poiNameCol = self.poiNameComboBox.currentIndex()
        self.defaultCategoryLineEdit.setEnabled(categoryCol == 0)
        self.defaultPOILineEdit.setEnabled(poiNameCol == 0)

    
LAST_PATH = "LastPath"
def askForFolder(parent, name="POIExportPath"):
    path = getSetting(LAST_PATH, name)
    folder =  QFileDialog.getExistingDirectory(parent, "Select POI folder", path)
    if folder:
        setSetting(LAST_PATH, name, folder)
    return folder

def setSetting(namespace, name, value):
    settings = QSettings()
    settings.setValue(namespace + "/" + name, value)

def getSetting(namespace, name):
    v = QSettings().value(namespace + "/" + name, None)
    if isinstance(v, QPyNullVariant):
        v = None
    return v