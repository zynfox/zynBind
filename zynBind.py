import os
import urllib.request
import zipfile
import json
import subprocess
import sys
import re
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QLineEdit, QWidget, QHBoxLayout, QCheckBox
from PySide6.QtCore import Qt
import keyboard
from pynput import mouse

class DateKeyBinder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("zynBind - Mouse/Keyboard Key Binder")
        self.setGeometry(100, 100, 300, 400)
        self.layout = QVBoxLayout()

        self.switch_layout = QHBoxLayout()
        self.toggle_listening_checkbox = QCheckBox("Enable Keybind Listening", self)
        self.toggle_listening_checkbox.setChecked(True)
        self.switch_layout.addWidget(self.toggle_listening_checkbox)

        self.add_space_checkbox = QCheckBox("Add Space After Date", self)
        self.add_space_checkbox.setChecked(False)
        self.add_space_checkbox.stateChanged.connect(self.update_keybind_with_space)
        self.switch_layout.addWidget(self.add_space_checkbox)

        self.layout.addLayout(self.switch_layout)

        self.instructions = QLabel("Press 'Add Keybind' and then your desired key or mouse button.")
        self.layout.addWidget(self.instructions)

        self.keybind_input = QLineEdit(self)
        self.keybind_input.setPlaceholderText("Enter keybind here...")
        self.keybind_input.textChanged.connect(self.auto_save_keybind)
        self.layout.addWidget(self.keybind_input)

        self.add_keybind_button = QPushButton("Add Keybind", self)
        self.add_keybind_button.clicked.connect(self.add_keybind)
        self.layout.addWidget(self.add_keybind_button)

        self.status_label = QLabel("Status: Waiting for keybind...")
        self.layout.addWidget(self.status_label)

        self.instructions_label = QLabel(
            "\nInstructions:\n"
            "1. Press 'Add Keybind' and then your desired key or mouse button.\n"
            "2. Use the switch at the top to enable or disable keybind listening.\n"
            "3. Check 'Add Space After Date' to automatically append a space after the date.",
            self
        )
        self.layout.addWidget(self.instructions_label)

        self.run_button = QPushButton("Run", self)
        self.run_button.clicked.connect(self.save_and_run)
        self.layout.addWidget(self.run_button)

        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.close_app)
        self.layout.addWidget(self.close_button)

        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        self.current_keybind = None
        self.mouse_listener = None
        self.first_instance = True
        self.autohotkey_process = None

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.paths_file = os.path.join(self.script_dir, 'autohotkey_paths.json')

        # Load previous keybind on startup
        self.load_keybind()

        # Ensure AutoHotkey is set up
        self.ensure_autohotkey_setup()

    def ensure_autohotkey_setup(self):
        if not os.path.exists(self.paths_file):
            self.download_and_setup_autohotkey()

    def download_and_setup_autohotkey(self):
        url = "https://www.autohotkey.com/download/2.0/AutoHotkey_2.0.18.zip"
        zip_filename = "AutoHotkey_2.0.18.zip"
        zip_path = os.path.join(self.script_dir, zip_filename)
        extract_dir_name = os.path.splitext(zip_filename)[0]
        extract_path = os.path.join(self.script_dir, extract_dir_name)

        print("Downloading AutoHotkey...")
        urllib.request.urlretrieve(url, zip_path)
        print("Download complete.")

        print(f"Unzipping AutoHotkey to {extract_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        print("Unzip complete.")

        print(f"Deleting ZIP file {zip_path}...")
        os.remove(zip_path)
        print("ZIP file deleted.")

        executable_path = self.find_executable_path(extract_path)
        if executable_path:
            self.save_paths(extract_path, executable_path)
        else:
            print("AutoHotkey executable not found. Please install it manually.")

    def find_executable_path(self, extract_path):
        print(f"Looking for executable in {extract_path}")
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                if file.lower() == 'autohotkey64.exe':
                    return os.path.join(root, file)
        return None

    def save_paths(self, extract_path, executable_path):
        paths = {
            'extract_path': extract_path,
            'executable_path': executable_path
        }
        with open(self.paths_file, 'w') as file:
            json.dump(paths, file)
        print(f"Paths saved to {self.paths_file}")

    def load_keybind(self):
        json_path = os.path.join(self.script_dir, 'keybind_settings.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as json_file:
                settings = json.load(json_file)
                self.current_keybind = settings.get('keybind', '')
                if self.current_keybind:
                    self.keybind_input.setText(self.current_keybind)
                    self.status_label.setText(f"Status: Keybind set to {self.current_keybind}")
                    if "{SPACE}" in self.current_keybind:
                        self.add_space_checkbox.setChecked(True)
                else:
                    self.status_label.setText("Status: No keybind set")

    def add_keybind(self):
        self.status_label.setText("Status: Press a key or mouse button...")
        self.keybind_input.clear()
        self.keybind_input.setFocus()
        self.keybind_set = False
        self.first_instance = True

        def on_key_event(e):
            if not self.keybind_set:
                key = e.name
                self.current_keybind = key
                if self.add_space_checkbox.isChecked():
                    self.current_keybind += "{SPACE}"
                self.keybind_input.setText(self.current_keybind)
                self.status_label.setText(f"Status: Keybind set to {self.current_keybind}")
                self.keybind_set = True
                keyboard.unhook_all()
                if self.mouse_listener:
                    self.mouse_listener.stop()
                self.create_ahk_file()

        def on_click(x, y, button, pressed):
            if pressed and not self.keybind_set:
                self.current_keybind = str(button)
                if self.add_space_checkbox.isChecked():
                    self.current_keybind += "{SPACE}"
                self.keybind_input.setText(self.current_keybind)
                self.status_label.setText(f"Status: Keybind set to {self.current_keybind}")
                self.keybind_set = True
                if self.mouse_listener:
                    self.mouse_listener.stop()
                self.create_ahk_file()

        keyboard.hook(on_key_event)
        self.mouse_listener = mouse.Listener(on_click=on_click)
        self.mouse_listener.start()

    def save_keybind(self, keybind):
        settings = {'keybind': keybind}
        json_path = os.path.join(self.script_dir, 'keybind_settings.json')
        with open(json_path, 'w') as json_file:
            json.dump(settings, json_file)

    def auto_save_keybind(self):
        keybind = self.keybind_input.text()
        if keybind:
            self.save_keybind(keybind)

    def update_keybind_with_space(self):
        keybind = self.keybind_input.text()
        if self.add_space_checkbox.isChecked():
            if "{SPACE}" not in keybind:
                keybind += "{SPACE}"
        else:
            keybind = keybind.replace("{SPACE}", "")
        self.keybind_input.setText(keybind)
        self.save_keybind(keybind)

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

        autohotkey_dir = self.script_dir
        if os.path.exists(self.paths_file):
            with open(self.paths_file, 'r') as json_file:
                paths = json.load(json_file)
                executable_path = paths.get('executable_path')
                if executable_path:
                    autohotkey_dir = os.path.dirname(executable_path)

        script_content = f"""
        {keybind_clean}::
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

        ahk_file_path = os.path.join(autohotkey_dir, 'paste_date.ahk')
        with open(ahk_file_path, 'w') as file:
            file.write(script_content)
        print(f"AHK script created at {ahk_file_path}")
        self.run_autohotkey_script(ahk_file_path)

    def run_autohotkey_script(self, ahk_file_path):
        if os.path.exists(self.paths_file):
            with open(self.paths_file, 'r') as json_file:
                paths = json.load(json_file)
                executable_path = paths.get('executable_path')
                if executable_path:
                    if self.autohotkey_process:
                        self.autohotkey_process.terminate()
                    self.autohotkey_process = subprocess.Popen([executable_path, ahk_file_path])

    def save_and_run(self):
        keybind = self.keybind_input.text()
        self.save_keybind(keybind)
        self.create_ahk_file()

    def close_app(self):
        # Terminate AutoHotkey process if running
        if self.autohotkey_process and self.autohotkey_process.poll() is None:
            self.autohotkey_process.terminate()  # Try to terminate gracefully
            self.autohotkey_process.wait()  # Wait for process to terminate
        self.close()  # Close the application window

    def closeEvent(self, event):
        """Override the closeEvent to ensure AutoHotkey is terminated."""
        self.close_app()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DateKeyBinder()
    window.show()
    sys.exit(app.exec())
