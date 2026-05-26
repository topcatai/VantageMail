# -*- coding: utf-8 -*-

from pathlib import Path
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt, QEvent, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QApplication
)

class SplashScreen(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(400, 400)
        self.setStyleSheet("background-color: #ffffff;")
        
        # Center the dialog on the screen
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - 400) // 2
            y = (screen_geometry.height() - 400) // 2
            self.move(x, y)

        base = Path("icons_Vantage Mail")
        video_path = base / "Vantage_Loading_Logo.mp4"

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Video Widget (Sized to fill the entire 400x400 dialog)
        self.video_widget = QVideoWidget()
        self.video_widget.setFixedSize(400, 400)
        self.video_widget.setStyleSheet("background-color: #ffffff;")
        main_layout.addWidget(self.video_widget)

        # Install event filter to capture clicks on the video widget
        self.video_widget.installEventFilter(self)

        # QMediaPlayer setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Play the video exactly once
        self.media_player.setLoops(1)
        
        # Signal connections
        self.media_player.errorOccurred.connect(self._on_video_error)
        self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)

        if video_path.exists():
            self.media_player.setSource(QUrl.fromLocalFile(str(video_path.resolve())))
            self.media_player.play()
        else:
            QTimer.singleShot(0, self.accept)

        self.setLayout(main_layout)

    def eventFilter(self, obj, event):
        # Capture mouse press events on the video player
        if event.type() == QEvent.Type.MouseButtonPress:
            self.accept()
            return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        # Capture clicks on the dialog window
        self.accept()

    def _on_video_error(self, error, error_string):
        print(f"Video play error: {error_string}")
        self.accept()

    def _on_media_status_changed(self, status):
        # Auto-accept and close splash when video completes playing once
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.accept()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.accept()

    def accept(self):
        self.media_player.stop()
        super().accept()
