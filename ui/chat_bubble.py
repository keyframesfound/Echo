from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt

class ChatBubble(QWidget):
    def __init__(self, message: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        label = QLabel(message)
        # Style for user/assistant
        if is_user:
            label.setStyleSheet("background-color: #DCF8C6; border-radius: 10px; padding: 8px;")
            layout.addWidget(label, 0, alignment=Qt.AlignRight)
        else:
            label.setStyleSheet("background-color: #F1F0F0; border-radius: 10px; padding: 8px;")
            layout.addWidget(label, 0, alignment=Qt.AlignLeft)
        self.setLayout(layout) 