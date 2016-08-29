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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# Initialize Qt resources from file resources.py
import resources

import os.path
from poiExportDialog import POIExportDialog

class POIExport:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        """Create the menu & tool bar items within QGIS"""
        self.poiDialog = POIExportDialog(self.iface)
        icon = QIcon(":/plugins/poiexport/icon.png")
        self.poiAction = QAction(icon, u"POI Exporter", self.iface.mainWindow())
        self.poiAction.triggered.connect(self.showPOIDialog)
        self.poiAction.setCheckable(False)
        self.iface.addToolBarIcon(self.poiAction)
        self.iface.addPluginToVectorMenu(u"GPS", self.poiAction)

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        self.iface.removePluginVectorMenu(u"GPS", self.poiAction)
        self.iface.removeToolBarIcon(self.poiAction)
    
    def showPOIDialog(self):
        """Display the POI Dialog window."""
        self.poiDialog.show()
        self.poiDialog.raise_()
        self.poiDialog.activateWindow()
        
        
