# ui/app.py
# Main UI logic for Echo AI Butler

import sys
import time
import asyncio
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, 
    QHBoxLayout, QScrollArea, QFrame, QProgressBar, QMessageBox, QComboBox
)
from PySide6.QtCore import QTimer, Qt, Signal, Slot, QThread
from PySide6.QtGui import QImage, QPixmap
import cv2
import datetime
from modules.enhanced_speech import speech_manager, SpeechEngine

class AsyncHelper(QThread):
    """Helper class to run async code in Qt"""
    def __init__(self, coro):
        super().__init__()
        self.coro = coro

    def run(self):
        asyncio.run(self.coro)

class EchoUI(QWidget):
    update_response_signal = Signal(str)
    set_input_signal = Signal(str)
    add_chat_bubble_signal = Signal(str, str)  # role, text
    update_voice_ui_signal = Signal(bool)
    show_loading_signal = Signal()  # New signal for showing loading bar
    remove_loading_signal = Signal()  # New signal for removing loading bar
    update_status_signal = Signal(str, bool)  # message, is_error
    voice_changed_signal = Signal(str)

    def __init__(self):
        super().__init__()
        if sys.platform == 'darwin':
            # Set input method hints for better macOS compatibility
            self.setAttribute(Qt.WA_InputMethodEnabled)
            self.setAttribute(Qt.WA_KeyCompression)
        
        self.setWindowTitle("Echo AI Butler")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("background-color: #181A1B; color: #F5F6FA; font-family: '.AppleSystemUIFont', 'SF Pro', 'Helvetica Neue', sans-serif;")

        self.layout = QVBoxLayout()
        self.webcam_label = QLabel()
        self.webcam_label.setAlignment(Qt.AlignCenter)
        self.webcam_label.setStyleSheet("border-radius: 16px; background: #23272A; margin: 16px;")
        self.layout.addWidget(self.webcam_label)

        # Replace response_box with chat area
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setStyleSheet("background: #23272A; border-radius: 12px; padding: 8px;")
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.addStretch(1)
        self.chat_widget.setLayout(self.chat_layout)
        self.chat_area.setWidget(self.chat_widget)
        self.layout.addWidget(self.chat_area)

        # Add chat input and buttons
        self.input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your message here...")
        self.input_box.setStyleSheet("background: #23272A; border-radius: 8px; font-size: 16px; padding: 8px;")
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("background: #5865F2; color: white; border-radius: 8px; font-size: 16px; padding: 8px 16px;")
        self.voice_button = QPushButton("🎤 Voice")
        self.voice_button.setStyleSheet("background: #43B581; color: white; border-radius: 8px; font-size: 16px; padding: 8px 16px;")
        self.stop_listening_button = QPushButton("⏹ Stop Listening")
        self.stop_listening_button.setStyleSheet("background: #F04747; color: white; border-radius: 8px; font-size: 16px; padding: 8px 16px;")
        self.stop_listening_button.setVisible(False)
        self.input_layout.addWidget(self.input_box)
        self.input_layout.addWidget(self.send_button)
        self.input_layout.addWidget(self.voice_button)
        self.input_layout.addWidget(self.stop_listening_button)
        self.layout.addLayout(self.input_layout)

        # Add voice profile selector
        voice_layout = QHBoxLayout()
        self.voice_selector = QComboBox()
        self.voice_selector.addItems(speech_manager.voice_profiles.keys())
        self.voice_selector.setStyleSheet("""
            QComboBox {
                background: #23272A;
                border-radius: 8px;
                font-size: 14px;
                padding: 4px 8px;
                color: #F5F6FA;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        self.voice_selector.currentTextChanged.connect(self.handle_voice_change)
        voice_layout.addWidget(QLabel("Voice:"))
        voice_layout.addWidget(self.voice_selector)
        voice_layout.addStretch(1)
        self.input_layout.insertLayout(0, voice_layout)

        self.setLayout(self.layout)

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Connect send button and Enter key
        self.send_button.clicked.connect(self.handle_send)
        self.input_box.returnPressed.connect(self.handle_send)
        self.voice_button.clicked.connect(self.handle_voice)
        self.stop_listening_button.clicked.connect(self.handle_stop_listening)

        # Connect all signals
        self.update_response_signal.connect(self.display_response)
        self.set_input_signal.connect(self.input_box.setText)
        self.update_voice_ui_signal.connect(self._set_voice_ui_state)
        self.add_chat_bubble_signal.connect(self.add_chat_bubble)
        self.show_loading_signal.connect(self._create_loading_bar)  # New connection
        self.remove_loading_signal.connect(self._remove_loading_bar)  # New connection
        self.update_status_signal.connect(self._show_status)  # New connection

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image).scaled(800, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.webcam_label.setPixmap(pixmap)

    @Slot(str, str)
    def add_chat_bubble(self, role, text, replace_last_llm=False):
        # Improved Discord-style message row with better formatting, avatars, and markdown support
        from PySide6.QtWidgets import QLabel, QHBoxLayout, QFrame, QVBoxLayout, QProgressBar
        import datetime
        from PySide6.QtGui import QTextDocument
        import re
        # If replacing last LLM bubble (for loading), remove it
        if replace_last_llm and self.chat_layout.count() > 1:
            for i in range(self.chat_layout.count() - 2, -1, -1):
                frame = self.chat_layout.itemAt(i).widget()
                if frame is not None and hasattr(frame, 'role') and frame.role == 'llm':
                    frame.deleteLater()
                    break
        row = QFrame()
        row.role = role  # For animation lookup
        row.setFrameShape(QFrame.NoFrame)
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(8, 4, 8, 4)
        row_layout.setSpacing(10)
        # Avatar
        avatar = QLabel()
        avatar.setFixedSize(36, 36)
        if role == "user":
            avatar.setStyleSheet("border-radius: 18px; background: #5865F2; font-size: 22px; text-align: center;")
            avatar.setText("🧑")
        else:
            avatar.setStyleSheet("border-radius: 18px; background: #23272A; font-size: 22px; text-align: center;")
            avatar.setText("🤖")
        # Name and message
        name = QLabel("You" if role == "user" else "Echo")
        name.setStyleSheet("font-weight: bold; font-size: 14px; color: #8e9297;")
        # Markdown support for message
        msg = QLabel()
        msg.setWordWrap(True)
        msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        msg.setStyleSheet("font-size: 16px; color: #F5F6FA; background: none;")
        def md_to_html(s):
            s = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', s)
            s = re.sub(r'\*(.*?)\*', r'<i>\1</i>', s)
            s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
            s = s.replace('\n', '<br>')
            return s
        msg.setText(md_to_html(text))
        # Timestamp
        timestamp = QLabel(datetime.datetime.now().strftime("%H:%M"))
        timestamp.setStyleSheet("font-size: 12px; color: #72767d; margin-left: 6px;")
        # Layout
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(name)
        col.addWidget(msg)
        if role == "user":
            row_layout.addWidget(avatar)
            row_layout.addLayout(col)
            row_layout.addWidget(timestamp)
            row_layout.addStretch(1)
        else:
            row_layout.addStretch(1)
            row_layout.addWidget(avatar)
            row_layout.addLayout(col)
            row_layout.addWidget(timestamp)
        row.setLayout(row_layout)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, row)
        # Always autoscroll to bottom
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    @Slot(str)
    def display_response(self, text):
        # If this is a real LLM response, replace the loading bar
        self.remove_loading_bar()
        self.add_chat_bubble_signal.emit("llm", text)
        if text == "Loading...":
            self.show_loading_bar()

    @Slot()
    def _create_loading_bar(self):
        """Creates loading bar widget on the main thread"""
        row = QFrame()
        row.role = 'llm'
        row.setFrameShape(QFrame.NoFrame)
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(8, 4, 8, 4)
        row_layout.setSpacing(10)
        avatar = QLabel()
        avatar.setFixedSize(36, 36)
        avatar.setStyleSheet("border-radius: 18px; background: #23272A; font-size: 22px; text-align: center;")
        avatar.setText("🤖")
        name = QLabel("Echo")
        name.setStyleSheet("font-weight: bold; font-size: 14px; color: #8e9297;")
        bar = QProgressBar()
        bar.setRange(0,0)  # Indeterminate
        bar.setFixedHeight(16)
        bar.setFixedWidth(180)
        bar.setStyleSheet("QProgressBar {background: #23272A; border-radius: 8px;} QProgressBar::chunk {background: #5865F2;}")
        timestamp = QLabel(datetime.datetime.now().strftime("%H:%M"))
        timestamp.setStyleSheet("font-size: 12px; color: #72767d; margin-left: 6px;")
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(name)
        col.addWidget(bar)
        row_layout.addStretch(1)
        row_layout.addWidget(avatar)
        row_layout.addLayout(col)
        row_layout.addWidget(timestamp)
        row.setLayout(row_layout)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, row)
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
        self._loading_row = row

    @Slot()
    def _remove_loading_bar(self):
        """Removes loading bar widget on the main thread"""
        if hasattr(self, '_loading_row') and self._loading_row is not None:
            self._loading_row.deleteLater()
            self._loading_row = None

    @Slot(str, bool)
    def _show_status(self, message, error=False):
        """Shows status message on the main thread"""
        from PySide6.QtWidgets import QMessageBox
        def show():
            if error:
                QMessageBox.critical(self, "Error", message)
            else:
                QMessageBox.information(self, "Status", message)
        QTimer.singleShot(0, show)

    def start_continuous_voice(self, timeout=10):
        """Enhanced continuous voice mode with VAD"""
        self.listening = True
        self.update_voice_ui_signal.emit(True)
        
        async def listen_loop():
            last_interaction = time.time()
            while self.listening:
                try:
                    # Use enhanced speech recognition
                    result = await speech_manager.listen(timeout=5, continuous=True)
                    
                    if not self.listening:
                        break
                        
                    if result:
                        self.add_chat_bubble_signal.emit("user", result)
                        self.update_response_signal.emit("Loading...")
                        
                        # Handle vision if needed
                        image_bytes = None
                        if self.needs_vision(result):
                            ret, frame = self.cap.read()
                            if ret:
                                try:
                                    ret2, jpeg = cv2.imencode('.jpg', frame)
                                    if ret2:
                                        image_bytes = jpeg.tobytes()
                                except Exception as e:
                                    self.show_status(f"Webcam error: {e}", error=True)
                                    
                        # Get AI response
                        from modules import llm
                        response = llm.generate_response(result, image_bytes=image_bytes)
                        self.update_response_signal.emit(response)
                        
                        # Use enhanced TTS
                        await speech_manager.speak(response)
                        last_interaction = time.time()
                    
                    # Check timeout
                    if time.time() - last_interaction > timeout:
                        self.update_response_signal.emit("[Voice session timed out. Click Voice to start again.]")
                        self.listening = False
                        break
                        
                except Exception as e:
                    self.show_status(f"Voice interaction error: {e}", error=True)
                    break
            
            self.update_voice_ui_signal.emit(False)
        
        AsyncHelper(listen_loop()).start()

    def show_loading_bar(self):
        """Thread-safe method to show loading bar"""
        self.show_loading_signal.emit()

    def remove_loading_bar(self):
        """Thread-safe method to remove loading bar"""
        self.remove_loading_signal.emit()

    def show_status(self, message, error=False):
        """Thread-safe method to show status"""
        self.update_status_signal.emit(message, error)

    @Slot(str)
    def display_response(self, text):
        """Thread-safe method to display responses"""
        if text == "Loading...":
            self.show_loading_bar()
        else:
            self.remove_loading_bar()
            self.add_chat_bubble_signal.emit("llm", text)

    @Slot(str, str)
    def add_chat_bubble(self, role, text, replace_last_llm=False):
        """Thread-safe method to add chat bubbles"""
        # Ensure we're on the main thread
        if QThread.currentThread() != QApplication.instance().thread():
            # If called from background thread, emit signal to self
            self.add_chat_bubble_signal.emit(role, text)
            return

        # Improved Discord-style message row with better formatting, avatars, and markdown support
        from PySide6.QtWidgets import QLabel, QHBoxLayout, QFrame, QVBoxLayout, QProgressBar
        import datetime
        from PySide6.QtGui import QTextDocument
        import re
        # If replacing last LLM bubble (for loading), remove it
        if replace_last_llm and self.chat_layout.count() > 1:
            for i in range(self.chat_layout.count() - 2, -1, -1):
                frame = self.chat_layout.itemAt(i).widget()
                if frame is not None and hasattr(frame, 'role') and frame.role == 'llm':
                    frame.deleteLater()
                    break
        row = QFrame()
        row.role = role  # For animation lookup
        row.setFrameShape(QFrame.NoFrame)
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(8, 4, 8, 4)
        row_layout.setSpacing(10)
        # Avatar
        avatar = QLabel()
        avatar.setFixedSize(36, 36)
        if role == "user":
            avatar.setStyleSheet("border-radius: 18px; background: #5865F2; font-size: 22px; text-align: center;")
            avatar.setText("🧑")
        else:
            avatar.setStyleSheet("border-radius: 18px; background: #23272A; font-size: 22px; text-align: center;")
            avatar.setText("🤖")
        # Name and message
        name = QLabel("You" if role == "user" else "Echo")
        name.setStyleSheet("font-weight: bold; font-size: 14px; color: #8e9297;")
        # Markdown support for message
        msg = QLabel()
        msg.setWordWrap(True)
        msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        msg.setStyleSheet("font-size: 16px; color: #F5F6FA; background: none;")
        def md_to_html(s):
            s = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', s)
            s = re.sub(r'\*(.*?)\*', r'<i>\1</i>', s)
            s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
            s = s.replace('\n', '<br>')
            return s
        msg.setText(md_to_html(text))
        # Timestamp
        timestamp = QLabel(datetime.datetime.now().strftime("%H:%M"))
        timestamp.setStyleSheet("font-size: 12px; color: #72767d; margin-left: 6px;")
        # Layout
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(name)
        col.addWidget(msg)
        if role == "user":
            row_layout.addWidget(avatar)
            row_layout.addLayout(col)
            row_layout.addWidget(timestamp)
            row_layout.addStretch(1)
        else:
            row_layout.addStretch(1)
            row_layout.addWidget(avatar)
            row_layout.addLayout(col)
            row_layout.addWidget(timestamp)
        row.setLayout(row_layout)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, row)
        # Always autoscroll to bottom
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)

    def handle_send(self):
        """Enhanced send handler with async TTS"""
        user_text = self.input_box.text().strip()
        if user_text:
            self.add_chat_bubble_signal.emit("user", user_text)
            def get_response():
                try:
                    self.update_response_signal.emit("Loading...")
                    image_bytes = None
                    if self.needs_vision(user_text):
                        ret, frame = self.cap.read()
                        if ret:
                            try:
                                ret2, jpeg = cv2.imencode('.jpg', frame)
                                if ret2:
                                    image_bytes = jpeg.tobytes()
                            except Exception as e:
                                self.show_status(f"Webcam error: {e}", error=True)
                                
                    from modules import llm
                    response = llm.generate_response(user_text, image_bytes=image_bytes)
                    self.update_response_signal.emit(response)
                    
                    # Use async TTS
                    async def speak_async():
                        await speech_manager.speak(response)
                    
                    AsyncHelper(speak_async()).start()
                    
                except Exception as e:
                    self.show_status(f"Error: {e}", error=True)
                    
            self.input_box.clear()
            QThread(target=get_response).start()

    def handle_voice(self):
        try:
            self.start_continuous_voice(timeout=15)
        except Exception as e:
            self.show_status(f"Voice error: {e}", error=True)

    def handle_stop_listening(self):
        self.listening = False
        self.update_voice_ui_signal.emit(False)
        self.update_response_signal.emit("[Voice session stopped.]")

    def handle_voice_change(self, profile_name):
        """Handle voice profile changes"""
        if speech_manager.switch_voice(profile_name):
            self.voice_changed_signal.emit(profile_name)

    def _set_voice_ui_state(self, listening):
        self.stop_listening_button.setVisible(listening)
        self.voice_button.setEnabled(not listening)

    def show_intro_message(self):
        self.add_chat_bubble_signal.emit("llm", "Hello! I am Echo, your AI butler. How can I help you today?")

    def inputMethodEvent(self, event):
        """Handle input method events for better IME support on macOS"""
        if self.input_box.hasFocus():
            self.input_box.inputMethodEvent(event)
        super().inputMethodEvent(event)

    def inputMethodQuery(self, query):
        """Handle input method queries for better IME support on macOS"""
        if self.input_box.hasFocus():
            return self.input_box.inputMethodQuery(query)
        return super().inputMethodQuery(query)

    def needs_vision(self, text):
        """Check if the user's input requires visual context"""
        vision_keywords = [
            "see", "look", "show", "camera", "webcam", 
            "screen", "display", "image", "picture",
            "what do you see", "can you see", "in front of me",
            "what's on my desk", "what am i holding",
            "describe what you see", "what's visible"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in vision_keywords)
