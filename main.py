#!/usr/bin/env python3
"""Simple launcher GUI for queue clearing and synthesis."""

from pathlib import Path
import subprocess
import sys

from PyQt5.QtCore import QProcess, Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.synth_process = None
        self.convert_process = None
        self.pending_output_path = None
        self.synthesis_output = ""
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Voice Synthesizer")
        self.setFixedSize(700, 500)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)

        instructions = QLabel(
            "Enter text to synthesize. Each non-empty line is synthesized in order, "
            "and lines can optionally start with [ConfigName]."
        )
        instructions.setWordWrap(True)

        self.text_input = QPlainTextEdit()
        self.text_input.setPlaceholderText(
            "Hello there.\n[Default] This line uses the Default config."
        )

        config_layout = QHBoxLayout()
        config_label = QLabel("Config File:")
        self.config_input = QLineEdit("Default")
        self.config_input.setPlaceholderText("Default")
        config_layout.addWidget(config_label)
        config_layout.addWidget(self.config_input)

        output_layout = QHBoxLayout()
        output_label = QLabel("Save .wav as:")
        default_output = Path(__file__).resolve().parent / "output.wav"
        self.output_input = QLineEdit(str(default_output))
        self.output_input.setPlaceholderText(str(default_output))
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_output_path)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(browse_button)

        button_row = QHBoxLayout()
        self.synthesize_button = QPushButton("Run synthesize.py")
        self.synthesize_button.clicked.connect(self.run_synthesis_script)

        open_old_button = QPushButton("Open old_generations")
        open_old_button.clicked.connect(self.open_old_generations_folder)
        
        clear_button = QPushButton("Run clear.py")
        clear_button.clicked.connect(self.run_clear_script)

        button_row.addWidget(self.synthesize_button)
        button_row.addWidget(open_old_button)
        button_row.addStretch(1)
        button_row.addWidget(clear_button)

        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        layout.addWidget(instructions)
        layout.addWidget(self.text_input)
        layout.addLayout(config_layout)
        layout.addLayout(output_layout)
        layout.addLayout(button_row)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def browse_output_path(self):
        """Choose where the converted wav file should be saved."""
        current_path = self.output_input.text().strip() or str(Path(__file__).resolve().parent / "output.wav")
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save converted wav",
            current_path,
            "WAV Files (*.wav);;All Files (*)"
        )

        if selected_path:
            self.output_input.setText(selected_path)

    def resolve_output_path(self):
        """Resolve the requested wav output path from the GUI."""
        raw_path = self.output_input.text().strip()
        if not raw_path:
            QMessageBox.warning(self, "Missing output path", "Enter a location for the converted .wav file.")
            return None

        output_path = Path(raw_path).expanduser()
        if output_path.suffix.lower() != ".wav":
            output_path = output_path.with_suffix(".wav")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_input.setText(str(output_path))
        return output_path

    def extract_generated_file(self, synth_output):
        """Extract the generated queue file path from synthesize.py output."""
        prefix = "Synthesized speech saved to binary format:"
        base_dir = Path(__file__).resolve().parent

        for line in synth_output.splitlines():
            if line.startswith(prefix):
                generated_path = line.split(prefix, 1)[1].strip()
                path = Path(generated_path)
                return path if path.is_absolute() else base_dir / path

        return None

    def start_conversion(self, input_path, output_path):
        """Run scripts/convert.py to create the requested wav file."""
        script_path = Path(__file__).resolve().parent / "scripts" / "convert.py"

        self.convert_process = QProcess(self)
        self.convert_process.setProgram(sys.executable)
        self.convert_process.setArguments([str(script_path), str(input_path), str(output_path)])
        self.convert_process.setWorkingDirectory(str(Path(__file__).resolve().parent))
        self.convert_process.finished.connect(self.on_conversion_finished)
        self.status_label.setText("Converting to wav...")
        self.convert_process.start()

        if not self.convert_process.waitForStarted(3000):
            error_text = self.convert_process.errorString()
            self.convert_process.deleteLater()
            self.convert_process = None
            self.pending_output_path = None
            self.synthesize_button.setEnabled(True)
            self.status_label.setText("Conversion failed to start.")
            QMessageBox.critical(self, "Failed to start", f"Could not start convert.py:\n{error_text}")

    def open_old_generations_folder(self):
        """Open the old_generations folder in the system file manager."""
        folder_path = Path(__file__).resolve().parent / "old_generations"
        folder_path.mkdir(parents=True, exist_ok=True)

        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder_path)))
        if not opened:
            QMessageBox.warning(
                self,
                "Unable to open folder",
                f"Could not open:\n{folder_path}"
            )

    def run_synthesis_script(self):
        """Run scripts/synthesize.py with textbox content."""
        if self.synth_process is not None or self.convert_process is not None:
            QMessageBox.information(self, "Process running", "Synthesis or conversion is already in progress.")
            return

        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Missing text", "Enter text in the box before running synthesis.")
            return

        output_path = self.resolve_output_path()
        if output_path is None:
            return

        config_name = self.config_input.text().strip() or "Default"
        script_path = Path(__file__).resolve().parent / "scripts" / "synthesize.py"
        self.pending_output_path = output_path
        self.synthesis_output = ""

        self.synth_process = QProcess(self)
        self.synth_process.setProgram(sys.executable)
        self.synth_process.setArguments([str(script_path), text, config_name])
        self.synth_process.setWorkingDirectory(str(Path(__file__).resolve().parent))
        self.synth_process.finished.connect(self.on_synthesis_finished)

        self.synthesize_button.setEnabled(False)
        self.status_label.setText("Synthesizing...")
        self.synth_process.start()

        if not self.synth_process.waitForStarted(3000):
            error_text = self.synth_process.errorString()
            self.synth_process.deleteLater()
            self.synth_process = None
            self.synthesize_button.setEnabled(True)
            self.status_label.setText("Synthesis failed to start.")
            QMessageBox.critical(self, "Failed to start", f"Could not start synthesize.py:\n{error_text}")

    def on_synthesis_finished(self, exit_code, _exit_status):
        """Start conversion after scripts/synthesize.py completes successfully."""
        stdout = bytes(self.synth_process.readAllStandardOutput()).decode("utf-8", errors="replace").strip()
        stderr = bytes(self.synth_process.readAllStandardError()).decode("utf-8", errors="replace").strip()
        self.synthesis_output = stdout

        self.synth_process.deleteLater()
        self.synth_process = None

        if exit_code != 0:
            self.synthesize_button.setEnabled(True)
            self.status_label.setText("Synthesis failed.")
            self.pending_output_path = None
            QMessageBox.critical(
                self,
                "synthesize.py failed",
                f"Exit code: {exit_code}\n\n{stderr or stdout or 'No output.'}"
            )
            return

        generated_file = self.extract_generated_file(stdout)
        if generated_file is None:
            self.synthesize_button.setEnabled(True)
            self.status_label.setText("Synthesis finished, but conversion could not start.")
            self.pending_output_path = None
            QMessageBox.critical(
                self,
                "Missing queue output",
                "synthesize.py finished but the generated queue file path could not be determined."
            )
            return

        self.start_conversion(generated_file, self.pending_output_path)

    def on_conversion_finished(self, exit_code, _exit_status):
        """Show final status once convert.py completes."""
        stdout = bytes(self.convert_process.readAllStandardOutput()).decode("utf-8", errors="replace").strip()
        stderr = bytes(self.convert_process.readAllStandardError()).decode("utf-8", errors="replace").strip()
        output_path = self.pending_output_path

        self.convert_process.deleteLater()
        self.convert_process = None
        self.pending_output_path = None
        self.synthesize_button.setEnabled(True)

        if exit_code == 0:
            self.status_label.setText("Synthesis and conversion finished.")
            message = stdout or "Synthesis and conversion completed successfully."
            if output_path is not None:
                message = f"Saved wav to:\n{output_path}\n\n{message}"

            QMessageBox.information(self, "Conversion finished", message)
        else:
            self.status_label.setText("Conversion failed.")
            error_message = stderr or stdout or self.synthesis_output or "No output."
            QMessageBox.critical(
                self,
                "convert.py failed",
                f"Exit code: {exit_code}\n\n{error_message}"
            )
    
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