import sys
import os
import datetime
import shutil
import base64
import pyautogui
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QMessageBox, QFileDialog, QStackedWidget, QFrame, QDialog, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint, QBuffer, QIODeviceBase
from PyQt6.QtGui import QFont, QPixmap, QFontDatabase, QMovie, QColor, QBitmap, QPainter, QPainterPath, QPen
from src.pet_brain import PetBrain

class PinkPopup(QDialog):
    def __init__(self, title, message, pixel_font="Consolas", is_question=False, parent=None):
        super().__init__()
        if parent: self.setParent(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_widget = QWidget(self)
        main_widget.setStyleSheet("""
            QWidget#MainWidget {
                background-color: #FDE2ED;
                border: 2px solid black;
            }
        """)
        main_widget.setObjectName("MainWidget")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget)
        
        v_layout = QVBoxLayout(main_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(0)
        
        # Title bar (Hot Pink)
        title_bar = QWidget()
        title_bar.setFixedHeight(24)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #F35B89;
                border-bottom: 2px solid black;
            }
        """)
        t_layout = QHBoxLayout(title_bar)
        t_layout.setContentsMargins(6, 0, 4, 0)
        
        t_label = QLabel(title)
        t_label.setStyleSheet(f"color: white; font-family: '{pixel_font}'; font-weight: bold; font-size: 13px; border: none; background: transparent;")
        t_layout.addWidget(t_label)
        t_layout.addStretch()
        
        # Close button in title bar
        close_btn = QPushButton("X")
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FDE2ED;
                border: 1px solid black;
                color: black;
                font-family: 'Consolas';
                font-size: 11px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover { background-color: #FFFFFF; }
        """)
        close_btn.clicked.connect(self.reject)
        t_layout.addWidget(close_btn)
        
        v_layout.addWidget(title_bar)
        
        # Body Content
        content_widget = QWidget()
        content_widget.setStyleSheet("border: none; background: transparent;")
        c_layout = QHBoxLayout(content_widget)
        c_layout.setContentsMargins(12, 12, 12, 12)
        
        # Add Icon
        icon_label = QLabel()
        icon_pixmap = QPixmap(36, 36)
        icon_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(icon_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        path.moveTo(18, 4)
        path.lineTo(34, 32)
        path.lineTo(2, 32)
        path.closeSubpath()
        painter.setBrush(QColor("#F35B89"))
        painter.setPen(QPen(QColor("black"), 2))
        painter.drawPath(path)
        
        painter.setBrush(QColor("black"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(16, 12, 4, 10)
        painter.drawRect(16, 26, 4, 4)
        painter.end()
        
        icon_label.setPixmap(icon_pixmap)
        c_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignTop)
        
        c_layout.addSpacing(5)
        
        msg_layout = QVBoxLayout()
        msg_layout.setSpacing(8)
        
        msg_label = QLabel(message)
        msg_label.setFont(QFont(pixel_font, 10))
        msg_label.setStyleSheet("color: black;")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        msg_layout.addWidget(msg_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.setSpacing(10)
        
        btn_style = f"""
            QPushButton {{
                background-color: #FDE2ED;
                border: 2px solid black;
                color: black;
                font-family: '{pixel_font}';
                font-size: 11px;
                padding: 3px 12px;
            }}
            QPushButton:hover {{
                background-color: #F35B89;
                color: white;
            }}
            QPushButton:pressed {{
                background-color: #D81B60;
            }}
        """
        
        if is_question:
            yes_btn = QPushButton("Yes")
            yes_btn.setStyleSheet(btn_style)
            yes_btn.clicked.connect(self.accept)
            
            no_btn = QPushButton("No")
            no_btn.setStyleSheet(btn_style)
            no_btn.clicked.connect(self.reject)
            
            btn_layout.addWidget(yes_btn)
            btn_layout.addWidget(no_btn)
        else:
            ok_btn = QPushButton("OK")
            ok_btn.setStyleSheet(btn_style)
            ok_btn.clicked.connect(self.accept)
            btn_layout.addWidget(ok_btn)
            
        msg_layout.addLayout(btn_layout)
        c_layout.addLayout(msg_layout)
        v_layout.addWidget(content_widget)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_pos') and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()



class TamagotchiWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.movie = None
        self.current_img = "chillin"
        self.brain = PetBrain()
        
        self.is_dragging = False
        self.drag_position = QPoint()
        self.click_start_pos = QPoint()
        self.bubble_visible = False
        self.is_chonky = False
        self.current_page = 0

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
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent; border: none; outline: none;")
        self.setWindowOpacity(0.999) 
        self.setContentsMargins(0, 0, 0, 0)
        self.setAcceptDrops(True) 
        
        cursor_path = os.path.join(self.assets_dir, "cursor.png")
        if not os.path.exists(cursor_path):
            from PyQt6.QtWidgets import QFileDialog
            popup = PinkPopup("Desktop", "Missing Cursor Image!\n\nPlease select the paw image you uploaded\nso I can set it as your cursor!", self.pixel_font, False, self)
            popup.exec()
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
        self.layout.setSpacing(-110) # Overlap boxes more closely onto the cat
        self.layout.setContentsMargins(0, 0, 0, 0)

        # --- SPEECH BUBBLE (Click Menu) ---
        self.speech_container = QWidget()
        self.speech_container.setObjectName("SpeechBox")
        
        self.speech_title_label = QLabel(self.speech_container)
        self.speech_title_label.setGeometry(50, 3, 110, 22)
        self.speech_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speech_title_label.setFont(QFont(self.pixel_font, 12))
        self.speech_title_label.setStyleSheet("color: #4B0082; font-weight: bold; background: transparent; border: none;")
        
        self.layers_layout = QVBoxLayout()
        self.layers_layout.setContentsMargins(23, 40, 32, 4)
        self.layers_layout.setSpacing(0)
        self.speech_container.setLayout(self.layers_layout)
        
        frame_path = os.path.join(self.assets_dir, "frame.png")
        if not os.path.exists(frame_path):
            from PyQt6.QtWidgets import QFileDialog
            popup = PinkPopup("Desktop", "Missing Frame Image!\n\nPlease find frame.png in your folder.", self.pixel_font, False, self)
            popup.exec()
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
            self.speech_container.setFixedSize(220, 160)
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
                border: 1px solid #B19CD9;
                border-radius: 4px;
                padding: 1px 2px;
            }}
            QPushButton:hover {{
                background-color: #E6E6FA;
            }}
        """

        self.feed_btn = QPushButton("DEVOUR PROCESS" + "\u00A0" * 4)
        self.feed_btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        from PyQt6.QtGui import QIcon
        from PyQt6.QtCore import QSize
        ramen_path = os.path.join(self.assets_dir, "ramen1.png")
        if os.path.exists(ramen_path):
            self.feed_btn.setIcon(QIcon(ramen_path))
            self.feed_btn.setIconSize(QSize(28, 28))
        
        self.feed_btn.setStyleSheet(btn_css)
        self.feed_btn.setFixedSize(134, 32)
        self.feed_btn.clicked.connect(self.handle_feeding)
        self.feed_btn.hide()
        self.layers_layout.addWidget(self.feed_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.overclock_btn = QPushButton("TOGGLE OVERCLOCK" + "\u00A0" * 4)
        self.overclock_btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        monster_path = os.path.join(self.assets_dir, "monsterdrink.png")
        if os.path.exists(monster_path):
            self.overclock_btn.setIcon(QIcon(monster_path))
            self.overclock_btn.setIconSize(QSize(28, 28))
            
        self.overclock_btn.setStyleSheet(btn_css)
        self.overclock_btn.setFixedSize(134, 32)
        self.overclock_btn.clicked.connect(self.handle_overclock)
        self.layers_layout.addWidget(self.overclock_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.reboot_btn = QPushButton("REBOOT SYSTEM 💾")
        self.reboot_btn.setStyleSheet(btn_css)
        self.reboot_btn.setFixedSize(134, 32)
        self.reboot_btn.clicked.connect(self.handle_reboot)
        self.reboot_btn.hide()
        self.layers_layout.addWidget(self.reboot_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.layers_layout.addStretch()
        # Add to horizontal layout later
        # Move StatsBox ABOVE the Sprite        # --- STATS BUBBLE (Hover Menu) ---
        self.stats_container = QWidget()
        self.stats_container.setObjectName("StatsBox")
        
        self.stats_title_label = QLabel("     SYSTEM MONITOR] ", self.stats_container)
        self.stats_title_label.setGeometry(55, 3, 110, 22)
        self.stats_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_title_label.setFont(QFont(self.pixel_font, 11))
        self.stats_title_label.setStyleSheet("color: #4B0082; font-weight: bold; background: transparent; border: none;")
        
        self.stats_inner_layout = QVBoxLayout()
        self.stats_inner_layout.setContentsMargins(16, 22, 40, 15)
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
            self.stats_container.setFixedSize(220, 160)
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
        self.stats_label.setFont(QFont(self.pixel_font, 12))
        self.stats_inner_layout.addStretch()
        self.stats_inner_layout.addWidget(self.stats_label)
        self.stats_inner_layout.addStretch()

        # --- MUSIC CONTAINER ---
        self.music_container = QWidget()
        self.music_container.setObjectName("MusicBox")
        self.music_container.setFixedSize(220, 160) # Updated fixed size
        self.music_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.music_layout = QVBoxLayout()
        self.music_layout.setContentsMargins(23, 33, 32, 15)
        self.music_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if os.path.exists(frame_path):
            self.music_style = f"""
                QWidget#MusicBox {{
                    background-color: transparent; 
                    border-image: url("{frame_path.replace('\\', '/')}") 0 0 0 0 stretch stretch;
                }}
                QLabel {{
                    color: #4B0082; 
                    background: transparent;
                    border: none;
                }}
            """
            self.music_container.setStyleSheet(self.music_style)
        else:
            self.music_style = """
                QWidget#MusicBox {
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
            self.music_container.setStyleSheet(self.music_style)
            
        self.music_title_label = QLabel("    [MUSIC REMOTE]", self.music_container)
        self.music_title_label.setGeometry(55, 1, 110, 22)
        self.music_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.music_title_label.setFont(QFont(self.pixel_font, 11))
        self.music_title_label.setStyleSheet("color: #4B0082; font-weight: bold; background: transparent; border: none;")
        
        self.music_controls_layout = QVBoxLayout()
        self.music_controls_layout.setSpacing(10)
        self.music_controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_play_music = QPushButton("🎧 PLAY/PAUSE")
        self.btn_play_music.setStyleSheet(btn_css)
        self.btn_play_music.setFixedSize(130, 32)
        self.btn_play_music.clicked.connect(lambda: pyautogui.press('playpause'))
        
        self.btn_stop_music = QPushButton("✨ SKIP TRACK")
        self.btn_stop_music.setStyleSheet(btn_css)
        self.btn_stop_music.setFixedSize(130, 32)
        self.btn_stop_music.clicked.connect(lambda: pyautogui.press('nexttrack'))
        
        self.music_controls_layout.addWidget(self.btn_play_music)
        self.music_controls_layout.addWidget(self.btn_stop_music)
        
        # Override margins to physically push the content box into the visual white center of the bubble
        # self.music_layout.setContentsMargins(19, 30, 27, 14) # Removed, now set above
        
        self.music_layout.addLayout(self.music_controls_layout)
        self.music_container.setLayout(self.music_layout)
        # --- STACKED WIDGET ---
        self.stacked_pages = QStackedWidget()
        self.stacked_pages.setFrameStyle(QFrame.Shape.NoFrame | QFrame.Shadow.Plain)
        self.stacked_pages.setFixedSize(220, 160)
        
        # --- COVER PAGE (GIF) ---
        self.cover_container = QWidget()
        self.cover_container.setObjectName("CoverBox")
        self.cover_container.setFixedSize(220, 160)
        # The container acts as the black border
        self.cover_container.setStyleSheet("""
            #CoverBox {
                background-color: black;
                border-radius: 12px;
            }
        """)
        
        self.cover_layout = QVBoxLayout()
        # 2px margins create a 2px black border around the GIF
        self.cover_layout.setContentsMargins(2, 2, 2, 2)
        self.cover_container.setLayout(self.cover_layout)
        
        cover_path = os.path.join(self.assets_dir, "tamayogif.gif")
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setFixedSize(216, 156)
        
        # Strictly mask the label so the QMovie cannot render outside the rounded corners
        mask = QBitmap(216, 156)
        mask.clear()
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.color1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 216, 156, 10, 10)
        painter.end()
        self.cover_label.setMask(mask)
        self.cover_label.setStyleSheet("background-color: transparent;")
        
        if os.path.exists(cover_path):
            self.cover_movie = QMovie(cover_path)
            self.cover_movie.jumpToFrame(0)
            orig_size = self.cover_movie.currentImage().size()
            if orig_size.width() > 0 and orig_size.height() > 0:
                # Scale the GIF to cover the entire label
                scaled_size = orig_size.scaled(216, 156, Qt.AspectRatioMode.KeepAspectRatioByExpanding)
                self.cover_movie.setScaledSize(scaled_size)
            self.cover_label.setMovie(self.cover_movie)
            self.cover_movie.start()
        else:
            self.cover_label.setText("[tamayogif.gif missing]")
            
        self.cover_layout.addWidget(self.cover_label)
        
        # Give pages a transparent background so the curl renders cleanly
        if hasattr(self, 'speech_style'):
            # Note: cover_container retains its black rounded background defined above
            self.speech_container.setStyleSheet(self.speech_style + "\nbackground: transparent;")
            self.stats_container.setStyleSheet(self.stats_style + "\nbackground: transparent;")
            self.music_container.setStyleSheet(self.music_style + "\nbackground: transparent;")
        
        self.stacked_pages.addWidget(self.cover_container)
        self.stacked_pages.addWidget(self.stats_container)
        self.stacked_pages.addWidget(self.speech_container)
        self.stacked_pages.addWidget(self.music_container)
        self.stacked_pages.setCurrentIndex(0)
        self.stacked_pages.hide()
        
        from PyQt6.QtWidgets import QHBoxLayout
        self.menus_layout = QHBoxLayout()
        self.menus_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.menus_layout.addWidget(self.stacked_pages)
        
        self.layout.addLayout(self.menus_layout)

        # --- SPRITE ---
        self.sprite_label = QLabel()
        self.sprite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sprite_label.setFrameShape(QFrame.Shape.NoFrame)
        self.sprite_label.setStyleSheet("border: none; background: transparent; outline: none;")
        self.movie = None
        
        self.layout.addWidget(self.sprite_label)
        self.setLayout(self.layout)

        # No raise_() needed, QStackedWidget handles order

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(2000)
        
        self.update_display()
        self.setFixedSize(400, 320)
        self.show()

    def update_display(self):
        stats = self.brain.update_stats(QApplication.clipboard().text())
        current_hour = datetime.datetime.now().hour

        # Determine Sprite state directly from the pet brain
        img = stats.get('img', 'chillin')
        status = stats['status']
        
        # UI overlays
        if "OVERCLOCK" in status:
            monster_uri = os.path.join(self.assets_dir, "monsterdrink.png").replace('\\', '/')
            status = f"OVERCLOCK <img src='{monster_uri}' width='14' height='14' align='middle'>"
            
        if self.is_chonky and img not in ["dead"]:
            img = "chonky"
            status = "CHONKY 🍔"

        # Update Pixmap
        self.update_pet_image(img)
        
        # Update Text Content
        self.speech_title_label.setText(f"[{stats['title']}]")
        self.speech_text.setText(f"<center>State: {status}</center>")
        
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
        if "LOW BATTERY" in status or "FATAL" in status:
            self.feed_btn.hide()
            self.overclock_btn.hide()
            self.reboot_btn.show()
        else:
            self.reboot_btn.hide()
            self.overclock_btn.show()
            self.feed_btn.show()

    def update_pet_image(self, img):
        # Check if PyQt6 label has actual graphical data loaded
        pixmap = self.sprite_label.pixmap()
        has_pixmap = pixmap is not None and not pixmap.isNull()
        
        # Do not restart the animation if the state is already playing
        if img == self.current_img and (self.movie is not None or has_pixmap):
            return
            
        self.current_img = img

        # Stop any existing movie
        if self.movie:
            self.movie.stop()
            self.movie = None
            self.sprite_label.setMovie(None)

        # 1. Try to load GIF first for animation
        gif_path = os.path.join(self.assets_dir, f"{img}.gif")
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.movie.jumpToFrame(0)
            orig_size = self.movie.currentImage().size()
            if orig_size.width() > 0 and orig_size.height() > 0:
                # Scale keeping aspect ratio, bounded by 250x250
                scaled_size = orig_size.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio)
                self.movie.setScaledSize(scaled_size)
            self.sprite_label.setMovie(self.movie)
            self.movie.start()
        else:
            # 2. Fallback to static PNG
            img_path = os.path.join(self.assets_dir, f"{img}.png")
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio)
                self.sprite_label.setPixmap(scaled)
            else:
                self.sprite_label.setText(f"[{img}]")
        
        self.is_chonky = (img == "chonky")

    # Removed enterEvent and leaveEvent because QStackedWidget handles visibility now

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
                # Check what was clicked using local position
                clicked_widget = self.childAt(event.position().toPoint())
                
                # Check if click is on/within stacked_pages
                is_on_menu = False
                temp = clicked_widget
                while temp:
                    if temp == self.stacked_pages:
                        is_on_menu = True
                        break
                    temp = temp.parentWidget()
                
                if is_on_menu:
                    # User clicked the boxes -> flip to next page
                    self.flip_to_next_page()
                elif clicked_widget == self.sprite_label or clicked_widget == self:
                    # User clicked the cat or the background -> toggle boxes
                    if self.stacked_pages.isVisible():
                        self.bubble_visible = False
                        self.stacked_pages.hide()
                    else:
                        self.bubble_visible = True
                        self.stacked_pages.show()

    def flip_to_next_page(self):
        """Toggle to the next box in the stack."""
        self.current_page = (self.current_page + 1) % 4
        self.stacked_pages.setCurrentIndex(self.current_page)

    def handle_feeding(self):
        target = self.brain.get_top_offender()
        if target:
            popup = PinkPopup("Confirm Action", f"Do you want to devour\n'{target['name']}'?", self.pixel_font, True, self)
            
            if popup.exec() == QDialog.DialogCode.Accepted:
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
            
            # 1. Immediately enter chonky state when file is dragged onto pet
            self.is_chonky = True
            self.update_display()
            QApplication.processEvents() # Ensure the GUI updates before the blocking dialog
            
            # 2. Show confirmation
            filename = os.path.basename(path)
            popup = PinkPopup("Confirm Feeding", f"Do you want to feed '{filename}' to the pet?\n(This will move the file to the Recycle Bin!)", self.pixel_font, True, self)
            
            # 3. Handle reply
            if popup.exec() == QDialog.DialogCode.Accepted:
                success, message = self.brain.eat_file(path)
                if success:
                    self.brain.pet_thoughts = message
                    self.brain.thought_timer = 20
                    self.update_display()
                    QTimer.singleShot(8000, self.revert_chonky_state) # Stay chonky for 8 seconds
                else:
                    self.brain.pet_thoughts = message
                    self.brain.thought_timer = 20
                    self.revert_chonky_state() # Revert if failed
            else:
                self.revert_chonky_state() # Revert immediately if cancelled

    def revert_chonky_state(self):
        self.is_chonky = False
        self.update_display()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = TamagotchiWidget()
    sys.exit(app.exec())
