from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, QScrollArea, QFileDialog, QHBoxLayout, QComboBox)
import sys
from ui.chat_bubble import ChatBubble
from modules.llm import query_llm, OpenRouterError
from modules.speech import recognize_speech
from modules.enhanced_speech import transcribe_audio, OpenRouterWhisperError
from modules.ocr import extract_text_from_image
from modules.vision import analyze_image
from modules.search import search_web, SerpAPIError

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Echo AI Assistant")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.layout = QVBoxLayout()
        
        # Scroll area for chat
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_widget.setLayout(self.chat_layout)
        self.scroll_area.setWidget(self.chat_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Input row (text, send, mic, image, search)
        input_row = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your message and press Enter or Send...")
        self.input_box.returnPressed.connect(self.send_message)
        input_row.addWidget(self.input_box)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_row.addWidget(self.send_button)
        self.mic_button = QPushButton("🎤")
        self.mic_button.setToolTip("Speak (basic speech recognition)")
        self.mic_button.clicked.connect(self.speech_input)
        input_row.addWidget(self.mic_button)
        self.whisper_button = QPushButton("🗣️")
        self.whisper_button.setToolTip("Transcribe audio file (Whisper)")
        self.whisper_button.clicked.connect(self.whisper_input)
        input_row.addWidget(self.whisper_button)
        self.image_button = QPushButton("🖼️")
        self.image_button.setToolTip("Upload image for OCR/vision")
        self.image_button.clicked.connect(self.image_input)
        input_row.addWidget(self.image_button)
        self.search_button = QPushButton("🔍")
        self.search_button.setToolTip("Web search (SerpAPI)")
        self.search_button.clicked.connect(self.search_input)
        input_row.addWidget(self.search_button)
        self.layout.addLayout(input_row)
        
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)
        
        # Initial assistant message
        self.add_chat_bubble("Hello! How can I help you today?", is_user=False)

    def add_chat_bubble(self, message, is_user=True):
        bubble = ChatBubble(message, is_user=is_user)
        self.chat_layout.addWidget(bubble)
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def send_message(self):
        prompt = self.input_box.text().strip()
        if not prompt:
            return
        self.add_chat_bubble(prompt, is_user=True)
        self.input_box.clear()
        QApplication.processEvents()
        try:
            response = query_llm(prompt)
            self.add_chat_bubble(response, is_user=False)
        except OpenRouterError as e:
            QMessageBox.critical(self, "LLM Error", str(e))

    def speech_input(self):
        self.add_chat_bubble("[Listening for speech...]")
        QApplication.processEvents()
        text = recognize_speech()
        self.add_chat_bubble(text, is_user=True)
        if text and not text.startswith("["):
            try:
                response = query_llm(text)
                self.add_chat_bubble(response, is_user=False)
            except OpenRouterError as e:
                QMessageBox.critical(self, "LLM Error", str(e))

    def whisper_input(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select audio file", "", "Audio Files (*.wav *.mp3 *.m4a *.flac)")
        if not file_path:
            return
        self.add_chat_bubble(f"[Transcribing audio: {file_path}]")
        QApplication.processEvents()
        try:
            text = transcribe_audio(file_path)
            self.add_chat_bubble(text, is_user=True)
            if text and not text.startswith("["):
                response = query_llm(text)
                self.add_chat_bubble(response, is_user=False)
        except OpenRouterWhisperError as e:
            QMessageBox.critical(self, "Whisper Error", str(e))

    def image_input(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select image file", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff)")
        if not file_path:
            return
        self.add_chat_bubble(f"[Analyzing image: {file_path}]")
        QApplication.processEvents()
        # OCR
        ocr_text = extract_text_from_image(file_path)
        self.add_chat_bubble(f"[OCR]: {ocr_text}", is_user=False)
        # Vision (stub)
        vision_result = analyze_image(file_path)
        self.add_chat_bubble(f"[Vision]: {vision_result}", is_user=False)
        # Optionally, send OCR text to LLM
        if ocr_text and not ocr_text.startswith("["):
            try:
                response = query_llm(ocr_text)
                self.add_chat_bubble(response, is_user=False)
            except OpenRouterError as e:
                QMessageBox.critical(self, "LLM Error", str(e))

    def search_input(self):
        query, ok = QFileDialog.getText(self, "Web Search", "Enter search query:")
        if not ok or not query.strip():
            return
        self.add_chat_bubble(f"[Web search]: {query}", is_user=True)
        QApplication.processEvents()
        try:
            result = search_web(query)
            self.add_chat_bubble(f"[Search result]: {result}", is_user=False)
        except SerpAPIError as e:
            QMessageBox.critical(self, "Search Error", str(e))

def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 