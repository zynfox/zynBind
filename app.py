import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QLineEdit, QWidget, QHBoxLayout, QCheckBox
from PySide6.QtCore import Qt
import keyboard
from pynput import mouse
import datetime

# Define the current version of your application
__version__ = "0.2-beta"

class DateKeyBinder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("zynBind - Mouse/Keyboard Key Binder")
        self.setGeometry(100, 100, 300, 350)

        self.layout = QVBoxLayout()

        # Create a horizontal layout for the switch and label
        self.switch_layout = QHBoxLayout()

        # Enable Keybind Listening Switch
        self.toggle_listening_checkbox = QCheckBox("Enable Keybind Listening", self)
        self.toggle_listening_checkbox.setChecked(True)
        self.switch_layout.addWidget(self.toggle_listening_checkbox)

        self.layout.addLayout(self.switch_layout)

        self.instructions = QLabel("Press 'Add Keybind' and then your desired key or mouse button.")
        self.layout.addWidget(self.instructions)

        self.keybind_input = QLineEdit(self)
        self.keybind_input.setPlaceholderText("Enter keybind here...")
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
            "3. You can include {SPACE} in your keybind for inserting spaces before or after the date.\n"
            "   For example, if your keybind is 'F1{SPACE}', the date will paste with a space afterward.",
            self
        )
        self.layout.addWidget(self.instructions_label)

        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        self.current_keybind = None
        self.mouse_listener = None
        self.first_instance = True

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
                self.keybind_input.setText(key)
                self.status_label.setText(f"Status: Keybind set to {key}")
                self.keybind_set = True
                keyboard.unhook_all()
                if self.mouse_listener:
                    self.mouse_listener.stop()

        def on_click(x, y, button, pressed):
            if pressed and not self.keybind_set:
                self.current_keybind = str(button)
                self.keybind_input.setText(str(button))
                self.status_label.setText(f"Status: Keybind set to {button}")
                self.keybind_set = True
                if self.mouse_listener:
                    self.mouse_listener.stop()

        keyboard.hook(on_key_event)

        self.mouse_listener = mouse.Listener(on_click=on_click)
        self.mouse_listener.start()

    def start_listening(self):
        def on_triggered(e):
            if self.toggle_listening_checkbox.isChecked():
                if e.name == self.current_keybind:
                    if self.first_instance:
                        self.first_instance = False  # Ignore first instance for pasting date
                    else:
                        self.paste_date()
                    return True  # Block other handlers from processing

        def on_mouse_click(x, y, button, pressed):
            if self.toggle_listening_checkbox.isChecked() and pressed and str(button) == self.current_keybind:
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
