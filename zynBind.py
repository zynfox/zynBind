import os
import json
import subprocess
import sys
import re
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QLineEdit, QWidget, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt
import keyboard
from pynput import mouse, keyboard as pynput_keyboard
from pynput.mouse import Button
from PySide6.QtGui import QPixmap

__copyright__ = u'Copyright (C) 2024 zynfox.com'
__license__ = 'Proprietary'

class DateKeyBinder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("zynBind - Mouse/Keyboard Key Binder")
        self.setMinimumSize(300, 400)

        # Main container layout
        main_container = QVBoxLayout()
        main_container.setContentsMargins(20, 0, 20, 0)  # Add padding on left and right

        main_layout = QVBoxLayout()
        top_layout = QGridLayout()
        top_layout.setColumnStretch(0, 1)
        top_layout.setColumnStretch(1, 2)
        top_layout.setColumnStretch(2, 1)

        self.logo_label = QLabel()
        self.original_logo_pixmap = QPixmap("C:\\Users\\zork\\Projects\\Github\\zynfox\\zynBind\\img\\zynBind-logo.png")
        self.logo_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        top_layout.addWidget(self.logo_label, 0, 0)

        copyright_label = QLabel(f"{__copyright__}\nLicense: {__license__}")
        copyright_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        copyright_label.setStyleSheet("color: gray; font-size: 10px;")
        top_layout.addWidget(copyright_label, 0, 2)

        main_layout.addLayout(top_layout)

        self.layout = QVBoxLayout()
        self.layout.addStretch()

        self.switch_layout = QHBoxLayout()
        self.toggle_button = QPushButton("OFF", self)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2c39;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:checked {
                background-color: #721cbd;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_switch)
        self.switch_layout.addWidget(self.toggle_button)

        toggle_label = QLabel("Add Space After Date")
        self.switch_layout.addWidget(toggle_label)

        self.layout.addLayout(self.switch_layout)

        self.instructions = QLabel("Press 'Add Keybind' and then your desired key or mouse button.")
        self.layout.addWidget(self.instructions)

        self.keybind_input = QLineEdit(self)
        self.keybind_input.setPlaceholderText("Enter keybind here...")
        self.keybind_input.textChanged.connect(self.auto_save_keybind)
        self.keybind_input.setAlignment(Qt.AlignCenter)  # Center the keybind input
        self.layout.addWidget(self.keybind_input)

        self.status_label = QLabel("Status: Waiting for keybind...")
        self.layout.addWidget(self.status_label, alignment=Qt.AlignCenter)  # Center the status label

        self.add_keybind_button = QPushButton("Add Keybind", self)
        self.add_keybind_button.clicked.connect(self.add_keybind)
        self.layout.addWidget(self.add_keybind_button, alignment=Qt.AlignCenter)  # Center the button

        self.instructions_label = QLabel(
            "\nInstructions:\n"
            "1. Press 'Add Keybind' and then your desired key or mouse button.\n"
            "2. Toggle 'Add Space After Date' to automatically append a space after the date."
        )
        self.layout.addWidget(self.instructions_label)

        # Button layout for Run and Close
        button_layout = QHBoxLayout()
        self.run_button = QPushButton("Run", self)
        self.run_button.clicked.connect(self.save_and_run)
        button_layout.addWidget(self.run_button)

        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.close_app)
        button_layout.addWidget(self.close_button)

        self.layout.addLayout(button_layout)  # Add button layout to main layout

        self.layout.addStretch()
        main_layout.addLayout(self.layout)

        main_container.addLayout(main_layout)

        self.container = QWidget()
        self.container.setLayout(main_container)
        self.setCentralWidget(self.container)

        self.current_keybind = None
        self.mouse_listener = None
        self.first_instance = True
        self.autohotkey_process = None
        self.ahk_script_running = False

        self.load_settings()
        self.ensure_autohotkey_setup()

        for button in self.findChildren(QPushButton):
            button.setFixedWidth(150)  # Reduce button width
            button.clicked.connect(self.check_space_checkbox)

        self.scale_logo()
        self.resizeEvent = self.on_resize

    def toggle_switch(self):
        if self.toggle_button.isChecked():
            self.toggle_button.setText("ON")
        else:
            self.toggle_button.setText("OFF")
        self.update_keybind_with_space()
        self.save_settings()

    def scale_logo(self, event=None):
        available_width = self.width() * 0.5
        available_height = self.height() * 0.3
        size = min(available_width, available_height)
        
        scaled_pixmap = self.original_logo_pixmap.scaled(
            size, size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.logo_label.setPixmap(scaled_pixmap)

    def on_resize(self, event):
        self.scale_logo(event)
        font_size = max(10, self.width() // 50)
        self.setStyleSheet(f"font-size: {font_size}px;")
        for button in self.findChildren(QPushButton):
            button.setFixedWidth(max(150, self.width() // 4))
        self.toggle_button.setFixedWidth(max(50, self.width() // 10))  # Adjust width for the toggle button
        super().resizeEvent(event)

    def get_app_dir(self):
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def check_space_checkbox(self):
        if self.toggle_button.isChecked():
            current_keybind = self.keybind_input.text()
            if "{SPACE}" not in current_keybind:
                self.keybind_input.setText(current_keybind + "{SPACE}")

    def ensure_autohotkey_setup(self):
        self.paths_file = os.path.join(self.get_app_dir(), 'autohotkey_paths.json')
        ahk_folder = os.path.join(self.get_app_dir(), 'AutoHotkey_2.0.18')
        executable_path = os.path.join(ahk_folder, 'AutoHotkey64.exe')

        if not os.path.exists(executable_path):
            print("AutoHotkey executable not found. Please ensure the AutoHotkey_2.0.18 folder is in the same directory as the script.")
            sys.exit(1)

        self.save_paths(ahk_folder, executable_path)

    def save_paths(self, extract_path, executable_path):
        paths = {
            'extract_path': extract_path,
            'executable_path': executable_path
        }
        with open(self.paths_file, 'w') as file:
            json.dump(paths, file)
        print(f"Paths saved to {self.paths_file}")

    def load_settings(self):
        settings_path = os.path.join(self.get_app_dir(), 'settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            keybind = settings.get('keybind', '')
            self.keybind_input.setText(keybind)
            add_space = settings.get('add_space', False)
            self.toggle_button.setChecked(add_space)
            self.toggle_button.setText("ON" if add_space else "OFF")
            self.update_keybind_with_space()
            if keybind:
                self.status_label.setText(f"Status: Keybind set to {keybind}")

    def add_keybind(self):
        self.status_label.setText("Status: Press a key or mouse button...")
        self.keybind_input.clear()
        self.keybind_input.setFocus()
        self.keybind_set = False
        self.current_keybind = ""
        self.pressed_keys = set()

        def on_key_event(e):
            if not self.keybind_set:
                if e.event_type == keyboard.KEY_DOWN and e.name not in self.pressed_keys:
                    if e.name in {'ctrl', 'alt', 'shift', 'win'}:
                        self.current_keybind += e.name.upper() + "+"
                        self.pressed_keys.add(e.name)
                    else:
                        self.current_keybind += e.name.upper()
                        self.keybind_input.setText(self.current_keybind)
                        self.status_label.setText(f"Status: Keybind set to {self.current_keybind}")
                        self.keybind_set = True
                        keyboard.unhook_all()
                        if self.mouse_listener:
                            self.mouse_listener.stop()
                        self.check_space_checkbox()
                        self.create_ahk_file()

        keyboard.hook(on_key_event)
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()

    def on_click(self, x, y, button, pressed):
        if pressed and not self.keybind_set:
            if button == Button.left:
                self.current_keybind = "LButton"
            elif button == Button.right:
                self.current_keybind = "RButton"
            elif button == Button.middle:
                self.current_keybind = "MButton"
            elif button == Button.x1:
                self.current_keybind = "XButton1"
            elif button == Button.x2:
                self.current_keybind = "XButton2"
            else:
                self.current_keybind = str(button)
            self.keybind_input.setText(self.current_keybind)
            self.status_label.setText(f"Status: Keybind set to {self.current_keybind}")
            self.keybind_set = True
            if self.mouse_listener:
                self.mouse_listener.stop()
            self.check_space_checkbox()
            self.create_ahk_file()

    def get_modifier_key(self, key_name):
        modifier_keys = {
            'CTRL': '^',
            'ALT': '!',
            'SHIFT': '+',
            'WIN': '#'
        }
        return modifier_keys.get(key_name, '')

    def save_settings(self):
        settings = {
            'keybind': self.keybind_input.text(),
            'add_space': self.toggle_button.isChecked()
        }
        settings_path = os.path.join(self.get_app_dir(), 'settings.json')
        with open(settings_path, 'w') as f:
            json.dump(settings, f)

    def auto_save_keybind(self):
        keybind = self.keybind_input.text()
        if keybind:
            self.save_settings()

    def update_keybind_with_space(self):
        keybind = self.keybind_input.text()
        if self.toggle_button.isChecked():
            if "{SPACE}" not in keybind:
                keybind += "{SPACE}"
        else:
            keybind = keybind.replace("{SPACE}", "")
        self.keybind_input.setText(keybind)
        self.save_settings()

    def create_ahk_file(self):
        keybind = self.keybind_input.text()
        keybind_clean = re.sub(r'Button\.x(\d+)', r'XButton\1', keybind)
        space_before = ""
        space_after = ""
        if "{SPACE}" in keybind_clean:
            if keybind_clean.startswith("{SPACE}"):
                keybind_clean = keybind_clean.replace("{SPACE}", "")
                space_before = " "
            else:
                keybind_clean = keybind_clean.replace("{SPACE}", "")
                space_after = " "

        ahk_keybind = ''
        for part in keybind_clean.split('+'):
            if part in {'CTRL', 'ALT', 'SHIFT', 'WIN'}:
                ahk_keybind += self.get_modifier_key(part)
            else:
                ahk_keybind += part

        script_content = f"""
{ahk_keybind}::
{{
    ; Use FormatTime to get the current date in MM/dd/yyyy format
    currentDate := FormatTime(A_Now, "MM/dd/yyyy")
    ; Add a space after the formatted date
    formattedDateWithSpace := currentDate "{space_after}"
    ; Send formatted input
    SendInput(formattedDateWithSpace)
    return
}}
"""

        json_path = os.path.join(self.get_app_dir(), 'autohotkey_paths.json')
        with open(json_path, 'r') as json_file:
            paths = json.load(json_file)
        ahk_file_path = os.path.join(paths['extract_path'], 'keybind.ahk')
        with open(ahk_file_path, 'w') as ahk_file:
            ahk_file.write(script_content)
        print(f"AHK file created: {ahk_file_path}")
        self.run_ahk_script(ahk_file_path)

    def run_ahk_script(self, ahk_file_path):
        json_path = os.path.join(self.get_app_dir(), 'autohotkey_paths.json')
        with open(json_path, 'r') as json_file:
            paths = json.load(json_file)
        autohotkey_executable = paths['executable_path']
        if self.autohotkey_process:
            self.autohotkey_process.terminate()
        print(f"Running AHK script: {ahk_file_path}")
        self.autohotkey_process = subprocess.Popen([autohotkey_executable, ahk_file_path])
        self.ahk_script_running = True
        print("AHK script running...")

    def save_and_run(self):
        keybind = self.keybind_input.text()
        if keybind:
            self.save_settings()
            self.create_ahk_file()
            self.status_label.setText(f"Status: Keybind '{keybind}' saved and script running.")
        else:
            self.status_label.setText("Status: No keybind to save.")

    def close_app(self):
        self.save_settings()
        if self.autohotkey_process:
            self.autohotkey_process.terminate()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = DateKeyBinder()
    main_window.show()
    sys.exit(app.exec())