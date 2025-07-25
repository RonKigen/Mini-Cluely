import sqlite3
import sys
import os
import pandas as pd
import pyaudio
import wave
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QTextEdit, QFileDialog
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from chatbot.bot import get_bot_answer
from chatbot.bot import get_bot_answer_question  # Changed from get_bot_answer_wenti
from chatbot.utils import speech_to_text
from PyQt5.QtWidgets import QMessageBox, QLabel
from chatbot.bot import capture_and_extract_text
from PyQt5.QtWidgets import QPushButton, QFileDialog
#from chatbot.audio_thread import AudioThread  # Import the audio thread class just created
from chatbot.bot import generate_prompt
from PyQt5.QtWidgets import QSlider, QLabel, QVBoxLayout, QWidget, QTextEdit, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QRadioButton, QVBoxLayout, QTextEdit, QWidget
from chatbot.taskthread import TaskThread
from chatbot.bot import get_kg_answer


class ChatBotApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set window title and size
        self.setWindowTitle("Professional Interview Chatbot")
        self.setGeometry(100, 100, 1000, 900)
        self.setWindowFlag(Qt.FramelessWindowHint)  # Remove window border
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        # Initialize layouts FIRST to avoid parent issues
        self.layout = QVBoxLayout(self)
        self.button_layout = QHBoxLayout()
        self.input_layout = QHBoxLayout()
        
        # Initialize drag-related variables
        self.is_dragging = False  
        self.drag_position = None  

        # Set chat history box to display user and bot conversations
        self.chat_history = QTextEdit(self)
        self.chat_history.setReadOnly(True)  # Set to read-only, user cannot modify chat history
        # FIXED: Removed text-shadow which is not supported in Qt
        self.chat_history.setStyleSheet("""
            background-color: rgba(0, 0, 0, 70);
            color: blue;
            font-size: 25px;
            font-weight: bold;
        """)
        self.layout.addWidget(self.chat_history)  # Add chat box to layout
        
        # Set user input box and send button
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("Enter your interview question...")
        self.user_input.setStyleSheet(
            "background-color: rgba(0, 0, 0, 200); color: white; font-size: 14px; padding: 10px;")
        self.input_layout.addWidget(self.user_input)

        # Create send button
        self.send_button = QPushButton("Send", self)
        self.send_button.setStyleSheet(
            "background-color: rgba(0, 0, 0, 150); color: white; font-size: 14px; padding: 10px;")
        self.send_button.clicked.connect(self.send_message)
        self.input_layout.addWidget(self.send_button)
        self.layout.addLayout(self.input_layout)
        
        # Set input box to get focus
        self.user_input.setFocus()
        # Timer for displaying messages segment by segment
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.display_next_message)
        self.messages = []
        self.current_message_index = 0


        # Voice recording button
        self.voice_button = QPushButton("🎤Record", self)
        self.voice_button.setStyleSheet("""
                                  background-color: rgba(0, 0, 255, 150);
                                  color: white;
                                  font-size: 20px;
                                  padding: 5px;
                                  border-radius: 10px;
                              """)
        self.voice_button.setFixedSize(90, 50)
        self.voice_button.clicked.connect(self.toggle_recording)
        
        # Recording related variables
        self.is_recording = False
        self.audio = None
        self.stream = None
        self.frames = []
        self.output_filename = "assets/recorded_audio.wav"

        # Capture keyboard spacebar events for start/stop recording
        self.user_input.installEventFilter(self)
        # Connect Enter key event to send message when Enter is pressed
        self.user_input.returnPressed.connect(self.send_message)

        # Knowledge base button
        self.kg_button = QPushButton("📕", self)
        self.kg_button.setStyleSheet("""
                                  background-color: rgba(0, 0, 0, 150);
                                  color: white;
                                  font-size: 20px;
                                  padding: 5px;
                                  border-radius: 10px;
                              """)
        self.kg_button.setGeometry(850, 0, 40, 40)
        self.kg_button.setFixedSize(40, 40)
        self.kg_button.pressed.connect(self.setup_kg)

        # Drag button
        self.drag_button = QPushButton("☰", self)
        self.drag_button.setStyleSheet("""
                          background-color: rgba(0, 0, 0, 150);
                          color: white;
                          font-size: 20px;
                          padding: 5px;
                          border-radius: 10px;
                      """)
        self.drag_button.setGeometry(900, 0, 40, 40)
        self.drag_button.setFixedSize(40, 40)
        self.drag_button.pressed.connect(self.start_drag)

        # Close button
        self.close_button = QPushButton("X", self)
        self.close_button.setStyleSheet("""
            background-color: rgba(255, 0, 0, 180); 
            color: white; 
            font-size: 20px; 
            padding: 5px;
            border-radius: 10px;
        """)
        self.close_button.clicked.connect(self.close)
        self.close_button.setGeometry(950, 0, 40, 40)
        self.close_button.setFixedSize(40, 40)

        # Create screenshot button
        self.capture_button = QPushButton("📷Screenshot", self)
        self.capture_button.setStyleSheet("""
            background-color: rgba(0, 0, 255, 150);
            color: white;
            font-size: 20px;
            padding: 5px;
            border-radius: 10px;
        """)
        self.capture_button.setFixedSize(90, 50)
        # Connect button click event
        self.capture_button.clicked.connect(self.on_capture_button_click)

        # Create clear chat history button
        self.clear_button = QPushButton("Clear History", self)
        self.clear_button.setStyleSheet("""
                background-color: rgba(255, 0, 0, 150);
                color: white;
                font-size: 20px;
                padding: 5px;
                border-radius: 10px;
            """)
        self.clear_button.setFixedSize(90, 50)
        self.clear_button.clicked.connect(self.clear_chat_history)

        # Create another button for loading files and generating prompt.txt
        self.load_button = QPushButton("Load Resume", self)
        self.load_button.setStyleSheet("""
                        background-color: rgba(0, 255, 0, 150);
                        color: white;
                        font-size: 20px;
                        padding: 5px;
                        border-radius: 10px;
                    """)
        self.load_button.setFixedSize(90, 50)
        self.load_button.clicked.connect(self.load_resume)

        # Create knowledge base mode button
        self.kga_button = QPushButton("Enable KG", self)
        self.kga_button.setStyleSheet("""
                                background-color: rgba(0, 0, 255, 150);
                                color: white;
                                font-size: 20px;
                                padding: 5px;
                                border-radius: 10px;
                            """)
        self.kga_button.setFixedSize(90, 50)
        self.kga_button.clicked.connect(self.toggle_kg)
        self.is_kg=False

        # Microphone test button
        self.mic_test_button = QPushButton("🎧Test Mic", self)
        self.mic_test_button.setStyleSheet("""
                                  background-color: rgba(128, 128, 128, 150);
                                  color: white;
                                  font-size: 20px;
                                  padding: 5px;
                                  border-radius: 10px;
                              """)
        self.mic_test_button.setFixedSize(100, 50)
        self.mic_test_button.clicked.connect(self.test_microphone)

        # Quick text input button
        self.quick_text_button = QPushButton("💬Quick Text", self)
        self.quick_text_button.setStyleSheet("""
                                  background-color: rgba(0, 150, 0, 150);
                                  color: white;
                                  font-size: 18px;
                                  padding: 5px;
                                  border-radius: 10px;
                              """)
        self.quick_text_button.setFixedSize(100, 50)
        self.quick_text_button.clicked.connect(self.focus_text_input)

        # Add buttons to bottom button layout
        self.button_layout.addWidget(self.voice_button)
        self.button_layout.addWidget(self.capture_button)
        self.button_layout.addWidget(self.clear_button)
        self.button_layout.addWidget(self.load_button)
        self.button_layout.addWidget(self.kga_button)
        self.button_layout.addWidget(self.mic_test_button)
        self.button_layout.addWidget(self.quick_text_button)

        # Create radio buttons: control font color
        self.black_radio = QRadioButton("Code Mode", self)
        self.black_radio.setChecked(False)  # Default not selected for black font
        self.black_radio.toggled.connect(self.update_font_color)

        self.white_radio = QRadioButton("Light Mode", self)
        self.white_radio.setChecked(False)  # Default not selected for white font
        self.white_radio.toggled.connect(self.update_font_color)

        self.red_radio = QRadioButton("Default Mode", self)
        self.red_radio.setChecked(True)  # Default selected for red font
        self.red_radio.toggled.connect(self.update_font_color)

        self.black_radio1 = QRadioButton("Focus Mode", self)
        self.black_radio1.setChecked(False)  # Default not selected for black font
        self.black_radio1.toggled.connect(self.update_font_color)

        # Set radio button styles
        self.black_radio.setStyleSheet("""
                    font-size: 20px;
                    padding: 10px;
                """)
        self.white_radio.setStyleSheet("""
                    font-size: 20px;
                    padding: 10px;
                """)
        self.red_radio.setStyleSheet("""
                    font-size: 20px;
                    padding: 10px;
                """)
        self.black_radio1.setStyleSheet("""
                            font-size: 20px;
                            padding: 10px;
                        """)

        # Add radio buttons to layout
        self.button_layout.addWidget(self.black_radio)
        self.button_layout.addWidget(self.white_radio)
        self.button_layout.addWidget(self.red_radio)
        self.button_layout.addWidget(self.black_radio1)

        # FIXED: Only add button_layout once to main layout
        self.layout.addLayout(self.button_layout)
        
        # FIXED: Don't call setLayout again since we already set it in __init__
        # self.setLayout(self.layout) - This line was causing the layout parent issue

    def toggle_kg(self):
        """Toggle knowledge base status"""
        if self.is_kg:
            self.kga_button.setText("Enable KG")
            self.stop_kg()
        else:
            self.kga_button.setText("🔴")
            self.start_kg()

    def start_kg(self):
        self.is_kg=True
        self.chat_history.append('Knowledge base has been enabled...')
        pass
    def stop_kg(self):
        self.is_kg=False
        self.chat_history.append('Knowledge base has been disabled...')
        pass

    def setup_kg(self):  # Changed from stru_kg to setup_kg for better English naming
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Excel Files (*.xlsx)")  # Only allow selection of .xlsx files
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            if file_path:
                self.chat_history.append('Building knowledge base! Please wait patiently....')
                self.load_excel_to_db(file_path)
            else:
                print("No file selected, program exits.")
        return None

    def load_excel_to_db(self,file_path, db_name="knowledge/knowledge.db"):
        # Load Excel file
        df = pd.read_excel(file_path)

        # Check if data format meets requirements
        if 'Question' not in df.columns or 'Answer' not in df.columns:
            print("Excel format error, please ensure it contains 'Question' and 'Answer' columns.")
            return

        # Connect to database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Create table (if it doesn't exist)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
        ''')

        # Insert data, avoid duplicates
        for _, row in df.iterrows():
            question, answer = row['Question'], row['Answer']

            # Check if the same Q&A pair already exists in database
            cursor.execute("SELECT COUNT(*) FROM knowledge WHERE question = ? AND answer = ?", (question, answer))
            if cursor.fetchone()[0] == 0:
                # Not duplicate, insert new record
                cursor.execute("INSERT INTO knowledge (question, answer) VALUES (?, ?)", (question, answer))
            else:
                # print(f"Duplicate data: '{question}' already exists, skip insertion.")
                pass

        # Commit and close database connection
        conn.commit()
        conn.close()
        print(f"Data has been imported from '{file_path}' to database '{db_name}'.")
        self.show_popup_message("Success", "Personal knowledge base has been generated! Please select knowledge base mode to use!")

    def update_font_color(self):
        """Update font color based on radio button selection"""
        # FIXED: Removed all text-shadow properties as they're not supported in Qt
        if self.black_radio.isChecked():
            self.chat_history.setStyleSheet("""
                        background-color: rgba(0, 0, 0, 200);
                        color: white;
                        font-size: 18px;
                        font-weight: bold;
                    """)
        elif self.white_radio.isChecked():
            self.chat_history.setStyleSheet("""
                                    background-color: rgba(0, 0, 0, 0);
                                    color: yellow;
                                    font-size: 30px;
                                    font-weight: bold;
                                """)
        elif self.red_radio.isChecked():
            self.chat_history.setStyleSheet("""
                                    background-color: rgba(0, 0, 0, 70);
                                    color: red;
                                    font-size: 25px;
                                    font-weight: bold;
                                """)
        elif self.black_radio1.isChecked():
            self.chat_history.setStyleSheet("""
                                    background-color: rgba(0, 0, 0, 250);
                                    color: white;
                                    font-size: 30px;
                                    font-weight: bold;
                                """)
        else:
            self.chat_history.setStyleSheet("""
                                                background-color: rgba(0, 0, 0, 70);
                                                color: red;
                                                font-size: 25px;
                                                font-weight: bold;
                                            """)

    def load_resume(self):
        """Select file and generate prompt.txt"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Text Files (*.pdf)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]

            #generate_prompt(file_path)  # Call function to process file
            self.chat_history.append('Executing task! This takes a long time, please wait patiently....')
            #Add multithreading
            self.thread_merge = TaskThread(generate_prompt,file_path)
            self.thread_merge.finished_signal.connect(self.load_resume_information)  # Changed from load_resum_informa
            # Recycle thread
            self.thread_merge.finished_signal.connect(self.thread_merge.deleteLater)
            self.thread_merge.start()

    def load_resume_information(self):  # Changed from load_resum_informa to load_resume_information
        """Process merged data"""
        #print("Merged data:", result)# Pop up reminder box to remind user
        self.show_popup_message("Success", "prompt.txt file has been generated! Please restart application to update information!")

    def show_popup_message(self, title, message):
        """Show popup message"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def clear_chat_history(self):
        """Clear chat history"""
        self.chat_history.clear()
        print("Chat history has been cleared!")

    def on_capture_button_click(self):
        self.chat_history.append('Start screenshot...')
        text=capture_and_extract_text()

        # Add multithreading
        self.thread_merge = TaskThread(get_bot_answer_question, text)  # Changed from get_bot_answer_wenti
        self.thread_merge.result_signal.connect(self.split)
        # Recycle thread
        self.thread_merge.finished_signal.connect(self.thread_merge.deleteLater)
        self.thread_merge.start()

    def send_message(self):
        """Handle send message event"""
        user_message = self.user_input.text().strip()
        if user_message:
            self.chat_history.append(f"You: {user_message}")
            self.chat_history.append("")  # Empty line separator
            self.user_input.clear()
            '''
            The logic here is: if knowledge base is enabled, prioritize knowledge base query, 
            if no results found then use large model. If disabled, directly use large model.
            '''
            if self.is_kg:
                results = get_kg_answer(user_message)
                if results:
                    self.chat_history.append(f"Found {len(results)} relevant records:")
                    for idx, (question, answer) in enumerate(results, 1):
                        self.chat_history.append(f"{idx}. Question: {question}\n   Answer: {answer}\n")
                else:
                    self.chat_history.append(f"No relevant records found in local knowledge base, large model answering...")
                    answer = get_bot_answer(user_message)
                    self.split(answer)
            else:
                answer = get_bot_answer(user_message)
                self.split(answer)

    def display_next_message(self):
        """Display robot messages step by step"""
        if self.current_message_index < len(self.messages):
            message = self.messages[self.current_message_index]
            self.chat_history.append(message)
            self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())
            self.current_message_index += 1
        else:
            self.timer.stop()

    def start_drag(self):
        """Start dragging window"""
        self.is_dragging = True
        self.drag_position = QCursor.pos() - self.frameGeometry().topLeft()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False

    def toggle_recording(self):
        """Toggle recording status"""
        if self.is_recording:
            self.voice_button.setText("🎤Record")
            self.stop_recording()
        else:
            self.voice_button.setText("🔴")  # Red dot indicating recording
            self.start_recording()

    def start_recording(self):
        """Start recording"""
        self.chat_history.append('Start recording...')
        if self.is_recording:
            return  # If already recording, return directly

        self.is_recording = True
        self.frames = []

        # FIXED: Add error handling for audio initialization
        try:
            # Initialize pyaudio and audio stream with better settings
            self.audio = pyaudio.PyAudio()
            
            # Find the default input device and check its capabilities
            default_device_info = self.audio.get_default_input_device_info()
            self.chat_history.append(f"Using microphone: {default_device_info['name']}")
            
            self.stream = self.audio.open(format=pyaudio.paInt16,
                                          channels=1,
                                          rate=16000,
                                          input=True,
                                          frames_per_buffer=1024,
                                          input_device_index=default_device_info['index'])
            self.voice_button.setText("🔴")  # Change button text
            self.record_audio()  # Start recording
        except Exception as e:
            self.chat_history.append(f"Audio initialization failed: {str(e)}")
            self.chat_history.append("Please check your microphone connection and permissions.")
            self.is_recording = False

    def stop_recording(self):
        """Stop recording and save file"""
        if not self.is_recording:
            return

        self.is_recording = False
        
        # Stop and close audio stream
        try:
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
            if self.audio is not None:
                self.audio.terminate()

            # Save file
            if not os.path.exists('assets'):
                os.makedirs('assets')  # Ensure assets folder exists

            if self.frames:  # Only save if we have recorded data
                self.chat_history.append(f"Recording saved. Processing audio ({len(self.frames)} frames)...")
                with wave.open(self.output_filename, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(16000)
                    wf.writeframes(b''.join(self.frames))

                # Perform speech recognition after recording completion
                self.on_recording_complete()
            else:
                self.chat_history.append("No audio data recorded. Please check your microphone and try again.")
                
        except Exception as e:
            self.chat_history.append(f"Recording save failed: {str(e)}")
        finally:
            # Clear recording data
            self.frames = []
            self.stream = None
            self.audio = None

    def on_recording_complete(self):
        """Perform speech recognition after recording completion"""
        try:
            self.chat_history.append("Converting speech to text...")
            result = speech_to_text(self.output_filename)
            if result.get('err_no') == 0:
                recognized_text = result.get('result', [])[0]
                self.chat_history.append(f"You: {recognized_text}")
                print(f"Recognition result: {recognized_text}")
                
                # Send recognized text to large model
                if self.is_kg:
                    results = get_kg_answer(recognized_text)
                    if results:
                        self.chat_history.append(f"Found {len(results)} relevant records:")
                        for idx, (question, answer) in enumerate(results, 1):
                            self.chat_history.append(f"{idx}. Question: {question}\n   Answer: {answer}\n")
                    else:
                        self.chat_history.append(f"No relevant records found in local knowledge base, large model answering...")
                        self.thread_merge = TaskThread(get_bot_answer, recognized_text)
                        self.thread_merge.result_signal.connect(self.split)
                        self.thread_merge.finished_signal.connect(self.thread_merge.deleteLater)
                        self.thread_merge.start()
                else:
                    self.thread_merge = TaskThread(get_bot_answer, recognized_text)
                    self.thread_merge.result_signal.connect(self.split)
                    self.thread_merge.finished_signal.connect(self.thread_merge.deleteLater)
                    self.thread_merge.start()
            else:
                error_msg = result.get('err_msg', 'Unknown error')
                self.chat_history.append(f"Speech recognition failed: {error_msg}")
                print(f"Speech recognition failed: {error_msg}")
                
                # Offer manual text input as fallback
                self.chat_history.append("═══════════════════════════════════")
                self.chat_history.append("🎤 Voice recognition didn't work this time.")
                self.chat_history.append("💬 Please type your question in the text box below instead!")
                self.chat_history.append("🔧 Or try the '🎧Test Mic' button to check your microphone setup.")
                self.chat_history.append("═══════════════════════════════════")
                
                # If the error is due to quiet audio, provide specific guidance
                if 'quiet' in error_msg.lower() or 'silent' in error_msg.lower():
                    self.chat_history.append("💡 Tip: Your microphone volume seems too low.")
                    self.chat_history.append("   Try speaking louder and closer to the microphone.")
                elif 'network' in error_msg.lower() or 'connection' in error_msg.lower():
                    self.chat_history.append("💡 Tip: Check your internet connection.")
                elif 'pocketsphinx' in error_msg.lower() or 'sphinx' in error_msg.lower():
                    self.chat_history.append("💡 Tip: Offline recognition unavailable. Try typing instead.")
        except Exception as e:
            self.chat_history.append(f"Speech recognition error: {str(e)}")
            print(f"Speech recognition error: {str(e)}")

    def split(self, result):
        answer = result + '\n----------------------end----------------------------'
        #answer = get_bot_answer(recognized_text) + '\nEnd'
        #print("kkkkkk")
        self.messages = answer.split('\n')
        self.current_message_index = 0
        self.timer.start(0)

    def record_audio(self):
        """Continuous recording"""
        if self.is_recording and self.stream is not None:
            try:
                data = self.stream.read(1024)
                self.frames.append(data)
                QTimer.singleShot(10, self.record_audio)  # Recursive call to continue recording
            except Exception as e:
                self.chat_history.append(f"Recording error: {str(e)}")
                self.stop_recording()

    def test_microphone(self):
        """Test microphone functionality and provide feedback"""
        self.chat_history.append("Testing microphone...")
        
        try:
            import pyaudio
            audio = pyaudio.PyAudio()
            
            # Get info about available devices
            self.chat_history.append("Available audio input devices:")
            device_count = 0
            for i in range(audio.get_device_count()):
                info = audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    device_count += 1
                    self.chat_history.append(f"  {i}: {info['name']}")
            
            if device_count == 0:
                self.chat_history.append("❌ No microphone devices found!")
                audio.terminate()
                return
            
            # Test default input device
            default_device = audio.get_default_input_device_info()
            self.chat_history.append(f"Default microphone: {default_device['name']}")
            
            # Test recording a short sample
            self.chat_history.append("Recording 3-second test sample...")
            
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            # Record for 3 seconds
            frames = []
            for i in range(0, int(16000 / 1024 * 3)):
                data = stream.read(1024)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Analyze the recorded audio
            import struct
            all_data = b''.join(frames)
            audio_values = struct.unpack('<' + 'h' * (len(all_data) // 2), all_data)
            max_amplitude = max(abs(v) for v in audio_values) if audio_values else 0
            
            self.chat_history.append(f"Test recording complete!")
            self.chat_history.append(f"Max audio level detected: {max_amplitude}")
            
            if max_amplitude < 100:
                self.chat_history.append("⚠️ Audio level is very low. Please:")
                self.chat_history.append("  - Check microphone connection")
                self.chat_history.append("  - Increase microphone volume in system settings")
                self.chat_history.append("  - Speak closer to the microphone")
                self.chat_history.append("  - Check if microphone is muted")
            elif max_amplitude < 1000:
                self.chat_history.append("⚠️ Audio level is low but detectable. Consider:")
                self.chat_history.append("  - Speaking louder")
                self.chat_history.append("  - Moving closer to the microphone")
            else:
                self.chat_history.append("✅ Microphone is working well!")
                self.chat_history.append("You should be able to use voice recording successfully.")
                
        except Exception as e:
            self.chat_history.append(f"❌ Microphone test failed: {str(e)}")
            self.chat_history.append("Please check your audio drivers and microphone connection.")

    def focus_text_input(self):
        """Focus on text input and provide guidance"""
        self.chat_history.append("💬 Text input mode activated!")
        self.chat_history.append("Type your interview question below and press Enter or click Send.")
        self.user_input.setFocus()
        # Flash the input field to draw attention
        original_style = self.user_input.styleSheet()
        self.user_input.setStyleSheet(
            "background-color: rgba(0, 255, 0, 100); color: white; font-size: 14px; padding: 10px; border: 2px solid green;")
        
        # Restore original style after 1 second
        def restore_style():
            self.user_input.setStyleSheet(original_style)
        
        QTimer.singleShot(1000, restore_style)

    def eventFilter(self, source, event):
        """Capture keyboard events"""
        if event.type() == event.KeyPress and event.key() == Qt.Key_Space:
            self.toggle_recording()
            return True
        elif event.type() == event.KeyPress and event.modifiers() == (Qt.ControlModifier | Qt.AltModifier):
            # Ctrl + Alt triggers screenshot button click event
            self.capture_button.click()  # Simulate screenshot button click
            return True  # Event has been handled
        return super().eventFilter(source, event)