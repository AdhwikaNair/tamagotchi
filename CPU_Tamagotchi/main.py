import sys
import os
import datetime
import shutil
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QFont, QPixmap, QFontDatabase
from src.pet_brain import PetBrain

class TamagotchiWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.brain = PetBrain()
        
        self.is_dragging = False 
        self.click_start_pos = QPoint()
        self.bubble_visible = False
        self.is_chonky = False 

        # Absolute path to assets folder
        self.assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

        # --- LOAD CUSTOM PIXEL FONT ---
        font_path = os.path.join(self.assets_dir, "font.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    self.pixel_font = families[0]
                else:
                    self.pixel_font = "Consolas"
            else:
                self.pixel_font = "Consolas"
        else:
            self.pixel_font = "Consolas"
        
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True) 
        
        cursor_path = os.path.join(self.assets_dir, "cursor.png")
        if not os.path.exists(cursor_path):
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            reply = QMessageBox.information(None, "Missing Cursor Image!", "Hey! Please click OK to select the paw image you just uploaded so I can set it as your custom cursor!")
            selected, _ = QFileDialog.getOpenFileName(None, "Select Cursor Image", "", "Images (*.png *.jpg *.jpeg)")
            if selected:
                try:
                    import shutil
                    shutil.copy(selected, cursor_path)
                except Exception:
                    pass

        if os.path.exists(cursor_path):
            from PyQt6.QtGui import QCursor
            pixmap = QPixmap(cursor_path)
            if not pixmap.isNull():
                scaled_cursor = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio)
                custom_cursor = QCursor(scaled_cursor, 16, 16)
                self.setCursor(custom_cursor)
        
        self.layout = QVBoxLayout()
        # Anchoring to AlignBottom prevents the app from piercing the taskbar!
        self.layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.layout.setSpacing(-50) # Overlap boxes onto the image
        self.layout.setContentsMargins(0, 0, 0, 0)

        # --- SPEECH BUBBLE (Click Menu) ---
        self.speech_container = QWidget()
        self.speech_container.setObjectName("SpeechBox")
        self.layers_layout = QVBoxLayout()
        self.layers_layout.setContentsMargins(11, 36, 25, 22)
        self.layers_layout.setSpacing(6)
        self.speech_container.setLayout(self.layers_layout)
        
        frame_path = os.path.join(self.assets_dir, "frame.png")
        if not os.path.exists(frame_path):
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            reply = QMessageBox.information(None, "Missing Frame Image!", "Hey! I couldn't find frame.png in your assets folder (I can't steal it from our chat!).\nPlease click OK to select the image file from your Downloads folder so I can use it!")
            selected, _ = QFileDialog.getOpenFileName(None, "Select Frame Image", "", "Images (*.png *.jpg *.jpeg)")
            if selected:
                try:
                    import shutil
                    shutil.copy(selected, frame_path)
                except Exception as e:
                    print("Failed to copy", e)

        if os.path.exists(frame_path):
            self.speech_style = f"""
                QWidget#SpeechBox {{
                    background-color: transparent; 
                    border-image: url("{frame_path.replace('\\', '/')}") 0 0 0 0 stretch stretch;
                }}
                QLabel {{
                    color: #4B0082;
                    border: none;
                    background: transparent;
                }}
            """
            self.speech_container.setStyleSheet(self.speech_style)
            self.speech_container.setFixedSize(180, 145)
        else:
            self.speech_style = """
                QWidget#SpeechBox {
                    background-color: #FFFFFF; 
                    border: 3px solid #B19CD9;
                    border-radius: 6px;
                    padding: 5px;
                }
                QLabel {
                    color: #4B0082;
                    border: none;
                }
            """
            self.speech_container.setStyleSheet(self.speech_style)
        
        sp_speech = self.speech_container.sizePolicy()
        sp_speech.setRetainSizeWhenHidden(True)
        self.speech_container.setSizePolicy(sp_speech)
        self.speech_container.hide()

        self.speech_text = QLabel("...")
        self.speech_text.setFont(QFont(self.pixel_font, 10))
        self.speech_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layers_layout.addWidget(self.speech_text)

        # Buttons Style
        btn_css = f"""
            QPushButton {{
                background-color: #F0F0F0;
                color: #4B0082;
                font-family: '{self.pixel_font}';
                font-size: 12px;
                font-weight: bold;
                border: 2px solid #B19CD9;
                border-radius: 4px;
                padding: 1px;
            }}
            QPushButton:hover {{
                background-color: #E6E6FA;
            }}
        """

        self.feed_btn = QPushButton("DEVOUR PROCESS 💊")
        self.feed_btn.setStyleSheet(btn_css)
        self.feed_btn.setFixedWidth(136)
        self.feed_btn.clicked.connect(self.handle_feeding)
        self.feed_btn.hide()
        self.layers_layout.addWidget(self.feed_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.overclock_btn = QPushButton("TOGGLE OVERCLOCK ⚡")
        self.overclock_btn.setStyleSheet(btn_css)
        self.overclock_btn.setFixedWidth(136)
        self.overclock_btn.clicked.connect(self.handle_overclock)
        self.layers_layout.addWidget(self.overclock_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.reboot_btn = QPushButton("REBOOT SYSTEM 💾")
        self.reboot_btn.setStyleSheet(btn_css)
        self.reboot_btn.setFixedWidth(136)
        self.reboot_btn.clicked.connect(self.handle_reboot)
        self.reboot_btn.hide()
        self.layers_layout.addWidget(self.reboot_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        # Add to horizontal layout later
        # Move StatsBox ABOVE the Sprite so taskbar doesn't clip it!
        self.stats_container = QWidget()
        self.stats_container.setObjectName("StatsBox")
        self.stats_inner_layout = QVBoxLayout()
        self.stats_inner_layout.setContentsMargins(11, 36, 25, 22)
        self.stats_container.setLayout(self.stats_inner_layout)
        
        self.stats_label = QLabel("Loading...")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if os.path.exists(frame_path):
            self.stats_style = f"""
                QWidget#StatsBox {{
                    background-color: transparent; 
                    border-image: url("{frame_path.replace('\\', '/')}") 0 0 0 0 stretch stretch;
                }}
                QLabel {{
                    color: #4B0082; 
                    background: transparent;
                    border: none;
                }}
            """
            self.stats_container.setStyleSheet(self.stats_style)
            self.stats_label.setStyleSheet("background: transparent; border: none; color: #4B0082;")
            self.stats_container.setFixedSize(180, 145)
        else:
            self.stats_style = """
                QWidget#StatsBox {
                    background-color: #FAF5FF;
                    border: 3px solid #B19CD9;
                    border-radius: 6px;
                    padding: 8px;
                }
                QLabel {
                    color: #4B0082;
                    border: none;
                    background: transparent;
                }
            """
            self.stats_container.setStyleSheet(self.stats_style)
            self.stats_label.setStyleSheet("color: #4B0082; border: none; background: transparent;")
        self.stats_label.setFont(QFont(self.pixel_font, 10))
        self.stats_inner_layout.addStretch()
        self.stats_inner_layout.addWidget(self.stats_label)
        self.stats_inner_layout.addStretch()

        sp_stats = self.stats_container.sizePolicy()
        sp_stats.setRetainSizeWhenHidden(True)
        self.stats_container.setSizePolicy(sp_stats)
        self.stats_container.hide()
        
        from PyQt6.QtWidgets import QHBoxLayout
        self.menus_layout = QHBoxLayout()
        self.menus_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.menus_layout.setSpacing(10)
        self.menus_layout.addWidget(self.stats_container)
        self.menus_layout.addWidget(self.speech_container)
        
        self.layout.addLayout(self.menus_layout)

        # --- SPRITE ---
        self.sprite_label = QLabel()
        self.sprite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.sprite_label)
        self.setLayout(self.layout)

        # Ensure menus overlap on top
        self.speech_container.raise_()
        self.stats_container.raise_()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(2000)
        
        self.update_display()
        self.setFixedSize(400, 320)
        self.show()

    def update_display(self):
        stats = self.brain.update_stats(QApplication.clipboard().text())
        current_hour = datetime.datetime.now().hour

        # Determine Sprite state with proper priority
        if stats['status'] == "FATAL ERROR 🪦":
            img, status = "dead", "DEAD 💀"
        elif not stats['plugged_in'] and stats['battery'] < 20:
            img, status = "dead", "LOW BATT 🪦"
        elif self.brain.overclocking:
            img, status = "stressed", "OVERCLOCK ⚡"
        elif current_hour >= 23 or current_hour < 6:
            img, status = "sleepy", "SLEEPY 😴"
        elif self.is_chonky:
            img, status = "chonky", "CHONKY 🍔"
        elif stats['cpu'] > 85 or stats['ram'] > 85:
            img, status = "stressed", "STRESSED 🥵"
        else:
            img, status = "chillin", "CHILLIN 😎"

        # Update Pixmap
        img_path = os.path.join(self.assets_dir, f"{img}.png")
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio)
            cropped = scaled.copy(0, 40, scaled.width(), scaled.height() - 40)
            self.sprite_label.setPixmap(cropped)
        else:
            self.sprite_label.setText(f"[{img}]")
        
        # Update Text Content
        self.speech_text.setText(f"[{stats['title']}]\nState: {status}")
        
        time_str = datetime.datetime.now().strftime("%H:%M")
        pwr_str = "AC" if stats['plugged_in'] else f"{stats['battery']}%"
        self.stats_label.setText(
            f"TIME: {time_str} | PWR: {pwr_str}\n"
            f"{'-'*18}\n"
            f"CPU: {stats['cpu']}% | RAM: {stats['ram']}%\n"
            f"HP: {stats['hp']} | XP: {stats['xp']}\n"
            f"WGT: {stats['weight']}"
        )

        # Button Logic
        if "LOW BATT" in status or "DEAD" in status:
            self.feed_btn.hide()
            self.overclock_btn.hide()
            self.reboot_btn.show()
        else:
            self.reboot_btn.hide()
            self.overclock_btn.show()
            self.feed_btn.show()

    def enterEvent(self, event):
        self.stats_container.show()

    def leaveEvent(self, event):
        self.stats_container.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True 
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.click_start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False 
            if (event.globalPosition().toPoint() - self.click_start_pos).manhattanLength() < 5:
                # Priority: Handle clickable links or toggle bubble
                self.bubble_visible = not self.bubble_visible
                self.speech_container.setVisible(self.bubble_visible)

    def handle_feeding(self):
        target = self.brain.get_top_offender()
        if target:
            reply = QMessageBox.question(
                self, "Confirm Devour",
                f"Do you want to devour '{target['name']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.brain.devour_process(target['pid'])
                if success:
                    self.is_chonky = False 
                    self.brain.pet_thoughts = message
                    self.brain.thought_timer = 20 # Show result for a few ticks
                    self.update_display()
                else:
                    self.brain.pet_thoughts = message
                    self.brain.thought_timer = 20
                    self.update_display()
        else:
            self.brain.pet_thoughts = "Nothing to eat! I'm still hungry..."
            self.brain.thought_timer = 20
            self.update_display()

    def handle_overclock(self):
        self.brain.toggle_overclock()
        self.update_display()

    def handle_reboot(self):
        self.brain.reboot_system()
        self.update_display()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = os.path.normpath(urls[0].toLocalFile())
            if path.startswith("\\\\?\\"): path = path[4:]
            success, _ = self.brain.eat_file(path)
            if success:
                self.is_chonky = True 
                self.update_display()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = TamagotchiWidget()
    sys.exit(app.exec())
