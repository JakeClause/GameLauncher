import sys
import os
import json
import subprocess
from datetime import datetime
import win32com.client

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QScrollArea,
    QGridLayout, QPushButton, QFileDialog, QListWidget, QDialog, QLineEdit, QMenu, QSplashScreen, QSystemTrayIcon
)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QCursor
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, QObject, pyqtSignal, QTimer

def load_image(image_path):
    image = QImage(image_path)
    if image.isNull():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    image = image.convertToFormat(QImage.Format_RGB888)
    return QPixmap.fromImage(image)

class SettingsDialog(QDialog):
    dark_mode_changed = pyqtSignal(bool)
    online_games_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.parent_app = parent

        self.layout = QVBoxLayout(self)

        self.directory_label = QLabel("Directories:")
        self.layout.addWidget(self.directory_label)
        self.directory_list_widget = QListWidget()
        self.layout.addWidget(self.directory_list_widget)

        self.add_directory_button = QPushButton("Add Directory")
        self.add_directory_button.clicked.connect(self.add_directory)
        self.layout.addWidget(self.add_directory_button)
        self.remove_directory_button = QPushButton("Remove Directory")
        self.remove_directory_button.clicked.connect(self.remove_directory)
        self.layout.addWidget(self.remove_directory_button)

        self.dark_mode_button = QPushButton("Toggle Dark Mode")
        self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
        self.layout.addWidget(self.dark_mode_button)

        self.show_online_games_button = QPushButton("Toggle Online Games")
        self.show_online_games_button.clicked.connect(self.toggle_online_games)
        self.layout.addWidget(self.show_online_games_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.layout.addWidget(self.cancel_button)

        self.dark_mode = False
        self.show_online_games = False
        self.load_settings()
        self.load_directories_list()
        self.update_styles()

    def add_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.directory_list_widget.addItem(directory)

    def remove_directory(self):
        selected_item = self.directory_list_widget.currentItem()
        if selected_item:
            self.directory_list_widget.takeItem(self.directory_list_widget.row(selected_item))

    def toggle_online_games(self):
        self.show_online_games = not self.show_online_games
        self.online_games_toggled.emit(self.show_online_games)
        self.load_directories_list() 

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.update_styles()
        self.dark_mode_changed.emit(self.dark_mode)

    def update_styles(self):
        bg_color = "#26242f" if self.dark_mode else "darkGrey"
        fg_color = "white" if self.dark_mode else "black"
        self.setStyleSheet(f"background-color: {bg_color}; color: {fg_color};")

        for widget in [self.directory_label, self.save_button, self.cancel_button, self.add_directory_button, self.remove_directory_button, self.dark_mode_button, self.show_online_games_button]:
            widget.setStyleSheet(f"color: {fg_color};")

        self.directory_list_widget.setStyleSheet(f"color: {fg_color};")

    def load_directories_list(self):
        self.directory_list_widget.clear()
        filename = "settings.json"
        if os.path.exists(filename):
            with open(filename, "r") as file:
                settings = json.load(file)
                selected_directories = settings.get("selected_directories", [])
                for directory in selected_directories:
                    self.directory_list_widget.addItem(directory)

                online_games_dir = "C:/Users/jakec/Desktop/CS/.PERSONAL PROJECTS/GAMEGUI/Online Games"
                if self.show_online_games and online_games_dir not in selected_directories:
                    self.directory_list_widget.addItem(online_games_dir)
                elif not self.show_online_games:
                    for i in range(self.directory_list_widget.count()):
                        if self.directory_list_widget.item(i).text() == online_games_dir:
                            self.directory_list_widget.takeItem(i)
                            break

    def load_settings(self):
        filename = "settings.json"
        if os.path.exists(filename):
            with open(filename, "r") as file:
                settings = json.load(file)
                self.dark_mode = settings.get("dark_mode", False)
                self.show_online_games = settings.get("show_online_games", False)
                self.display_style = settings.get("display_style", "grid")
                print(f"Loaded settings: {settings}")

    def save_settings(self):
        settings = {
            "dark_mode": self.dark_mode,
            "selected_directories": [self.directory_list_widget.item(i).text() for i in range(self.directory_list_widget.count())],
            "display_style": self.display_style,
            "show_online_games": self.show_online_games
        }

        filename = "settings.json"
        with open(filename, "w") as file:
            json.dump(settings, file)
        print(f"Saved settings: {settings}")

class GameLauncherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Launcher")
        self.setGeometry(100, 100, 800, 600)
        self.default_settings = {
            'dark_mode': True,
            'selected_directories': ["E:/Video Games/Games", "F:/GAMES"],
            'current_directory': "E:/Video Games/Games"
        }
        self.dark_mode = False
        self.show_online_games_button = False
        self.tray_icon = None  # Initialize tray_icon to None
        self.selected_directories = ["E:/Video Games/Games", "F:/GAMES"]
        self.current_directory = self.selected_directories[0]
        self.showFullScreen()
        self.scroll_style = "horizontal"
         # Initialize game_count_label here
        self.game_count_label = QLabel("", self)
        self.load_settings()
        self.initUI()
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.dark_mode_changed.connect(self.update_dark_mode_ui)
        self.settings_dialog.online_games_toggled.connect(self.update_online_games)  # Connect online_games_toggled signal
        self.settings_dialog.finished.connect(self.refresh_ui)
        self.settings_dialog.finished.connect(self.update_game_list)  # Connect finished signal to refresh_ui slot
        self.tray_icon = self.create_tray_icon()
        self.tray_icon.show()
        self.update_colors()

    def update_online_games(self, show_online_games):
        self.show_online_games = show_online_games
        self.update_game_list()  # Refresh game list when online games setting changes


    def refresh_ui(self):
        self.update_colors()
        self.update_game_list()

    def update_game_list(self):
        self.create_frame()  # Clear existing game cards
        self.display_all_games()  # Display updated game cards

    def update_dark_mode_ui(self, dark_mode):
        self.dark_mode = dark_mode
        self.update_colors() 

    
    def create_tray_icon(self):
        tray_icon = QSystemTrayIcon(self)
        tray_icon.setIcon(QIcon('./icon (png).png'))
        tray_icon.setToolTip("Game Launcher")
        
        # Create a context menu for the tray icon
        tray_menu = QMenu()
        restore_action = tray_menu.addAction("Restore")
        quit_action = tray_menu.addAction("Quit")
        
        restore_action.triggered.connect(self.restore_and_refresh)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_icon.setContextMenu(tray_menu)

        # Optional: Connect the tray icon's activated signal to handle clicks
        tray_icon.activated.connect(self.tray_icon_activated)

        return tray_icon

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.restore_and_refresh()  # Restore the window if the tray icon is clicked

    def restore_and_refresh(self):
        self.showNormal()  # Show the main window
        self.showFullScreen()  # Bring it to the front
        self.raise_()  # Ensure it is raised above other windows

    # def create_tray_icon(self):
    #     tray_icon = QSystemTrayIcon(self)
    #     tray_icon.setIcon(QIcon('./icon (png).png'))
    #     tray_icon.setToolTip("Game Launcher")
        
    #     # Create a context menu for the tray icon
    #     tray_menu = QMenu()
    #     restore_action = tray_menu.addAction("Restore")
    #     quit_action = tray_menu.addAction("Quit")
        
    #     restore_action.triggered.connect(self.restore_and_refresh)
    #     quit_action.triggered.connect(QApplication.instance().quit)
        
    #     tray_icon.setContextMenu(tray_menu)
    #     return tray_icon

    def wheelEvent(self, event):
        if self.scroll_style == "horizontal":
            delta = event.angleDelta().y()
            horizontal_scrollbar = self.scroll_area.horizontalScrollBar()
            horizontal_scrollbar.setValue(horizontal_scrollbar.value() - delta)
        else:
            super().wheelEvent(event)

    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)

        self.grid_layout = QGridLayout(self.scroll_content)
        self.scroll_content.setLayout(self.grid_layout)

        self.nav_bar = QHBoxLayout()
        self.game_count_label = QLabel("", self)
        self.nav_bar.addWidget(self.game_count_label)

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search games...")
        self.search_bar.textChanged.connect(self.filter_games)
        self.nav_bar.addWidget(self.search_bar)

        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings)
        self.nav_bar.addWidget(self.settings_button)

        self.scroll_style_button = QPushButton()
        self.scroll_style_button.setIcon(QIcon("layout.jpg"))
        self.scroll_style_button.setFixedSize(25, 25)
        self.scroll_style_button.setIconSize(self.scroll_style_button.size())
        self.scroll_style_button.clicked.connect(self.toggle_scroll_style)
        self.nav_bar.addWidget(self.scroll_style_button)

        self.layout.addLayout(self.nav_bar)

        self.display_all_games()
        self.installEventFilter(self)

        self.settings_dialog = SettingsDialog(self)

    def toggle_scroll_style(self):
        if self.scroll_style == "grid":
            self.scroll_style = "horizontal"
        else:
            self.scroll_style = "grid"
        self.settings_dialog.display_style = self.scroll_style
        self.settings_dialog.save_settings()
        self.display_all_games()

    def update_dark_mode_ui(self, dark_mode):
        self.dark_mode = dark_mode
        self.update_colors()  # Update colors when dark mode is changed
    
    def update_colors(self):
        try:
            with open('settings.json', 'r') as file:
                settings = json.load(file)
                self.dark_mode = settings.get('dark_mode', self.default_settings['dark_mode'])
        except FileNotFoundError:
            self.dark_mode = self.default_settings['dark_mode']

        bg_color = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        self.setStyleSheet(f"background-color: {bg_color};")

        fg_color = "white" if self.dark_mode else "black"
        self.game_count_label.setStyleSheet(f"color: {fg_color};")
        
        # Update text color of game title labels
        for row in range(self.grid_layout.rowCount()):
            for col in range(self.grid_layout.columnCount()):
                item = self.grid_layout.itemAtPosition(row, col)
                if item:
                    widget = item.widget()
                    if widget and hasattr(widget, "layout"):
                        layout = widget.layout()
                        if layout and layout.count() > 1:
                            name_label = layout.itemAt(1).widget()
                            if name_label and isinstance(name_label, QLabel):
                                name_label.setStyleSheet(f"background-color: {self.get_bg_color()}; color: {fg_color};")

        for widget in [self.settings_button, self.search_bar]:
            widget.setStyleSheet(f"color: {fg_color};")

            
    def open_settings(self):
        self.settings_dialog.exec_()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key()== Qt.Key_Escape:
                self.close()
            elif event.key() == Qt.Key_F12:
                self.close()
        return super().eventFilter(obj, event)

    def display_all_games(self):
        self.create_frame()  # Clear existing game cards
        combined_games = []
        for directory in self.selected_directories:
            combined_games.extend(self.get_games_from_directory(directory))

        if self.scroll_style == "grid":
            self.create_application_cards_grid(self.current_directory, self.game_count_label)
        elif self.scroll_style == "horizontal":
            self.create_application_cards_horizontal(self.game_count_label)


    def create_application_cards_grid(self, directory, game_count_label):
        games = []  

        for directory in self.selected_directories:
            games.extend(self.get_games_from_directory(directory))

        games = list(set(games))
        games.sort(key=lambda game: game[0])

        num_cols = 5  
        for index, game in enumerate(games):
            row = index // num_cols
            col = index % num_cols
            name, app_path, image_path = game
            self.create_card(name, app_path, image_path, row, col)

        game_count_label.setText(f"Games: {len(games)}")
        self.current_directory = directory

        # Adjust the stretch factors for rows and columns to prioritize the top-left corner
        if games:
            num_rows = len(games) // num_cols + int(len(games) % num_cols != 0)
            for i in range(num_rows):
                self.grid_layout.setRowStretch(i, 0)  # Set stretch factor for each row to 0
            for j in range(num_cols):
                self.grid_layout.setColumnStretch(j, 1)  # Set stretch factor for each column to 0


    def create_application_cards_horizontal(self, game_count_label):
        games = []
        for directory in self.selected_directories:
            games.extend(self.get_games_from_directory(directory))

        games = list(set(games))
        games.sort(key=lambda game: game[0])

        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setVerticalSpacing(20)
        self.grid_layout.setContentsMargins(20, 200, 20, 20)

        if len(games) == 1:
            col = 0  # Set column index to 0 if there is only one game
        else:
            col = 0
            for index, game in enumerate(games):
                name, app_path, image_path = game
                if index == len(games) - 1:  # If it's the last game
                    col = max(0, col - 1)  # Ensure it appears at the left side of the screen
                self.create_card(name, app_path, image_path, 0, col)
                col += 1

        game_count_label.setText(f"Games: {len(games)}")



    def create_card(self, name, app_path, image_path, row, col):
        card_layout = QVBoxLayout()

        try:
            pixmap = load_image(image_path)
        except Exception as e:
            print(f"Error loading image: {e}")
            pixmap = load_image("default_cover.jpg")

        image_label = QLabel(self)
        if self.scroll_style == "grid":
            image_label.setPixmap(pixmap.scaled(300, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif self.scroll_style == "horizontal":
            image_label.setPixmap(pixmap.scaled(375, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        image_label.setCursor(Qt.PointingHandCursor)
        image_label.mousePressEvent = lambda event, app_path=app_path: self.handle_click(event, app_path)

        name_label = QLabel(name, self)
        name_label.setAlignment(Qt.AlignHCenter)
        name_label.setStyleSheet(f"color: {self.get_fg_color()};")

        card_layout.addWidget(image_label)
        card_layout.addWidget(name_label)

        card_widget = QWidget()
        card_widget.setLayout(card_layout)
        card_widget.setMaximumHeight(550)
        card_widget.setStyleSheet(f"""
            background-color: {self.get_bg_color()};
            border-radius: 10px;
            padding: 5px;
            margin: 10px;
        """)
        self.grid_layout.addWidget(card_widget, row, col)

    def handle_click(self, event, app_path):
        if event.button() == Qt.LeftButton:
            self.launch(app_path)
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event, app_path)

    def show_context_menu(self, event, app_path):
        context_menu = QMenu(self)
        
        fg_color = "white" if self.dark_mode else "black"
        bg_color = "#26242f" if self.dark_mode else "darkGrey"

        context_menu.setStyleSheet(f"background-color: {bg_color}; color: {fg_color};")

        open_location_action = context_menu.addAction("Open File Location")
        
        action = context_menu.exec_(QCursor.pos())
        if action == open_location_action:
            self.open_file_location(app_path)

    def open_file_location(self, app_path):
        target_path = self.get_shortcut_target(app_path)
        if target_path:
            normalized_path = os.path.normpath(target_path)
            subprocess.Popen(f'explorer /select,"{normalized_path}"', shell=True)
        else:
            print(f"Could not find target for shortcut: {app_path}")
    
    def get_shortcut_target(self, shortcut_path):
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)
            target_path = shortcut.TargetPath
            return target_path
        except Exception as e:
            print(f"Error reading shortcut: {e}")
            return None

    def launch(self, app_path):
        subprocess.Popen(app_path, shell=True)
        self.hide()
        self.tray_icon.show()

    def load_settings(self):
        try:
            with open('settings.json', 'r') as file:
                settings = json.load(file)
                self.dark_mode = settings.get('dark_mode', self.default_settings['dark_mode'])
                self.selected_directories = settings.get('selected_directories', self.default_settings['selected_directories'])
                self.current_directory = settings.get('current_directory', self.default_settings['current_directory'])
                self.scroll_style = settings.get('display_style', 'horizontal')
                self.show_online_games = settings.get('show_online_games', False)  # Load show_online_games setting
        except FileNotFoundError:
            self.dark_mode = self.default_settings['dark_mode']
            self.selected_directories = self.default_settings['selected_directories']
            self.current_directory = self.default_settings['current_directory']
            self.scroll_style = 'horizontal'
            self.show_online_games = False
            

    def save_directories(self):
        filename = "directories.json"
        with open(filename, "w") as file:
            json.dump(self.selected_directories, file)

    def get_games_from_directory(self, directory):
        games = []

        if isinstance(directory, str) and os.path.isdir(directory):
            # Scan the main directory
            for entry in os.scandir(directory):
                if entry.is_file() and (entry.name.endswith(".lnk") or entry.name.endswith(".url")):
                    name = os.path.splitext(entry.name)[0]
                    image_path = os.path.join("photos", f"{name}.jpg")
                    games.append((name, entry.path, image_path))

        # Optionally include games from the online games directory
        if self.show_online_games:
            online_games_dir = "C:/Users/jakec/Desktop/CS/.PERSONAL PROJECTS/GAMEGUI/Online Games"
            if os.path.isdir(online_games_dir):
                for entry in os.scandir(online_games_dir):
                    if entry.is_file() and (entry.name.endswith(".lnk") or entry.name.endswith(".url")):
                        name = os.path.splitext(entry.name)[0]
                        image_path = os.path.join("photos", f"{name}.jpg")
                        games.append((name, entry.path, image_path))

        return games


    def create_frame(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            self.grid_layout.removeWidget(widget)
            if widget:
                widget.deleteLater()  # Properly delete the widget
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)


    def get_bg_color(self):
        return "#313e57" if self.dark_mode else "darkGrey"

    def get_fg_color(self):
        return "white" if self.dark_mode else "black"
    
    def filter_games(self, text):
        text = text.lower()  # Convert search text to lowercase for case-insensitive matching
        #print(f"Filtering games with search text: {text}")
        
        # Get the current display style from settings
        current_display_style = self.settings_dialog.display_style
        
        # Keep track of the row and column indices for visible games in grid view
        visible_games = []
        num_cols = 5  # Number of columns in the grid layout
        game_count = 0  # Initialize game count
        
        # Hide all widgets before filtering
        for i in range(self.grid_layout.count()):
            widget_item = self.grid_layout.itemAt(i)
            if widget_item:
                widget = widget_item.widget()
                if widget and hasattr(widget, "layout"):
                    layout = widget.layout()
                    if layout:
                        if layout.count() > 1:
                            name_label = layout.itemAt(1).widget()
                            if name_label and isinstance(name_label, QLabel):
                                if current_display_style == "grid":
                                    widget.hide()
                                else:
                                    widget.setVisible(False)
        
        # Iterate through all game widgets in the grid layout
        for i in range(self.grid_layout.count()):
            widget_item = self.grid_layout.itemAt(i)
            if widget_item:
                widget = widget_item.widget()
                if widget and hasattr(widget, "layout"):
                    layout = widget.layout()
                    if layout:
                        if layout.count() > 1:
                            name_label = layout.itemAt(1).widget()
                            if name_label and isinstance(name_label, QLabel):
                                game_name = name_label.text().lower()
                                if text in game_name:
                                    # Show the widget if the game is matched by the search text
                                    if current_display_style == "grid":
                                        widget.show()
                                        # Calculate the row and column indices for the widget
                                        row = len(visible_games) // num_cols
                                        col = len(visible_games) % num_cols
                                        visible_games.append((widget, row, col))
                                    else:
                                        widget.setVisible(True)
                                    game_count += 1  # Increment game count
                                else:
                                    # Hide the widget if the game is not matched by the search text
                                    if current_display_style == "grid":
                                        widget.hide()
                                    else:
                                        widget.setVisible(False)
        
        # Update game count label
        self.game_count_label.setText(f"Games: {game_count}")
        
        if current_display_style == "grid":
            # Adjust the positions of visible widgets in the grid layout
            for widget, row, col in visible_games:
                self.grid_layout.addWidget(widget, row, col)


class SplashScreen(QSplashScreen):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        self.setPixmap(pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Load and display splash screen
    splash_pix = QPixmap('icon (png).png')
    splash = SplashScreen(splash_pix)
    splash.show()
    
    def launch_game_launcher():
        launcher = GameLauncherApp()
        launcher.show()
    
    # Close splash screen after 10 seconds and launch game launcher
    QTimer.singleShot(5000, splash.close)
    QTimer.singleShot(5000, launch_game_launcher)

    sys.exit(app.exec_())

