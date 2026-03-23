import sys
import os
import datetime
import shutil
import base64
import pyautogui
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QMessageBox, QFileDialog, QStackedWidget
from PyQt6.QtCore import Qt, QTimer, QPoint, QBuffer, QIODeviceBase
from PyQt6.QtGui import QFont, QPixmap, QFontDatabase, QMovie, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from src.pet_brain import PetBrain


class WebFlipWidget(QWidget):
    """Transparent overlay that plays a CSS 3D book-page-flip transition."""

    ANIM_MS = 850   # CSS animation duration in ms

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        self.w, self.h = parent.width(), parent.height()
        self.setGeometry(0, 0, self.w, self.h)
        self.hide() # Initially hidden

        self._view = QWebEngineView(self)
        self._view.page().setBackgroundColor(QColor(0, 0, 0, 0))
        self._view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._view.resize(self.w, self.h)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._finish)

        html = f"""<!DOCTYPE html>
<html><head><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {
  width: {self.w}px; height: {self.h}px;
  overflow: hidden;
  background: rgba(177, 156, 217, 0);
}
.scene {
  width: {self.w}px; height: {self.h}px;
  perspective: 700px;
}
.page {{
  width: 100%; height: 100%;
  position: relative;
  transform-style: preserve-3d;
  transform-origin: left center;
  box-shadow: 4px 6px 16px rgba(177,156,217,0.7);
}}
@keyframes flipPage {{
  0%   {{ transform: rotateY(0deg);    }}
  45%  {{ box-shadow: 20px 10px 35px rgba(177,156,217,0.95); }}
  100% {{ transform: rotateY(-180deg); box-shadow: 4px 6px 16px rgba(177,156,217,0.7); }}
}}
.face {{
  position: absolute;
  width: 100%; height: 100%;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  overflow: hidden;
}}
.back {{ transform: rotateY(180deg); }}
img {{ width: 100%; height: 100%; display: block; object-fit: fill; }}
</style></head>
<body>
  <div class="scene">
    <div class="page" id="pg">
      <div class="face"><img id="imgFront" src=""/></div>
      <div class="face back"><img id="imgBack" src=""/></div>
    </div>
  </div>
</body></html>"""
        
        self._is_ready = False
        def set_ready(*args):
            self._is_ready = True
            
        self._view.loadFinished.connect(set_ready)
        self._view.setHtml(html)

    def pix_to_b64(self, pix):
        buf = QBuffer()
        buf.open(QIODeviceBase.OpenModeFlag.WriteOnly)
        pix.save(buf, "PNG")
        return base64.b64encode(bytes(buf.data())).decode()

    def play_flip(self, from_pixmap, to_pixmap, on_done):
        if not self._is_ready:
            # If still booting up chromium, just skip transition
            on_done()
            return
            
        self._on_done = on_done
        from_b64 = self.pix_to_b64(from_pixmap)
        to_b64   = self.pix_to_b64(to_pixmap)

        self.raise_()
        self.show()
        
        # Inject images and replay animation
        js = f"""
        document.getElementById('imgFront').src = "data:image/png;base64,{from_b64}";
        document.getElementById('imgBack').src  = "data:image/png;base64,{to_b64}";
        var pg = document.getElementById('pg');
        pg.style.animation = 'none';
        pg.offsetHeight; /* trigger reflow */
        pg.style.animation = 'flipPage {self.ANIM_MS}ms cubic-bezier(0.645,0.045,0.355,1.0) forwards';
        """
        self._view.page().runJavaScript(js)
        self._timer.start(self.ANIM_MS + 50)

    def _finish(self):
        self.hide()
        if self._on_done:
            self._on_done()


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
        self._is_flipping = False
        self.current_page = 0
        self._is_flipping = False

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
        self.layout.setSpacing(-80) # Overlap boxes onto the image
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
        self.layers_layout.setContentsMargins(19, 36, 27, 4)
        self.layers_layout.setSpacing(0)
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
        
        self.stats_title_label = QLabel("[SYSTEM MONITOR]", self.stats_container)
        self.stats_title_label.setGeometry(55, 3, 110, 22)
        self.stats_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_title_label.setFont(QFont(self.pixel_font, 11))
        self.stats_title_label.setStyleSheet("color: #4B0082; font-weight: bold; background: transparent; border: none;")
        
        self.stats_inner_layout = QVBoxLayout()
        self.stats_inner_layout.setContentsMargins(13, 20, 33, 14)
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

        # --- MUSIC CONTAINER ---
        self.music_container = QWidget()
        self.music_container.setObjectName("MusicBox")
        self.music_container.setFixedSize(180, 145)
        self.music_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.music_layout = QVBoxLayout()
        self.music_layout.setContentsMargins(13, 20, 33, 14)
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
            
        self.music_title_label = QLabel("[MEDIA REMOTE]", self.music_container)
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
        self.music_layout.setContentsMargins(19, 30, 27, 14)
        
        self.music_layout.addLayout(self.music_controls_layout)
        self.music_container.setLayout(self.music_layout)
        # --- STACKED WIDGET ---
        self.stacked_pages = QStackedWidget()
        self.stacked_pages.setFixedSize(220, 160)
        
        # Give pages a transparent background so the curl renders cleanly
        self.speech_container.setStyleSheet(self.speech_style + "\nbackground: transparent;")
        self.stats_container.setStyleSheet(self.stats_style + "\nbackground: transparent;")
        self.music_container.setStyleSheet(self.music_style + "\nbackground: transparent;")
        
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

        # Determine Sprite state with proper priority
        if stats['status'] == "FATAL ERROR 🪦":
            img, status = "dead", "DEAD 💀"
        elif not stats['plugged_in'] and stats['battery'] < 20:
            img, status = "dead", "LOW BATT 🪦"
        elif self.brain.overclocking:
            monster_uri = os.path.join(self.assets_dir, "monsterdrink.png").replace('\\', '/')
            img, status = "stressed", f"OVERCLOCK <img src='{monster_uri}' width='14' height='14' align='middle'>"
        elif current_hour >= 23 or current_hour < 6:
            img, status = "sleepy", "SLEEPY 😴"
        elif self.is_chonky:
            img, status = "chonky", "CHONKY 🍔"
        elif stats['cpu'] > 85 or stats['ram'] > 85:
            img, status = "stressed", "STRESSED 🥵"
        else:
            img, status = "chillin", "CHILLIN 😎"

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
        if "LOW BATT" in status or "DEAD" in status:
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
                cropped = scaled.copy(0, 40, scaled.width(), scaled.height() - 40)
                self.sprite_label.setPixmap(cropped)
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
                if not self.bubble_visible:
                    self.bubble_visible = True
                    self.stacked_pages.show()
                else:
                    # Trigger smooth 3D page flip
                    self.flip_to_next_page()

    def flip_to_next_page(self):
        """Grab pixmaps of current and next pages, then run the 3D curl animation."""
        if self._is_flipping:
            return   # ignore clicks while animation is running
        self._is_flipping = True
        next_page = (self.current_page + 1) % 3

        # Ensure overlay exists
        if not hasattr(self, 'flip_overlay'):
            self.flip_overlay = WebFlipWidget(self.stacked_pages)

        # Grab the current (from) page
        from_pix = self.stacked_pages.grab()

        # Briefly switch to next page to grab its appearance silently
        self.stacked_pages.setCurrentIndex(next_page)
        to_pix = self.stacked_pages.grab()
        self.stacked_pages.setCurrentIndex(self.current_page)

        def on_done():
            self.current_page = next_page
            self.stacked_pages.setCurrentIndex(next_page)
            self._is_flipping = False   # allow next flip

        self.flip_overlay.play_flip(from_pix, to_pix, on_done)

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
            
            # 1. Immediately enter chonky state when file is dragged onto pet
            self.is_chonky = True
            self.update_display()
            QApplication.processEvents() # Ensure the GUI updates before the blocking dialog
            
            # 2. Show confirmation
            filename = os.path.basename(path)
            reply = QMessageBox.question(
                self, "Confirm Feeding",
                f"Do you want to feed '{filename}' to the pet?\n(This will move the file to the Recycle Bin!)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            # 3. Handle reply
            if reply == QMessageBox.StandardButton.Yes:
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
