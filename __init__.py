def classFactory(iface):
    from .poiexport import POIExport
    return POIExport(iface)
