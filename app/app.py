from __future__ import annotations

import os
import re
import sys
from importlib.util import find_spec
from dataclasses import dataclass, field
from pathlib import Path


def configure_qt_runtime() -> None:
    spec = find_spec("PySide6")
    if spec is None or spec.origin is None:
        return

    pyside_dir = Path(spec.origin).resolve().parent
    plugin_dir = pyside_dir / "plugins"

    os.environ.setdefault("QT_PLUGIN_PATH", str(plugin_dir))
    os.environ["PATH"] = str(pyside_dir) + os.pathsep + os.environ.get("PATH", "")

    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(str(pyside_dir))
        except OSError:
            pass


configure_qt_runtime()

from PySide6.QtCore import QSignalBlocker, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)
from send2trash import send2trash


SUPPORTED_EXTENSIONS = {".mp3", ".wav"}
MULTI_SPACE = re.compile(r"\s+")


def normalize_title(path: Path) -> str:
    title = path.stem.replace("_", " ").replace("-", " ").lower().strip()
    return MULTI_SPACE.sub(" ", title)


def format_mm_ss(milliseconds: int) -> str:
    total_seconds = max(0, milliseconds // 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


@dataclass
class MusicFileEntry:
    file_name: str
    normalized_title: str
    full_path: Path
    extension: str
    file_size_bytes: int
    folder_path: Path

    @property
    def size_label(self) -> str:
        return f"{self.file_size_bytes / 1024 / 1024:.2f} MB"


@dataclass
class DuplicateGroup:
    normalized_title: str
    entries: list[MusicFileEntry] = field(default_factory=list)
    selected_keep_index: int | None = None

    @property
    def reviewed(self) -> bool:
        return self.selected_keep_index is not None

    @property
    def selected_entry(self) -> MusicFileEntry | None:
        if self.selected_keep_index is None:
            return None
        if self.selected_keep_index < 0 or self.selected_keep_index >= len(self.entries):
            return None
        return self.entries[self.selected_keep_index]


class ClickablePathLabel(QLabel):
    clicked = Signal()

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setWordWrap(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setStyleSheet("color: #1a5fb4;")

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class DuplicateMusicFinderWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Duplicate Music Finder")
        self.resize(1280, 860)

        self.selected_folder = ""
        self.groups: list[DuplicateGroup] = []
        self.process_completed = False
        self.current_group_index: int | None = None
        self.current_track_path: str | None = None
        self.seeking_from_ui = False
        self.audio_available = True

        self.player: QMediaPlayer | None = None
        self.audio_output: QAudioOutput | None = None
        self.initialize_audio()

        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)

        self.choose_folder_button = QPushButton("Choose Folder")
        self.choose_folder_button.clicked.connect(self.choose_folder)

        self.scan_button = QPushButton("Scan")
        self.scan_button.clicked.connect(self.scan_folder)

        self.group_list = QListWidget()
        self.group_list.currentRowChanged.connect(self.display_group)

        self.files_table = QTableWidget(0, 6)
        self.files_table.setHorizontalHeaderLabels(["Keep", "File Name", "Folder", "Type", "Size", "Preview"])
        self.files_table.verticalHeader().setVisible(False)
        self.files_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.files_table.setSelectionMode(QTableWidget.NoSelection)
        self.files_table.setFocusPolicy(Qt.NoFocus)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.status_label = QLabel("Select a folder to begin.")
        self.status_label.setWordWrap(True)

        self.total_files_label = QLabel("Files scanned: 0")
        self.duplicate_groups_label = QLabel("Duplicate groups: 0")
        self.skipped_files_label = QLabel("Skipped files: 0")
        self.deleted_files_label = QLabel("Moved to Trash / Recycle Bin: 0")

        self.playback_label = QLabel("Nothing playing.")
        self.timeline_label = QLabel("00:00 / 00:00")

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setEnabled(False)
        self.seek_slider.sliderPressed.connect(self.on_seek_started)
        self.seek_slider.sliderReleased.connect(self.on_seek_released)

        self.stop_button = QPushButton("Stop Playback")
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setEnabled(False)

        self.delete_button = QPushButton("Send Unselected Files To Trash / Recycle Bin")
        self.delete_button.clicked.connect(self.delete_unselected)
        self.delete_button.setEnabled(False)

        self._build_ui()
        self.apply_audio_availability()

    def initialize_audio(self) -> None:
        try:
            self.player = QMediaPlayer(self)
            self.audio_output = QAudioOutput(self)
            self.player.setAudioOutput(self.audio_output)
            self.audio_output.setVolume(0.85)

            self.position_timer = QTimer(self)
            self.position_timer.setInterval(250)
            self.position_timer.timeout.connect(self.refresh_timeline)

            self.player.positionChanged.connect(self.on_position_changed)
            self.player.durationChanged.connect(self.on_duration_changed)
            self.player.playbackStateChanged.connect(self.on_playback_state_changed)
            self.player.sourceChanged.connect(self.on_source_changed)
            self.player.mediaStatusChanged.connect(self.on_media_status_changed)
            self.player.errorOccurred.connect(self.on_player_error)
            self.audio_available = True
        except Exception:
            self.position_timer = QTimer(self)
            self.audio_available = False

    def apply_audio_availability(self) -> None:
        if self.audio_available:
            return

        self.playback_label.setText("Audio preview is unavailable on this system.")
        self.timeline_label.setText("00:00 / 00:00")
        self.seek_slider.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Audio preview is unavailable. Scanning and duplicate removal still work.")

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        header = QGroupBox()
        header_layout = QHBoxLayout(header)
        title_block = QVBoxLayout()
        title = QLabel("Duplicate Music Finder")
        title.setStyleSheet("font-size: 30px; font-weight: 700;")
        subtitle = QLabel("Scan a folder, listen to duplicate tracks, and choose exactly which copy stays.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #5c5c5c;")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        header_layout.addLayout(title_block, 1)
        credit = QLabel("By @stavik.music")
        credit.setStyleSheet("font-size: 18px; font-weight: 600; color: #8b5a00;")
        header_layout.addWidget(credit, 0, Qt.AlignBottom)
        root.addWidget(header)

        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(self.choose_folder_button)
        folder_row.addWidget(self.scan_button)
        root.addLayout(folder_row)

        content_row = QHBoxLayout()

        summary_box = QGroupBox("Summary")
        summary_layout = QVBoxLayout(summary_box)
        summary_layout.addWidget(self.status_label)
        summary_layout.addSpacing(8)
        summary_layout.addWidget(self.total_files_label)
        summary_layout.addWidget(self.duplicate_groups_label)
        summary_layout.addWidget(self.skipped_files_label)
        summary_layout.addWidget(self.deleted_files_label)
        summary_layout.addSpacing(16)
        summary_layout.addWidget(QLabel("Audio Preview"))
        summary_layout.addWidget(self.playback_label)
        summary_layout.addWidget(self.seek_slider)
        summary_layout.addWidget(self.timeline_label)
        summary_layout.addWidget(self.stop_button)
        summary_layout.addSpacing(16)
        summary_layout.addWidget(self.delete_button)
        summary_layout.addStretch(1)
        content_row.addWidget(summary_box, 0)

        review_box = QGroupBox("Duplicate Groups")
        review_layout = QHBoxLayout(review_box)
        review_layout.addWidget(self.group_list, 1)
        review_layout.addWidget(self.files_table, 3)
        content_row.addWidget(review_box, 1)

        root.addLayout(content_row, 1)

        footer = QLabel("Supported formats: .mp3 and .wav | Recursive scan enabled | Unselected duplicates are sent to Trash / Recycle Bin")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #5c5c5c;")
        root.addWidget(footer)

        self.setCentralWidget(central)

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose Folder To Scan")
        if not folder:
            return

        self.selected_folder = folder
        self.folder_edit.setText(folder)
        self.process_completed = False
        self.update_delete_button_state()
        self.status_label.setText("Folder selected. Ready to scan.")

    def scan_folder(self) -> None:
        if not self.selected_folder or not Path(self.selected_folder).exists():
            QMessageBox.warning(self, "Folder Required", "Please choose a valid folder before scanning.")
            return

        self.stop_playback(reset_status=False)
        self.status_label.setText("Scanning folders and matching duplicate titles...")
        QApplication.processEvents()

        entries: list[MusicFileEntry] = []
        skipped_files = 0

        for root, dirs, files in os.walk(self.selected_folder):
            dirs.sort()
            for file_name in sorted(files):
                path = Path(root) / file_name
                if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                try:
                    stat = path.stat()
                    normalized_title = normalize_title(path)
                    if not normalized_title:
                        skipped_files += 1
                        continue
                    entries.append(
                        MusicFileEntry(
                            file_name=path.name,
                            normalized_title=normalized_title,
                            full_path=path,
                            extension=path.suffix.lower(),
                            file_size_bytes=stat.st_size,
                            folder_path=path.parent,
                        )
                    )
                except OSError:
                    skipped_files += 1

        grouped: dict[str, list[MusicFileEntry]] = {}
        for entry in entries:
            grouped.setdefault(entry.normalized_title, []).append(entry)

        self.groups = [
            DuplicateGroup(title, sorted(group_entries, key=lambda item: str(item.full_path).lower()))
            for title, group_entries in sorted(grouped.items())
            if len(group_entries) > 1
        ]

        self.process_completed = False
        self.current_group_index = None
        self.group_list.clear()
        self.files_table.setRowCount(0)

        for group in self.groups:
            item = QListWidgetItem(f"{group.normalized_title} ({len(group.entries)})")
            self.group_list.addItem(item)

        self.total_files_label.setText(f"Files scanned: {len(entries)}")
        self.duplicate_groups_label.setText(f"Duplicate groups: {len(self.groups)}")
        self.skipped_files_label.setText(f"Skipped files: {skipped_files}")
        self.deleted_files_label.setText("Moved to Trash / Recycle Bin: 0")

        if self.groups:
            self.group_list.setCurrentRow(0)
            self.status_label.setText(f"Scan finished. Review {len(self.groups)} duplicate groups.")
        else:
            self.status_label.setText("Scan finished. No duplicate titles were found.")

        self.update_delete_button_state()

    def display_group(self, row: int) -> None:
        self.files_table.setRowCount(0)
        self.current_group_index = row if 0 <= row < len(self.groups) else None
        if self.current_group_index is None:
            return

        group = self.groups[self.current_group_index]
        self.files_table.setRowCount(len(group.entries))

        for index, entry in enumerate(group.entries):
            keep_button = QPushButton("Keep This")
            keep_button.clicked.connect(lambda _checked=False, group_index=self.current_group_index, entry_index=index: self.select_keep(group_index, entry_index))
            if group.selected_keep_index == index:
                keep_button.setText("Keeping")
                keep_button.setEnabled(False)

            folder_label = ClickablePathLabel(str(entry.folder_path))
            folder_label.clicked.connect(lambda folder=entry.folder_path: self.open_folder(folder))

            preview_button = QPushButton("Play/Pause")
            preview_button.clicked.connect(lambda _checked=False, path=str(entry.full_path): self.play_or_pause(path))

            self.files_table.setCellWidget(index, 0, keep_button)
            self.files_table.setItem(index, 1, QTableWidgetItem(entry.file_name))
            self.files_table.setCellWidget(index, 2, folder_label)
            self.files_table.setItem(index, 3, QTableWidgetItem(entry.extension))
            self.files_table.setItem(index, 4, QTableWidgetItem(entry.size_label))
            self.files_table.setCellWidget(index, 5, preview_button)

        self.files_table.resizeRowsToContents()

    def select_keep(self, group_index: int, entry_index: int) -> None:
        if not (0 <= group_index < len(self.groups)):
            return

        group = self.groups[group_index]
        group.selected_keep_index = entry_index
        self.status_label.setText(f"Selected to keep: {group.entries[entry_index].file_name}")

        current_row = self.group_list.currentRow()
        if current_row == group_index:
            self.display_group(group_index)

        self.refresh_group_labels()
        self.update_delete_button_state()

    def open_folder(self, folder: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def refresh_group_labels(self) -> None:
        for index, group in enumerate(self.groups):
            suffix = "reviewed" if group.reviewed else "choose one"
            item = self.group_list.item(index)
            if item is not None:
                item.setText(f"{group.normalized_title} ({len(group.entries)}) - {suffix}")

    def play_or_pause(self, path: str) -> None:
        if not self.audio_available or self.player is None:
            QMessageBox.warning(self, "Playback Unavailable", "Audio preview is not available on this system.")
            return

        if self.current_track_path != path:
            self.player.setSource(QUrl.fromLocalFile(path))
            self.current_track_path = path
            self.player.play()
            self.position_timer.start()
            self.status_label.setText(f"Playing: {Path(path).name}")
            return

        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.position_timer.stop()
            self.status_label.setText(f"Paused: {Path(path).name}")
        else:
            self.player.play()
            self.position_timer.start()
            self.status_label.setText(f"Playing: {Path(path).name}")

    def stop_playback(self, reset_status: bool = True) -> None:
        if self.player is None:
            return

        self.position_timer.stop()
        self.player.stop()
        self.player.setSource(QUrl())
        self.current_track_path = None
        self.stop_button.setEnabled(False)

        with QSignalBlocker(self.seek_slider):
            self.seek_slider.setRange(0, 0)
            self.seek_slider.setValue(0)

        self.timeline_label.setText("00:00 / 00:00")
        self.playback_label.setText("Nothing playing.")
        if reset_status and not self.groups:
            self.status_label.setText("Select a folder to begin.")

    def delete_unselected(self) -> None:
        if self.process_completed:
            return

        if not self.groups or any(not group.reviewed for group in self.groups):
            QMessageBox.warning(self, "Selection Required", "Choose one file to keep in every duplicate group before deleting.")
            return

        answer = QMessageBox.question(
            self,
            "Confirm Removal",
            "The unselected duplicate files will be sent to Trash / Recycle Bin. Continue?",
        )
        if answer != QMessageBox.Yes:
            return

        self.stop_playback(reset_status=False)

        deleted_files = 0
        kept_files = 0
        for group in self.groups:
            selected = group.selected_entry
            if selected is None:
                continue

            kept_files += 1
            for entry in group.entries:
                if entry.full_path == selected.full_path:
                    continue
                send2trash(str(entry.full_path))
                deleted_files += 1

        self.deleted_files_label.setText(f"Moved to Trash / Recycle Bin: {deleted_files}")
        self.group_list.clear()
        self.files_table.setRowCount(0)
        self.groups = []
        self.current_group_index = None
        self.process_completed = True
        self.duplicate_groups_label.setText("Duplicate groups: 0")
        self.status_label.setText(f"Finished. Kept {kept_files} files and moved {deleted_files} duplicates to Trash / Recycle Bin.")
        self.update_delete_button_state()

    def update_delete_button_state(self) -> None:
        can_delete = bool(self.groups) and not self.process_completed and all(group.reviewed for group in self.groups)
        self.delete_button.setEnabled(can_delete)

    def on_position_changed(self, position: int) -> None:
        if self.player is None:
            return

        if self.seeking_from_ui:
            return

        with QSignalBlocker(self.seek_slider):
            self.seek_slider.setValue(position)
        self.timeline_label.setText(f"{format_mm_ss(position)} / {format_mm_ss(self.player.duration())}")

    def on_duration_changed(self, duration: int) -> None:
        if self.player is None:
            return

        with QSignalBlocker(self.seek_slider):
            self.seek_slider.setRange(0, max(duration, 0))
        self.seek_slider.setEnabled(duration > 0 and self.current_track_path is not None)
        self.timeline_label.setText(f"{format_mm_ss(self.player.position())} / {format_mm_ss(duration)}")

    def on_playback_state_changed(self, _state: QMediaPlayer.PlaybackState) -> None:
        if self.player is None:
            return

        if self.current_track_path is None:
            self.playback_label.setText("Nothing playing.")
            self.stop_button.setEnabled(False)
            return

        state = self.player.playbackState()
        name = Path(self.current_track_path).name
        self.stop_button.setEnabled(True)
        if state == QMediaPlayer.PlayingState:
            self.playback_label.setText(f"Playing: {name}")
        elif state == QMediaPlayer.PausedState:
            self.playback_label.setText(f"Paused: {name}")
        else:
            self.playback_label.setText(f"Ready: {name}")

    def on_source_changed(self, _source: QUrl) -> None:
        has_source = self.current_track_path is not None
        self.stop_button.setEnabled(has_source)

    def on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.EndOfMedia:
            self.stop_playback(reset_status=False)

    def on_seek_started(self) -> None:
        self.seeking_from_ui = True

    def on_seek_released(self) -> None:
        if self.player is None:
            self.seeking_from_ui = False
            return

        self.player.setPosition(self.seek_slider.value())
        self.timeline_label.setText(f"{format_mm_ss(self.seek_slider.value())} / {format_mm_ss(self.player.duration())}")
        self.seeking_from_ui = False

    def refresh_timeline(self) -> None:
        if self.player is None:
            return

        if self.current_track_path is None:
            return
        self.timeline_label.setText(f"{format_mm_ss(self.player.position())} / {format_mm_ss(self.player.duration())}")

    def on_player_error(self, _error: QMediaPlayer.Error, error_string: str) -> None:
        failed_file_name = Path(self.current_track_path).name if self.current_track_path else "This file"
        self.position_timer.stop()
        self.current_track_path = None
        self.stop_button.setEnabled(False)
        with QSignalBlocker(self.seek_slider):
            self.seek_slider.setRange(0, 0)
            self.seek_slider.setValue(0)
        self.timeline_label.setText("00:00 / 00:00")
        self.playback_label.setText("Nothing playing.")
        self.status_label.setText("Playback failed for this file.")

        friendly_message = (
            f"{failed_file_name} could not be played.\n\n"
            "It may be corrupted, incomplete, or not a real MP3/WAV file."
        )
        if error_string:
            friendly_message += f"\n\nDetails: {error_string}"

        QMessageBox.warning(self, "Could Not Play File", friendly_message)


def main() -> int:
    app = QApplication(sys.argv)
    window = DuplicateMusicFinderWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
