PLUGINNAME = poiexport
PLUGINS = "$(HOME)"/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)
PY_FILES = poiexport.py __init__.py poiExportDialog.py
EXTRAS = icon.png metadata.txt
UI_FILES = poiexportdialog.ui

deploy: 
	mkdir -p $(PLUGINS)
	cp -vf $(PY_FILES) $(PLUGINS)
	cp -vf $(UI_FILES) $(PLUGINS)
	cp -vf $(EXTRAS) $(PLUGINS)
	cp -vfr doc $(PLUGINS)
	cp -vf helphead.html $(PLUGINS)/index.html
	python -m markdown -x markdown.extensions.headerid README.md >> $(PLUGINS)/index.html
	echo '</body>' >> $(PLUGINS)/index.html
