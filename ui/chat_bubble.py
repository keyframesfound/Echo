from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout
from PySide6.QtGui import QColor, QPalette

class ChatBubble(QWidget):
    def __init__(self, message: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        label = QLabel(message)
        # Style for user/assistant
        if is_user:
            label.setStyleSheet("background-color: #DCF8C6; border-radius: 10px; padding: 8px;")
            layout.addWidget(label, 0, alignment=1)  # Right
        else:
            label.setStyleSheet("background-color: #F1F0F0; border-radius: 10px; padding: 8px;")
            layout.addWidget(label, 0, alignment=0)  # Left
        self.setLayout(layout) 