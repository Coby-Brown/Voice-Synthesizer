#!/usr/bin/env python3
"""Simple launcher GUI for queue clearing."""

from pathlib import Path
import subprocess
import sys

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Voice Synthesizer")
        self.setFixedSize(320, 140)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        button = QPushButton("Run clear.py")
        button.setFixedSize(200, 50)
        button.clicked.connect(self.run_clear_script)
        
        layout.addWidget(button)
        self.setLayout(layout)
    
    def run_clear_script(self):
        """Run scripts/clear.py after GUI confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "This will delete files in queue/. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        script_path = Path(__file__).resolve().parent / "scripts" / "clear.py"
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                input="yes\n",
                text=True,
                capture_output=True,
                check=False,
            )
            
            output = (result.stdout or "").strip()
            errors = (result.stderr or "").strip()
            
            if result.returncode == 0:
                QMessageBox.information(self, "clear.py finished", output or "Queue clear completed.")
            else:
                QMessageBox.critical(
                    self,
                    "clear.py failed",
                    f"Exit code: {result.returncode}\n\n{errors or output or 'No output.'}"
                )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to run clear.py:\n{exc}")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()