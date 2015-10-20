@echo off

rem Make sure you added Program Files\QGIS xxx\bin to your PATH

call pyuic4 -o "ui\ui_aboutdialogbase.py" "ui\aboutdialogbase.ui"

call pyuic4 -o "ui\ui_photo2shapedialogbase.py" "ui\photo2shapedialogbase.ui"

call pyrcc4 -o "resources_rc.py" "resources.qrc"
