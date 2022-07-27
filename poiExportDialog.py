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
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSettings, QUrl
from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QDialogButtonBox

from qgis.core import Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsFeatureRequest, QgsVectorLayer, QgsMapLayerProxyModel, QgsProject
from xml.sax.saxutils import escape, unescape
from .colorhash import ColorHash
import webbrowser


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'poiexportdialog.ui'))

        
class POIExportDialog(QDialog, FORM_CLASS):
    def __init__(self, iface):
        """Initialize the QGIS POI (Points of Interest) dialog window."""
        super(POIExportDialog, self).__init__(iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Export")
        self.outputFormatComboBox.addItems(['GPX', 'Garmin CSV'])
        
        self.fileButton.clicked.connect(self.getDirPath)
        self.vectorComboBox.layerChanged.connect(self.initLayerFields)
        self.vectorComboBox.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.categoryComboBox.activated.connect(self.setEnabled)
        self.visualComboBox.activated.connect(self.setEnabled)
        self.poiNameComboBox.activated.connect(self.setEnabled)
        self.epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        self.buttonBox.button(QDialogButtonBox.Help).clicked.connect(self.help)

    def help(self):
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)
        
        
    def accept(self):
        """Called when the OK button has been pressed."""
        if self.vectorComboBox.count() == 0:
            self.iface.messageBar().pushMessage("", "No point vector layers are available", level=Qgis.Warning, duration=3)
            return
        # Read and get the state of all of the POI widgets
        base = self.fileLineEdit.text()
        categoryCol = self.categoryComboBox.currentIndex()
        poiNameCol = self.poiNameComboBox.currentIndex()
        visualCol = self.visualComboBox.currentIndex()
        descriptionCol = self.descriptionComboBox.currentIndex()
        commentCol = self.commentComboBox.currentIndex()
        linkCol = self.webLinkComboBox.currentIndex()
        symCol = self.symbolComboBox.currentIndex()
        defaultCategory = self.defaultCategoryLineEdit.text()
        defaultPOI = self.defaultPOILineEdit.text()
        
        outputFormat = self.outputFormatComboBox.currentIndex()
        
        # Set up a coordinate transform to make sure the output is always epsg:4326 
        layerCRS = self.selectedLayer.crs()
        self.transform4326 = QgsCoordinateTransform(layerCRS, self.epsg4326, QgsProject.instance())
        
        
        if outputFormat == 0: # GPX output formt
            if categoryCol == 0:
                # Process the input data to one output category as GPX format
                self.processSingleCatGPX(self.selectedLayer, base, defaultCategory, poiNameCol, defaultPOI, descriptionCol, commentCol, linkCol, symCol, visualCol)
            else:
                # The user has selected a column to be used as POI categories. This will create
                # multiple files with the names coming from this category. Output is GPX
                categoryName = str(self.categoryComboBox.currentText())
                self.processCatGPX(self.selectedLayer, base, categoryCol, categoryName, poiNameCol, defaultPOI, descriptionCol, commentCol, linkCol, symCol, visualCol)
        else: # CSV output formt
            if categoryCol == 0:
                # Process the input data to one output category as CSV format
                self.processSingleCat(self.selectedLayer, base, defaultCategory, poiNameCol, defaultPOI, descriptionCol, commentCol, linkCol, symCol, visualCol)
            else:
                # The user has selected a column to be used as POI categories. This will create
                # multiple files with the names coming from this category. Output is CSV
                categoryName = str(self.categoryComboBox.currentText())
                self.processCat(self.selectedLayer, base, categoryCol, categoryName, poiNameCol, defaultPOI, descriptionCol, commentCol, linkCol, symCol, visualCol)
        QDialog.accept(self)
        
    def processSingleCat(self, layer, base, cat, poiNameCol, defaultPOI, descCol, cmtCol, linkCol, symCol, visualCol):
        """ Output the POIs into a CSV file with only one category. Note that it
            quotes the text."""
        filename = "{}.csv".format(cat)
        path = os.path.join(base, filename)
        defaultPOI = str(defaultPOI).replace('"', '""')
        fp = open(path, "w", encoding="utf-8")
        for f in layer.getFeatures(  ):
            point = self.transform4326.transform(f.geometry().asPoint())
            if poiNameCol == 0:
                # Format: longitude, latitude, default name
                line = '{},{},"{}"'.format(point.x(), point.y(),defaultPOI)
            else:
                # Format: longitude, latitude, name from the specified column
                line = '{},{},"{}"'.format(point.x(), point.y(),str(f[poiNameCol-1]).replace('"','""'))
            fp.write(line)
            if cmtCol > 0:
                # Add: , comment to the line
                if f[cmtCol-1]:
                    line = ',"{}"'.format(str(f[cmtCol-1]).replace('"','""'))
                else:
                    line = ',""'
                fp.write(line)
            if descCol > 0:
                # Add: , description to the line
                if f[descCol-1]:
                    line = ',"{}"'.format(str(f[descCol-1]).replace('"','""'))
                else:
                    line = ',""'
                fp.write(line)
            if linkCol > 0:
                link = str(f[linkCol-1]).strip()
                if link and link != 'NULL':
                    line = ',"{}"'.format(link)
                else:
                    line = ',""'
                fp.write(line)
            if symCol > 0:
                sym = str(f[symCol-1]).strip()
                if sym and sym != 'NULL':
                    line = ',"{}"'.format(sym)
                else:
                    line = ',""'
                fp.write(sym)
            if visualCol > 0:
                # Add: , comment to the line
                if f[visualCol-1]:
                    line = ',"{}"'.format(str(f[visualCol-1]).replace('"','""'))
                else:
                    line = ',""'
                fp.write(line)
            fp.write('\n')  
        fp.close()
            
    def processCat(self, layer, base, categoryCol, categoryName, poiNameCol, defaultPOI, descCol, cmtCol, linkCol, symCol, visualCol):
        """ Output the POIs into multiple CSV files based on the unique categories specified by 
            categoryCol."""
        categories = layer.uniqueValues(categoryCol-1)
        defaultPOI = str(defaultPOI).replace('"', '""')
        for cat in categories:
            if cat is None or str(cat) is 'NULL':
                continue
            cat = str(cat)
            filename = "{}.csv".format(cat)
            path = os.path.join(base, filename)
            fp = open(path, "w", encoding="utf-8")
            filter = '"{}" = \'{}\''.format(categoryName, cat)
            request = QgsFeatureRequest().setFilterExpression( filter )
            for f in layer.getFeatures( request ):
                point = self.transform4326.transform(f.geometry().asPoint())
                if poiNameCol == 0:
                    # Format: longitude, latitude, default name
                    line = '{},{},"{}"'.format(point.x(), point.y(),defaultPOI)
                else:
                    line = '{},{},"{}"'.format(point.x(), point.y(),str(f[poiNameCol-1]).replace('"','""'))
                fp.write(line)
                if cmtCol > 0:
                    if f[cmtCol-1]:
                        line = ',"{}"'.format(str(f[cmtCol-1]).replace('"','""'))
                    else:
                        line = ',""'
                    fp.write(line)
                if descCol > 0:
                    if f[descCol-1]:
                        line = ',"{}"'.format(str(f[descCol-1]).replace('"','""'))
                    else:
                        line = ',""'
                    fp.write(line)
                if linkCol > 0:
                    link = str(f[linkCol-1]).strip()
                    if link and link != 'NULL':
                        line = ',"{}"'.format(link)
                    else:
                        line = ',""'
                    fp.write(line)
                if symCol > 0:
                    sym = str(f[symCol-1]).strip()
                    if sym and sym != 'NULL':
                        line = ',"{}"'.format(sym)
                    else:
                        line = ',""'
                    fp.write(sym)
                if visualCol > 0:
                    if f[visualCol-1]:
                        line = ',"{}"'.format(str(f[visualCol-1]).replace('"','""'))
                    else:
                        line = ',""'
                    fp.write(line)              
                fp.write('\n')
            fp.close()
        
    def processSingleCatGPX(self, layer, base, cat, poiNameCol, defaultPOI, descCol, cmtCol, linkCol, symCol, visualCol):
        """ Output the POIs into a GPX file with only one category. Note that it
            quotes the text."""
        filename = "{}.gpx".format(cat)
        path = os.path.join(base, filename)
        # Make sure the defaultPOI string is XML friendly
        defaultPOI = escape( unescape( str(defaultPOI), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})

        fp = open(path, "w", encoding="utf-8")
        fp.write('<?xml version="1.0" encoding="utf-8"?><gpx version="1.1" creator="QGIS POI Export" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')

        for f in layer.getFeatures(  ):
            point = self.transform4326.transform(f.geometry().asPoint())
            line = '<wpt lat="{}" lon="{}">\n'.format(point.y(), point.x())
            fp.write(line)
            if poiNameCol == 0:
                line = '<name>{}</name>\n'.format(defaultPOI)
            else:
                # Make sure the name string is XML friendly
                name = escape( unescape( str(f[poiNameCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                line = '<name>{}</name>\n'.format(name)
            fp.write(line)
            if cmtCol > 0:
                if f[cmtCol-1]:
                    # Make sure the comment string is XML friendly
                    cmt = escape( unescape( str(f[cmtCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                    line = '<cmt>{}</cmt>\n'.format(cmt)
                    fp.write(line)
            if descCol > 0:
                if f[descCol-1]:
                    # Make sure the description string is XML friendly
                    desc = escape( unescape( str(f[descCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                    line = '<desc>{}</desc>\n'.format(desc)
                    fp.write(line)
            if linkCol > 0:
                link = '{}'.format(f[linkCol-1]).strip()
                if link and link != 'NULL':
                    line = '<link href="{}" />\n'.format(link)
                    fp.write(line)
            if symCol > 0:
                sym = '{}'.format(f[symCol-1]).strip()
                if sym and sym != 'NULL':
                    line = '<sym>{}</sym>\n'.format(sym)
                    fp.write(line)
            if visualCol > 0:
                if f[visualCol-1]:
                    # Make sure the comment string is XML friendly
                    color = escape( unescape( str(f[visualCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                    colorAgence = ColorHash(color)
                    line = '<extensions><color>{}</color></extensions>\n'.format(colorAgence.hex)
                    fp.write(line)
            fp.write('</wpt>\n')
        fp.write('</gpx>\n')
        fp.close()
            
    def processCatGPX(self, layer, base, categoryCol, categoryName, poiNameCol, defaultPOI, descCol, cmtCol, linkCol, symCol, visualCol):
        """ Output the POIs into multiple GPX files based on the unique categories specified by 
            categoryCol."""
        categories = layer.uniqueValues(categoryCol-1)
        defaultPOI = escape( unescape( str(defaultPOI), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
        for cat in categories:
            if cat is None or str(cat) is 'NULL':
                continue
            cat = str(cat)
            filename = "{}.gpx".format(cat)
            path = os.path.join(base, filename)
            fp = open(path, "w", encoding="utf-8")
            fp.write('<?xml version="1.0" encoding="utf-8"?><gpx version="1.1" creator="QGIS POI Export" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')
            filter = '"{}" = \'{}\''.format(categoryName, cat)
            request = QgsFeatureRequest().setFilterExpression( filter )
            for f in layer.getFeatures( request ):
                point = self.transform4326.transform(f.geometry().asPoint())
                line = '<wpt lat="{}" lon="{}">\n'.format(point.y(), point.x())
                fp.write(line)
                if poiNameCol == 0:
                    line = '<name>{}</name>\n'.format(defaultPOI)
                else:
                    name = escape( unescape( str(f[poiNameCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                    line = '<name>{}</name>\n'.format(name)
                fp.write(line)
                if cmtCol > 0:
                    if f[cmtCol-1]:
                        cmt = escape( unescape( str(f[cmtCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                        line = '<cmt>{}</cmt>\n'.format(cmt)
                        fp.write(line)
                if descCol > 0:
                    if f[descCol-1]:
                        desc = escape( unescape( str(f[descCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                        line = '<desc>{}</desc>\n'.format(desc)
                        fp.write(line)
                if linkCol > 0:
                    link = str(f[linkCol-1]).strip()
                    if link and link != 'NULL':
                        line = '<link href="{}" />\n'.format(link)
                        fp.write(line)
                if symCol > 0:
                    sym = str(f[symCol-1]).strip()
                    if sym and sym != 'NULL':
                        line = '<sym>{}</sym>\n'.format(sym)
                        fp.write(line)
                if visualCol > 0:
                    if f[visualCol-1]:
                        color = escape( unescape( str(f[visualCol-1]), {"&apos;": "'", "&quot;": '"'}), {"'":"&apos;",'"':"&quot;"})
                        colorAgence = ColorHash(color)
                        line = '<extensions><color>{}</color></extensions>\n'.format(colorAgence.hex)
                        fp.write(line)
                fp.write('</wpt>\n')
            fp.write('</gpx>\n')
            fp.close()

    def getDirPath(self):
        settings = QSettings()
        path = settings.value("LastPath/POIExportPath", None)
        folder =  QFileDialog.getExistingDirectory(self, "Select POI folder", path)
        if not folder:
            return
        settings.setValue("LastPath/POIExportPath", folder)
        self.fileLineEdit.setText(folder)

    def showEvent(self, event):
        """ Initialize the Dialog widgets when it is first displyaed """
        super(POIExportDialog, self).showEvent(event)
        self.initLayerFields()

    def initLayerFields(self):
        """ Populate the QComboBox fields box with a list of all the fields in the selected
            points vector layer"""
        self.categoryComboBox.clear()
        self.poiNameComboBox.clear()
        self.visualComboBox.clear()
        self.descriptionComboBox.clear()
        self.commentComboBox.clear()
        self.webLinkComboBox.clear()
        self.symbolComboBox.clear()
        if self.vectorComboBox.count() == 0:
            return
        self.selectedLayer = self.vectorComboBox.currentLayer()
        
        self.categoryComboBox.addItem('[Use default category]', -1)
        self.poiNameComboBox.addItem('[Use default POI name]', -1)
        self.visualComboBox.addItem('[Select an optional POI color category field]', -1)
        self.commentComboBox.addItem('[Select an optional POI comment, address]', -1)
        self.descriptionComboBox.addItem('[Select an optional POI description]', -1)
        self.webLinkComboBox.addItem('[Select an optional URL field]', -1)
        self.symbolComboBox.addItem('[Select an optional symbol name]', -1)

        for idx, field in enumerate(self.selectedLayer.fields()):
            self.categoryComboBox.addItem(field.name(), idx)
            self.poiNameComboBox.addItem(field.name(), idx)
            self.visualComboBox.addItem(field.name(), idx)
            self.descriptionComboBox.addItem(field.name(), idx)
            self.commentComboBox.addItem(field.name(), idx)
            self.webLinkComboBox.addItem(field.name(), idx)
            self.symbolComboBox.addItem(field.name(), idx)

        self.setEnabled()
        
    def setEnabled(self):
        """ Depending on the settings some widgets are enabled and some are disabled. """
        categoryCol = self.categoryComboBox.currentIndex()
        poiNameCol = self.poiNameComboBox.currentIndex()
        self.defaultCategoryLineEdit.setEnabled(categoryCol == 0)
        self.defaultPOILineEdit.setEnabled(poiNameCol == 0)
        