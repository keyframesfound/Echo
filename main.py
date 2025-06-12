# main.py
# Entry point for Echo AI Butler

import sys
import os
from ui.app import EchoUI
from PySide6.QtWidgets import QApplication
from PySide6 import QtCore

if __name__ == "__main__":
    # Set up macOS-specific attributes
    if sys.platform == 'darwin':
        # Disable native menu bar
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_DontUseNativeMenuBar)
        # Enable native text rendering system
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
        # Set IME position policy
        os.environ['QT_IM_MODULE'] = 'ime'
        
    # Enable high DPI scaling
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    
    app = QApplication(sys.argv)
    app.setStyle('fusion')  # Use fusion style for better macOS compatibility
    window = EchoUI()
    window.show()
    window.show_intro_message()
    sys.exit(app.exec())
