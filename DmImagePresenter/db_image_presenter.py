# main.py

from PySide6.QtWidgets import (
    QApplication, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QLabel, QTabWidget,
    QListWidgetItem, QFileDialog, QAbstractItemView, QMainWindow, QToolButton, QStyle
)
from PySide6.QtGui import QPixmap, QIcon, QPainter, QImageReader, QImage
from PySide6.QtCore import Qt, QSize, QObject, Signal
import sys
import os
from typing import List, Optional

class ResizableLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ImageDisplayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Display")
        self.image_label = ResizableLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.image_label)

    def update_image(self, pixmap: QPixmap):
        self.image_label.setPixmap(pixmap)

class StagingTab(QWidget):
    # Define a custom signal
    update_output_image_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_images = []  # type: List[str]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.preview_label = ResizableLabel("No image selected")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setObjectName("previewLabel")
        layout.addWidget(self.preview_label)

        self.update_button = QPushButton("Update Output Image")
        # Connect the button to the custom signal
        self.update_button.clicked.connect(self.update_output_image_signal)
        self.update_button.setObjectName("updateButton")
        layout.addWidget(self.update_button)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("D&D Image Manager")
        self.image_display_window = None  # type: Optional[ImageDisplayWindow]
        self.image_paths = []  # type: List[str]
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Create the main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        # Left side widgets
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_widget.setLayout(left_layout)
        left_widget.setObjectName("leftWidget")

        # Folder chooser button
        self.folder_button = QPushButton()
        # Corrected the icon retrieval
        self.folder_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.folder_button.setFixedSize(30, 30)
        self.folder_button.setObjectName("folderButton")
        self.folder_button.clicked.connect(self.choose_folder)
        left_layout.addWidget(self.folder_button)

        # Filter text field
        self.filter_text = QLineEdit()
        self.filter_text.setPlaceholderText("Filter images...")
        self.filter_text.textChanged.connect(self.filter_images)
        self.filter_text.setObjectName("filterText")
        left_layout.addWidget(self.filter_text)

        # File list
        self.file_list = QListWidget()
        # Change selection mode to ExtendedSelection
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.itemSelectionChanged.connect(self.update_preview)
        self.file_list.setObjectName("fileList")
        left_layout.addWidget(self.file_list)

        # Set larger icon size for thumbnails
        self.thumbnail_size = QSize(128, 128)
        self.file_list.setIconSize(self.thumbnail_size)

        # Add left widget to splitter
        main_splitter.addWidget(left_widget)

        # Right side widgets
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setObjectName("rightSplitter")

        # Top-right: Tab widget for staging images
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.tab_widget.setObjectName("tabWidget")
        right_splitter.addWidget(self.tab_widget)

        # Add a button to add new tabs
        self.add_tab_button = QToolButton()
        self.add_tab_button.setText("+")
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)

        # Add the first tab
        self.add_new_tab()

        # Bottom-right: Output preview
        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_widget.setLayout(output_layout)
        output_widget.setObjectName("outputWidget")

        self.output_label = ResizableLabel("No image selected")
        self.output_label.setAlignment(Qt.AlignCenter)
        self.output_label.setObjectName("outputLabel")
        output_layout.addWidget(self.output_label)

        # Buttons for controlling the output display
        button_layout = QHBoxLayout()
        self.open_window_button = QPushButton("Open Separate Window")
        self.open_window_button.clicked.connect(self.open_separate_window)
        self.open_window_button.setObjectName("openWindowButton")
        button_layout.addWidget(self.open_window_button)

        self.fullscreen_button = QPushButton("Show Full Screen")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_button.setObjectName("fullscreenButton")
        button_layout.addWidget(self.fullscreen_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_output)
        self.clear_button.setObjectName("clearButton")
        button_layout.addWidget(self.clear_button)

        output_layout.addLayout(button_layout)

        right_splitter.addWidget(output_widget)

        # Add right splitter to main splitter
        main_splitter.addWidget(right_splitter)

        # Set initial sizes
        main_splitter.setStretchFactor(1, 1)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 1)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.load_images_from_folder(folder)

    def load_images_from_folder(self, folder_path: str):
        self.image_paths = []  # type: List[str]
        allowed_extensions = ('.png', '.jpg', '.jpeg', '.bmp')

        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(allowed_extensions):
                    full_path = os.path.join(root, file)
                    self.image_paths.append(full_path)

        self.display_images_in_list()

    def display_images_in_list(self):
        self.file_list.clear()
        filter_text = self.filter_text.text().lower()

        for image_path in self.image_paths:
            file_name = os.path.basename(image_path)
            base_name = os.path.splitext(file_name)[0]

            if filter_text in base_name.lower():
                item = QListWidgetItem()
                item.setText(base_name)
                item.setData(Qt.UserRole, image_path)
                item.setToolTip(image_path)

                # Generate and set thumbnail
                thumbnail = self.generate_thumbnail(image_path)
                if not thumbnail.isNull():
                    item.setIcon(QIcon(thumbnail))
                else:
                    # Use a placeholder icon if the image fails to load
                    item.setIcon(QIcon())

                self.file_list.addItem(item)

    def generate_thumbnail(self, image_path: str) -> QPixmap:
        # Generate a thumbnail without loading the full image into memory
        reader = QImageReader(image_path)
        reader.setAutoDetectImageFormat(True)
        reader.setScaledSize(self.thumbnail_size)
        image = reader.read()
        if not image.isNull():
            return QPixmap.fromImage(image)
        else:
            return QPixmap()

    def filter_images(self):
        self.display_images_in_list()

    def update_preview(self):
        # Get the current tab
        current_tab = self.tab_widget.currentWidget()
        if not current_tab:
            return

        # Store the selected images for the current tab
        selected_items = self.file_list.selectedItems()
        selected_image_paths = []
        if len(selected_items) > 4:
            # Limit selection to 4 items
            selected_items = selected_items[:4]

        for item in selected_items:
            image_path = item.data(Qt.UserRole)
            selected_image_paths.append(image_path)

        current_tab.selected_images = selected_image_paths
        self.update_tab_preview(current_tab)

    def update_tab_preview(self, tab):
        if not tab.selected_images:
            tab.preview_label.setText("No image selected")
            tab.preview_label.setPixmap(QPixmap())
            return

        pixmaps = []
        for image_path in tab.selected_images:
            pixmap = self.load_full_image(image_path)
            if not pixmap.isNull():
                pixmaps.append(pixmap)

        # Create a combined image based on the number of selected images
        combined_pixmap = self.combine_images(pixmaps, tab.preview_label.size())
        tab.preview_label.setPixmap(combined_pixmap)

    def load_full_image(self, image_path: str) -> QPixmap:
        # Load the full-resolution image from the file
        return QPixmap(image_path)

    def combine_images(self, pixmaps: List[QPixmap], target_size: QSize) -> QPixmap:
        if not pixmaps:
            return QPixmap()

        count = len(pixmaps)
        target_width = target_size.width()
        target_height = target_size.height()

        if count == 1:
            # Scale the image to fill the widget while maintaining aspect ratio
            return pixmaps[0].scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif count == 2 or count == 3:
            # Arrange images horizontally
            # Scale images to have the same height
            max_height = target_height
            scaled_pixmaps = []
            total_width = 0
            for pixmap in pixmaps:
                scaled_pixmap = pixmap.scaledToHeight(max_height, Qt.SmoothTransformation)
                scaled_pixmaps.append(scaled_pixmap)
                total_width += scaled_pixmap.width()

            # Adjust scaling if total width exceeds target width
            if total_width > target_width:
                scaling_factor = target_width / total_width
                scaled_pixmaps = [
                    pixmap.scaled(
                        pixmap.width() * scaling_factor,
                        pixmap.height() * scaling_factor,
                        Qt.IgnoreAspectRatio,
                        Qt.SmoothTransformation
                    ) for pixmap in scaled_pixmaps
                ]
                max_height = scaled_pixmaps[0].height()
                total_width = sum([pixmap.width() for pixmap in scaled_pixmaps])

            combined = QPixmap(int(total_width), int(max_height))
            combined.fill(Qt.transparent)
            painter = QPainter(combined)

            x_offset = 0
            for pixmap in scaled_pixmaps:
                painter.drawPixmap(int(x_offset), 0, pixmap)
                x_offset += pixmap.width()

            painter.end()

            # Scale the combined image to fill the widget
            return combined.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif count == 4:
            # Arrange images in a 2x2 grid
            # Scale images to fit half of the target size
            half_width = target_width / 2
            half_height = target_height / 2
            scaled_pixmaps = [
                pixmap.scaled(
                    half_width, half_height,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                ) for pixmap in pixmaps
            ]

            combined = QPixmap(int(target_width), int(target_height))
            combined.fill(Qt.transparent)
            painter = QPainter(combined)

            positions = [
                (0, 0), (half_width, 0),
                (0, half_height), (half_width, half_height)
            ]
            for pixmap, (x, y) in zip(scaled_pixmaps, positions):
                painter.drawPixmap(int(x), int(y), pixmap)

            painter.end()
            return combined
        else:
            return QPixmap()

    def add_new_tab(self):
        new_tab = StagingTab()
        # Connect the custom signal to the update_output_image method
        new_tab.update_output_image_signal.connect(self.update_output_image)
        index = self.tab_widget.addTab(new_tab, f"Tab {self.tab_widget.count() + 1}")
        self.tab_widget.setCurrentIndex(index)

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)

    def update_output_image(self):
        current_tab = self.tab_widget.currentWidget()
        if not current_tab:
            return

        if not current_tab.selected_images:
            self.output_label.setText("No image selected")
            self.output_label.setPixmap(QPixmap())
            if self.image_display_window:
                self.image_display_window.image_label.clear()
            return

        # Load full-resolution images for output
        pixmaps = []
        for image_path in current_tab.selected_images:
            pixmap = self.load_full_image(image_path)
            if not pixmap.isNull():
                pixmaps.append(pixmap)

        # Combine images and scale to fill the output label
        combined_pixmap = self.combine_images(pixmaps, self.output_label.size())
        self.output_label.setPixmap(combined_pixmap)

        # Update the separate window
        if self.image_display_window:
            # Combine images and scale to fill the window size
            window_size = self.image_display_window.size()
            combined_pixmap_full = self.combine_images(pixmaps, window_size)
            self.image_display_window.update_image(combined_pixmap_full)

    def open_separate_window(self):
        if not self.image_display_window:
            self.image_display_window = ImageDisplayWindow()
        self.image_display_window.show()

    def toggle_fullscreen(self):
        if self.image_display_window:
            if self.image_display_window.isFullScreen():
                self.image_display_window.showNormal()
                self.fullscreen_button.setText("Show Full Screen")
            else:
                self.image_display_window.showFullScreen()
                self.fullscreen_button.setText("Exit Full Screen")

    def clear_output(self):
        self.output_label.clear()
        self.output_label.setText("No image selected")
        if self.image_display_window:
            self.image_display_window.image_label.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Resize the images in the output label
        pixmap = self.output_label.pixmap()
        if pixmap:
            scaled_pixmap = pixmap.scaled(
                self.output_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.output_label.setPixmap(scaled_pixmap)

    def on_tab_changed(self, index):
        # When the tab changes, update the file list selection to match the tab's selected images
        current_tab = self.tab_widget.widget(index)
        if not current_tab:
            return

        # Disconnect the signal to prevent recursive calls
        self.file_list.itemSelectionChanged.disconnect(self.update_preview)

        # Clear the current selection
        self.file_list.clearSelection()

        # Select the items corresponding to the tab's selected images
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            image_path = item.data(Qt.UserRole)
            if image_path in current_tab.selected_images:
                item.setSelected(True)

        # Reconnect the signal
        self.file_list.itemSelectionChanged.connect(self.update_preview)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
