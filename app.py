import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QLineEdit, QWidget, QHBoxLayout, QCheckBox
from PySide6.QtCore import Qt
import json
import os
import keyboard
from pynput import mouse
import datetime

# Define the current version of your application
__version__ = "0.4-beta"

class DateKeyBinder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("zynBind - Mouse/Keyboard Key Binder")
        self.setGeometry(100, 100, 300, 400)

        self.layout = QVBoxLayout()

        # Create a horizontal layout for the switches and labels
        self.switch_layout = QHBoxLayout()

        # Enable Keybind Listening Switch
        self.toggle_listening_checkbox = QCheckBox("Enable Keybind Listening", self)
        self.toggle_listening_checkbox.setChecked(True)
        self.switch_layout.addWidget(self.toggle_listening_checkbox)

        # Add Space After Date Switch
        self.add_space_checkbox = QCheckBox("Add Space After Date", self)
        self.add_space_checkbox.setChecked(False)
        self.add_space_checkbox.stateChanged.connect(self.update_keybind_with_space)
        self.switch_layout.addWidget(self.add_space_checkbox)

        self.layout.addLayout(self.switch_layout)

        self.instructions = QLabel("Press 'Add Keybind' and then your desired key or mouse button.")
        self.layout.addWidget(self.instructions)

        self.keybind_input = QLineEdit(self)
        self.keybind_input.setPlaceholderText("Enter keybind here...")
        self.keybind_input.textChanged.connect(self.auto_save_keybind)  # Connect textChanged signal
        self.layout.addWidget(self.keybind_input)

        self.add_keybind_button = QPushButton("Add Keybind", self)
        self.add_keybind_button.clicked.connect(self.add_keybind)
        self.layout.addWidget(self.add_keybind_button)

        self.status_label = QLabel("Status: Waiting for keybind...")
        self.layout.addWidget(self.status_label)

        # Instructions for usage
        self.instructions_label = QLabel(
            "\nInstructions:\n"
            "1. Press 'Add Keybind' and then your desired key or mouse button.\n"
            "2. Use the switch at the top to enable or disable keybind listening.\n"
            "3. Check 'Add Space After Date' to automatically append a space after the date.",
            self
        )
        self.layout.addWidget(self.instructions_label)

        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        self.current_keybind = None
        self.mouse_listener = None
        self.first_instance = True

        # Determine the directory of the script
        if getattr(sys, 'frozen', False):
            self.script_dir = os.path.dirname(sys.executable)
        else:
            self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # Load previous keybind on startup
        self.load_keybind()

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
        self.first_instance = True  # Reset the flag when setting a new keybind

        def on_key_event(e):
            if not self.keybind_set:
                key = e.name
                self.current_keybind = key
                if self.add_space_checkbox.isChecked():
                    self.current_keybind += "{SPACE}"
                self.keybind_input.setText(self.current_keybind)
                self.status_label.setText(f"Status: Keybind set to {self.current_keybind}")
                self.keybind_set = True
                self.save_keybind(self.current_keybind)
                keyboard.unhook_all()
                if self.mouse_listener:
                    self.mouse_listener.stop()

        def on_click(x, y, button, pressed):
            if pressed and not self.keybind_set:
                self.current_keybind = str(button)
                if self.add_space_checkbox.isChecked():
                    self.current_keybind += "{SPACE}"
                self.keybind_input.setText(self.current_keybind)
                self.status_label.setText(f"Status: Keybind set to {self.current_keybind}")
                self.keybind_set = True
                self.save_keybind(self.current_keybind)
                if self.mouse_listener:
                    self.mouse_listener.stop()

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
        if keybind:  # Only save if there is a keybind
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

    def start_listening(self):
        def on_triggered(e):
            if self.toggle_listening_checkbox.isChecked():
                if e.name == self.current_keybind.split('{')[0]:  # Check only the key part
                    if self.first_instance:
                        self.first_instance = False  # Ignore first instance for pasting date
                    else:
                        self.paste_date()
                    return True  # Block other handlers from processing

        def on_mouse_click(x, y, button, pressed):
            if self.toggle_listening_checkbox.isChecked() and pressed and str(button) == self.current_keybind.split('{')[0]:  # Check only the button part
                if self.first_instance:
                    self.first_instance = False  # Ignore first instance for pasting date
                else:
                    self.paste_date()
                return True  # Block other handlers from processing

        keyboard.on_press(on_triggered)
        mouse_listener = mouse.Listener(on_click=on_mouse_click)
        mouse_listener.start()

    def paste_date(self):
        current_date = datetime.datetime.now().strftime("%m/%d/%Y")
        keybind_text = self.keybind_input.text()

        # Determine if {SPACE} should be added before or after
        if "{SPACE}" in keybind_text:
            if keybind_text.startswith("{SPACE}"):
                text_to_paste = " " + current_date
            elif keybind_text.endswith("{SPACE}"):
                text_to_paste = current_date + " "
            else:
                text_to_paste = current_date  # Default case
        else:
            text_to_paste = current_date

        keyboard.write(text_to_paste)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DateKeyBinder()
    window.show()
    window.start_listening()
    sys.exit(app.exec())