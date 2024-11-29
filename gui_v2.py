import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, 
    QListWidget, QPushButton, QFrame, QSystemTrayIcon, QMenu, QSplashScreen, QLineEdit, QDialog, QMenu, QAction
)
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import win32com.client
import datetime
import psutil
import time
import winshell


def load_image(image_path):
    print(f"Loading image from path: {image_path}")
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
        #self.update_styles()

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
        self.load_directories_list()
        self.online_games_toggled.emit(self.show_online_games)



    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.update_styles()
        self.dark_mode_changed.emit(self.dark_mode)

    def update_styles(self):
        bg_color = "#26242f" if self.dark_mode else "darkGrey"
        self.setStyleSheet(f"background-color: {bg_color};")

    def load_directories_list(self):
        self.directory_list_widget.clear()
        filename = "settings2.json"
        if os.path.exists(filename):
            with open(filename, "r") as file:
                settings = json.load(file)
                selected_directories = settings.get("selected_directories", [])
                for directory in selected_directories:
                    self.directory_list_widget.addItem(directory)

                online_games_dir = "./Online Games"
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
        print(f"Saved settings: {settings}")  # Debug statement




class GameLauncherApp(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            print("Initializing GameLauncherApp")
            self.setWindowTitle("Game Launcher")
            self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
            self.dark_mode = False
            self.directories = []  # Initialize directories here
            self.selected_game = None
            self.show_online_games = False
            self.tray_icon = None  # Initialize tray_icon to None
            self.initUI()
            self.update_game_list()  # Updated to call the new method
            self.settings_dialog = SettingsDialog(self)
            self.settings_dialog.dark_mode_changed.connect(self.update_dark_mode_ui)
            self.settings_dialog.online_games_toggled.connect(self.update_online_games)  # Connect online_games_toggled signal
            self.settings_dialog.finished.connect(self.refresh_ui)
            self.settings_dialog.finished.connect(self.update_game_list)  # Connect finished signal to refresh_ui slot
            self.showFullScreen()
            self.setFixedSize(self.screen().size())
            self.tray_icon = self.create_tray_icon()
            self.tray_icon.show()
            print("GameLauncherApp initialized and shown")
        except Exception as e:
            print(f"Error initializing GameLauncherApp: {e}")
            sys.exit(1)
    
    def refresh_ui(self):
        self.update_colors()
        self.update_game_list()

    def update_online_games(self, show_online_games):
        self.show_online_games = show_online_games
        self.update_game_list()

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
        return tray_icon

    def restore_and_refresh(self):
        print("Restoring and refreshing the Game Launcher")
        self.show()  # Show the window
        self.activateWindow()  # Bring the window to the foreground
        self.raise_()  # Ensure the window is not hidden behind others
        self.update_game_list()  # Refresh the game list
        # Optionally, you might want to also update the info view
        if self.selected_game:
            self.update_info_view()

    def filter_games(self, text):
        text = text.lower()  # Convert search text to lowercase for case-insensitive matching
        print(f"Filtering games with search text: '{text}'")

        # Clear the list widget
        self.game_list.clear()
        
        # Filter items based on the search text
        filtered_items = [game_name for game_name in self.original_game_list if text in game_name.lower()]
        
        # Add filtered items back to the list widget
        for item in filtered_items:
            self.game_list.addItem(item)
        
        # Update game count label
        game_count = len(filtered_items)
        self.game_counter_label.setText(f"Games: {game_count}")
        # Styles te game counter label
        self.game_counter_label.setStyleSheet("font-size: 42px; font-weight: bold;")

        # Handle game selection
        if filtered_items:
            # Select the first item in the filtered list
            self.game_list.setCurrentRow(0)
            self.selected_game = filtered_items[0]
            self.update_info_view()
        else:
            # No matches found, keep the last selected game
            if self.original_game_list:
                self.game_list.setCurrentRow(self.original_game_list.index(self.selected_game))
                self.update_info_view()

        print(f"Game list filtered. Number of games: {game_count}")



    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QHBoxLayout(central_widget)

        # Left side: Game list
        self.left_layout = QVBoxLayout()

        # Container for game list
        self.game_list_container = QWidget()
        self.game_list_container.setStyleSheet(
            "background-color: #313e57; border-radius: 10px; padding: 5px;")
        self.game_list_container.setFixedWidth(410)
        self.game_list_layout = QVBoxLayout(self.game_list_container)
        self.game_list_layout.setContentsMargins(10, 10, 10, 10)

        self.game_list = QListWidget()
        self.game_list.setStyleSheet("background-color: transparent; color: #ffffff;")
        self.game_list.setFixedWidth(400)
        self.game_list.currentItemChanged.connect(self.on_game_selected)
        self.game_list_layout.addWidget(self.game_list)

        # Context menu for game list
        self.game_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.game_list.customContextMenuRequested.connect(self.show_game_context_menu)

        # Game counter label
        self.game_counter_label = QLabel("Games: 0")
        self.left_layout.addWidget(self.game_list_container, stretch=1)
        self.left_layout.addWidget(self.game_counter_label, alignment=Qt.AlignBottom)
        self.game_counter_label.setStyleSheet("font-size: 42px; font-weight: bold;")


        self.layout.addLayout(self.left_layout, stretch=1)

        # Right side: Game details
        self.details_frame = QFrame()
        self.details_frame.setStyleSheet("background-color: #313e57; border-radius: 10px; padding: 20px;")
        self.details_frame.setContentsMargins(0, 0, 0, 0)
        self.details_layout = QVBoxLayout(self.details_frame)  # Use vertical layout for right side

        # Create a vertical layout for the cover and a horizontal layout for button and details
        cover_layout = QVBoxLayout()
        button_layout = QVBoxLayout()

        self.game_cover = QLabel()
        self.launch_button = QPushButton("Launch")
        self.launch_button.setFixedWidth(150)

        # Styled Launch Button
        self.launch_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Green background */
                border: none; /* Remove border */
                color: white; /* White text */
                padding: 10px 20px; /* Padding */
                text-align: center; /* Center text */
                font-size: 14px; /* Font size */
                border-radius: 5px; /* Rounded corners */
            }
            QPushButton:hover {
                background-color: #45a049; /* Darker green on hover */
            }
            QPushButton:pressed {
                background-color: #3e8e41; /* Even darker green on click */
            }
        """)

        # Initialize labels
        self.last_played_label = QLabel("Last Played: N/A")
        self.last_played_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        #self.total_played_label = QLabel("Total Time Played: N/A")

        cover_layout.addWidget(self.game_cover)

        # Stack the launch button and labels vertically with no spacing
        button_layout.addWidget(self.launch_button)
        button_layout.addWidget(self.last_played_label)
        #button_layout.addWidget(self.total_played_label)

        # Set spacing to zero
        button_layout.setSpacing(0)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Align button layout with the middle of the cover layout
        cover_layout.addLayout(button_layout)
        cover_layout.setAlignment(Qt.AlignVCenter)

        # Add cover_layout to details_layout
        self.details_layout.addLayout(cover_layout)

        # Create horizontal layout for search bar and settings button
        bottom_layout = QHBoxLayout()
        
        # Add search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search games...")
        self.search_bar.textChanged.connect(self.filter_games)
        bottom_layout.addWidget(self.search_bar)

        # Add settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings)
        bottom_layout.addWidget(self.settings_button)

        # Styled Settings Button
        self.settings_button.setStyleSheet("""
            QPushButton {
                Border: 1px solid #4CAF50; /* Green border */
                border-radius: 5px; /* Rounded corners *
                color: white; /* White text */
                padding: 10px 20px; /* Padding */
                text-align: center; /* Center text */
                font-size: 14px; /* Font size */
                border-radius: 5px; /* Rounded corners */
            }
            QPushButton:hover {
                background-color: #45a049; /* Darker green on hover */
            }
            QPushButton:pressed {
                background-color: #3e8e41; /* Even darker green on click */
            }
        """)

        # Add the horizontal layout to the vertical layout of details_frame
        self.details_layout.addLayout(bottom_layout)

        self.layout.addWidget(self.details_frame, stretch=2)

        print("Initializing UI")
        print("Game list container added to layout with custom styling")
        print("Details frame with game cover and buttons added to layout")
        self.load_settings()  # Load settings on startup
        
        # Ensure to connect the launch button after all setup
        self.launch_button.clicked.connect(self.launch_game)
    
    def show_game_context_menu(self, position):
        context_menu = QMenu(self)
        view_file_action = context_menu.addAction("View File Location")
        action = context_menu.exec_(self.game_list.viewport().mapToGlobal(position))

        if action == view_file_action:
            self.view_file_location()

    def view_file_location(self):
        selected_item = self.game_list.currentItem()
        if selected_item:
            game_name = selected_item.text()
            game_path = self.get_game_path(game_name)
            if game_path:
                # Open the file location in File Explorer
                os.startfile(os.path.dirname(game_path))
            else:
                print(f"File path for {game_name} not found")

    def get_target_from_shortcut(self, shortcut_path):
        try:
            # Resolve the target path of the shortcut
            shell = win32com.client.Dispatch('WScript.Shell')
            shortcut = shell.CreateShortcut(shortcut_path)
            return shortcut.Targetpath
        except Exception as e:
            print(f"Error resolving shortcut: {e}")
            return None

    def get_game_path(self, game_name):
        for directory in self.directories:
            if not os.path.isdir(directory):
                print(f"Directory not found: {directory}")
                continue
            
            possible_shortcut_path = os.path.join(directory, f"{game_name}.lnk")
            if os.path.exists(possible_shortcut_path):
                return self.get_target_from_shortcut(possible_shortcut_path)
            
            possible_shortcut_path = os.path.join(directory, f"{game_name}.url")
            if os.path.exists(possible_shortcut_path):
                return self.get_target_from_shortcut(possible_shortcut_path)


    def update_colors(self):
        bg_color = "#26242f" if self.dark_mode else "darkGrey"
        self.setStyleSheet(f"background-color: {bg_color};")
        color = "white" if self.dark_mode else "black"
        self.game_counter_label.setStyleSheet(f"color: {color}; font-size: 42px; font-weight: bold;")
        self.update_info_view()


    def open_settings(self):
        self.settings_dialog.exec_()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F12 or event.key() == Qt.Key_Escape:
            print("Closing application")
            self.close()

    def update_info_view(self):
        print(f"Updating info view for selected game: {self.selected_game}")
        if not self.selected_game:
            print("No game selected")
            return

        # Example path: assuming each game's cover image is named after the game
        game_cover_filename = f"{self.selected_game}.jpg"
        game_cover_path = os.path.join("./photos", game_cover_filename)
        print(f"Constructed cover image path: {game_cover_path}")

        if os.path.exists(game_cover_path):
            try:
                # Load and resize the image
                image = QImage(game_cover_path)
                if image.isNull():
                    print(f"Image loading failed: {game_cover_path}")
                    # Optionally, set a placeholder image
                    self.game_cover.setPixmap(QPixmap())  # Empty pixmap or a placeholder image
                    return

                # Resize image
                resized_image = image.scaled(500, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Example size: 500x800
                self.game_cover.setPixmap(QPixmap.fromImage(resized_image))
                print("Game cover image loaded and resized successfully")
            except FileNotFoundError as e:
                print(f"Error loading image: {e}")
                # Optionally, set a placeholder image
                self.game_cover.setPixmap(QPixmap())  # Empty pixmap or a placeholder image
        else:
            print(f"Cover image not found: {game_cover_path}")
            # Optionally, set a placeholder image
            self.game_cover.setPixmap(QPixmap())  # Empty pixmap or a placeholder image

        # Update button text
        self.launch_button.setText(f"Launch Game")

        # Read game_tracker.json for additional information
        tracker_file = "game_tracker.json"
        last_played = "N/A"
        total_played = "N/A"

        if os.path.exists(tracker_file):
            with open(tracker_file, "r") as file:
                data = json.load(file)
                game_data = data.get(self.selected_game, {})
                last_played = game_data.get("last_played", "N/A")
                total_played = game_data.get("total_played", "N/A")

        self.last_played_label.setText(f"Last Played: {last_played}")
        #self.total_played_label.setText(f"Total Time Played: {total_played}")
        print("Info view updated")

    def create_or_update_tracker(self):
        game_tracker_path = "game_tracker.json"
        if not os.path.exists(game_tracker_path):
            print(f"Creating game tracker file: {game_tracker_path}")
            games = [self.game_list.item(i).text() for i in range(self.game_list.count())]
            tracker_data = {game: {"last_played": "N/A", "total_played": "N/A"} for game in games}
            with open(game_tracker_path, "w") as file:
                json.dump(tracker_data, file, indent=4)
            print("Game tracker file created and initialized")
        else:
            print(f"Game tracker file already exists: {game_tracker_path}")

    def on_game_selected(self):
        selected_item = self.game_list.currentItem()
        if selected_item:
            self.selected_game = selected_item.text()
            self.update_info_view()
        else:
            print("No game selected")
        
    def update_game_tracker(self, start_time=False):
        tracker_file = "game_tracker.json"
        now = datetime.datetime.now()
        now_str = now.strftime("%Y-%m-%d %I:%M %p")  # Formatted time string

        data = {}

        if os.path.exists(tracker_file):
            with open(tracker_file, "r") as file:
                data = json.load(file)
        
        game_data = data.get(self.selected_game, {"last_played": "N/A", "total_played": "0", "start_time": "N/A"})

        if start_time:
            # Record start time
            game_data["start_time"] = now_str
        else:
            # Calculate and update total playtime
            start_time_str = game_data.get("start_time")
            if start_time_str and start_time_str != "N/A":
                try:
                    start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %I:%M %p")
                    play_duration = now - start_time
                    total_played = game_data.get("total_played", "0")
                    
                    # Convert total_played from "HH:MM:SS" to timedelta
                    total_played_td = datetime.timedelta(hours=int(total_played.split(':')[0]), 
                                                        minutes=int(total_played.split(':')[1]), 
                                                        seconds=int(total_played.split(':')[2]))
                    
                    new_total_played = total_played_td + play_duration
                    new_total_played_str = str(new_total_played).split()[2]  # "days, HH:MM:SS" -> "HH:MM:SS"
                    
                    game_data["total_played"] = new_total_played_str
                except ValueError as e:
                    print(f"Error parsing total_played or start_time: {e}")

                game_data["start_time"] = "N/A"  # Clear start time

        game_data["last_played"] = now_str
        data[self.selected_game] = game_data
        
        with open(tracker_file, "w") as file:
            json.dump(data, file, indent=4)
        
        print(f"Game tracker updated: {self.selected_game} -> {game_data}")

    def getLocation(shortcut_path):
        if not os.path.exists(shortcut_path):
            print(f"Error: {shortcut_path} does not exist.")
            return None
        
        shortcut = winshell.shortcut(shortcut_path)
        return shortcut.path

    @staticmethod
    def is_process_running(process_name):
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                return True
        return False

    def launch_game(self):
        if not self.selected_game:
            print("No game selected to launch")
            return

        shortcut_path = None
        for directory in self.directories:
            if not os.path.isdir(directory):
                print(f"Directory not found: {directory}")
                continue
            
            possible_shortcut_path = os.path.join(directory, f"{self.selected_game}.lnk")
            if os.path.exists(possible_shortcut_path):
                shortcut_path = possible_shortcut_path
                break
            
            possible_shortcut_path = os.path.join(directory, f"{self.selected_game}.url")
            if os.path.exists(possible_shortcut_path):
                shortcut_path = possible_shortcut_path
                break
        
        if shortcut_path:
            print(f"Launching game: {self.selected_game} from {shortcut_path}")
            try:
                target_path = self.get_target_from_shortcut(shortcut_path)
                if target_path and os.path.exists(target_path):
                    self.update_game_tracker(start_time=True)
                    
                    os.startfile(target_path)
                    self.hide()
                    self.tray_icon.show()
                    
                    process_name = os.path.basename(target_path)
                    print(f"Monitoring process: {process_name}")
                    if self.monitor_game_execution(process_name):
                        self.update_game_tracker(start_time=False)
                else:
                    print(f"Target path for game '{self.selected_game}' not found: {target_path}")
            except Exception as e:
                print(f"Error launching game: {e}")
        else:
            print(f"Shortcut for game '{self.selected_game}' not found")

    def monitor_game_execution(self, process_name):
        print(f"Monitoring process: {process_name}")

        try:
            while GameLauncherApp.is_process_running(process_name):
                time.sleep(5)
            
            print(f"{process_name} has stopped running")
            return True
        except Exception as e:
            print(f"Error while monitoring process: {e}")
            return False

    def update_game_list(self):
        print("Updating game list")
        self.game_list.clear()

        games = []

        # Load the games from selected directories
        for directory in self.directories:
            if not os.path.isdir(directory):
                print(f"Directory not found: {directory}")
                continue  # Skip non-existent directories

            for file_name in os.listdir(directory):
                if file_name.endswith(".lnk") or file_name.endswith(".url"):
                    game_name = os.path.splitext(file_name)[0]
                    games.append(game_name)

        
        # Handle online games
        online_games_dir = "./Online Games"
        if self.show_online_games:
            if os.path.isdir(online_games_dir):
                for file_name in os.listdir(online_games_dir):
                    if file_name.endswith(".lnk") or file_name.endswith(".url"):
                        game_name = os.path.splitext(file_name)[0]
                        if game_name not in games:
                            games.append(game_name)
        else:
            # Remove online games directory from directories if not showing online games
            if online_games_dir in self.directories:
                self.directories.remove(online_games_dir)
        
        # Sort the game list alphabetically
        games.sort()
        
        # Save the original game list for filtering
        self.original_game_list = games.copy()
        
        # Add sorted games to the list widget
        for game_name in games:
            self.game_list.addItem(game_name)
        
        game_count = len(games)
        self.game_counter_label.setText(f"Games: {game_count}")
        print(f"Game list updated with {game_count} games")



    def load_settings(self):
        print("Loading settings")
        filename = "settings2.json"
        if os.path.exists(filename):
            with open(filename, "r") as file:
                settings = json.load(file)
                self.dark_mode = settings.get("dark_mode", False)
                self.directories = settings.get("selected_directories", [])
                # Implement settings logic if needed
            print("Settings loaded:", settings)
        else:
            print(f"Settings file not found: {filename}")
            self.directories = []

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
    QTimer.singleShot(3500, splash.close)
    QTimer.singleShot(3500, launch_game_launcher)

    sys.exit(app.exec_())
