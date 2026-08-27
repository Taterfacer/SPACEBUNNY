"""
SpaceBunny: A CodeRabbit GUI Utility
UI Structure: 3-Pane Layout
Author: Joshua Alexander (TaterFacer Software)

Attribution: This is an independent, third-party application. NOT affiliated 
with, endorsed by, or officially associated with CodeRabbit.
"""

import sys, subprocess, json, os, platform, shutil, signal, tempfile, threading, webbrowser
from pathlib import Path
from typing import Optional
from PyQt5 import QtWidgets, QtCore, QtGui

# ==============================================================================
# THEME & CONFIG
# ==============================================================================
C = {
    "BG_DARK": "#08090C",
    "BG_PANEL": "#111318",
    "BG_INPUT": "#0A0B0E",
    "ACCENT_RED": "#D90429",
    "ACCENT_RED_DARK": "#8A031A",
    "ACCENT_CYAN": "#00E5FF",
    "STATUS_GREEN": "#00FF41",
    "TEXT_PRIMARY": "#D1D1D6",
    "TEXT_MUTED": "#5A5D6B",
    "BORDER": "#1F2229"
}

QSS = f"""QWidget{{background:{C['BG_DARK']};color:{C['TEXT_PRIMARY']};font-family:'Consolas',monospace;font-size:12px;}}
QFrame#panel{{background:{C['BG_PANEL']};border:1px solid {C['BORDER']};}}
QPushButton{{background:{C['BG_INPUT']};color:{C['TEXT_PRIMARY']};border:1px solid {C['BORDER']};padding:6px 12px;font-weight:bold;}}
QPushButton:hover{{background:{C['ACCENT_RED']};color:#FFF;border-color:{C['ACCENT_RED']};}}
QPushButton#primary{{background:{C['ACCENT_RED']};color:#FFF;border:1px solid {C['ACCENT_RED']};font-size:14px;}}
QPushButton#nav{{background:transparent;color:{C['TEXT_MUTED']};border:none;border-left:3px solid transparent;text-align:left;padding:10px 15px;}}
QPushButton#nav:hover,QPushButton#nav:checked{{background:{C['BG_PANEL']};color:{C['TEXT_PRIMARY']};border-left-color:{C['ACCENT_RED']};}}
QLineEdit,QPlainTextEdit{{background:{C['BG_INPUT']};border:1px solid {C['BORDER']};padding:8px;color:{C['TEXT_PRIMARY']};}}
QLineEdit:focus{{border-color:{C['ACCENT_RED']};}}
QScrollBar:vertical{{background:{C['BG_DARK']};width:6px;}}QScrollBar::handle:vertical{{background:{C['BORDER']};min-height:20px;}}
QLabel#hdr{{color:{C['TEXT_MUTED']};font-size:10px;font-weight:bold;letter-spacing:1px;margin-bottom:8px;}}"""

INSTALL_SCRIPTS = {"Windows": 'powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://cli.coderabbit.ai/install.ps1 | iex"',
                   "Darwin": 'sh -c "$(curl -fsSL https://cli.coderabbit.ai/install.sh)"', "Linux": 'sh -c "$(curl -fsSL https://cli.coderabbit.ai/install.sh)"'}
INSTALL_PATHS = {"Windows": [Path.home()/"AppData/Local/Programs/CodeRabbit/coderabbit.exe", Path.home()/"AppData/Local/CodeRabbit/coderabbit.exe"],
                 "Darwin": [Path("/opt/homebrew/bin/coderabbit"), Path.home()/".local/bin/coderabbit"],
                 "Linux": [Path("/usr/local/bin/coderabbit"), Path.home()/".local/bin/coderabbit"]}

# ==============================================================================
# BACKEND LOGIC
# ==============================================================================
class AppSettings:
    def __init__(self):
        self.path = Path.home() / ".spacebunny" / "settings.json"
        self.defaults = {"mute_sounds": False, "auto_git_init": True, "last_folder": ""}
        self.data = {**self.defaults}
        if self.path.exists():
            try: self.data.update(json.loads(self.path.read_text()))
            except: pass
    def get(self, k): return self.data.get(k, self.defaults.get(k))
    def set(self, k, v):
        if self.data.get(k) != v: self.data[k] = v; self.path.parent.mkdir(parents=True, exist_ok=True); self.path.write_text(json.dumps(self.data, indent=2))

class EndpointHealer:
    def __init__(self): self.cli_path, self.cli_version, self.os_name = None, None, platform.system()
    def discover_cli(self):
        paths = [Path(sys._MEIPASS)/("coderabbit.exe" if self.os_name=="Windows" else "coderabbit")] if getattr(sys,'frozen',False) else []
        if w := shutil.which('coderabbit'): paths.append(Path(w))
        paths.extend(INSTALL_PATHS.get(self.os_name, []))
        for p in paths:
            if p.exists(): self.cli_path = str(p.resolve()); return self.cli_path
        return None
    def detect_version(self):
        if not self.cli_path: return None
        try: r = subprocess.run([self.cli_path, "--version"], capture_output=True, text=True, timeout=10)
        except: return None
        return r.stdout.strip() if r.returncode == 0 else None
    def check_status(self):
        if not self.discover_cli(): return {"status": "not_found"}
        if v := self.detect_version(): return {"status": "ready", "version": v}
        return {"status": "broken"}

class GitHelper:
    @staticmethod
    def is_git_repo(p): return (p / '.git').is_dir()
    
    @staticmethod
    def has_commits(p):
        r = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=p, capture_output=True, text=True)
        return r.returncode == 0

    @staticmethod
    def init_repo(p):
        if not shutil.which('git'): return False, "Git not installed."
        try:
            subprocess.run(['git', 'init'], cwd=p, capture_output=True, text=True, timeout=30)
            subprocess.run(['git', 'add', '.'], cwd=p, capture_output=True, text=True, timeout=30)
            r = subprocess.run(['git', 'commit', '-m', 'chore: initial commit by SpaceBunny'], cwd=p, capture_output=True, text=True, timeout=30)
            return (True, "Git initialized and committed.") if r.returncode == 0 else (True, "Git initialized. (Folder might be empty)")
        except Exception as e: return False, str(e)

    @staticmethod
    def ensure_commits(p):
        """Fixes repos that have .git but no commits."""
        if not shutil.which('git'): return False
        subprocess.run(['git', 'add', '.'], cwd=p, capture_output=True, text=True, timeout=30)
        r = subprocess.run(['git', 'commit', '-m', 'chore: initial commit by SpaceBunny'], cwd=p, capture_output=True, text=True, timeout=30)
        return r.returncode == 0

class ReviewWorker(QtCore.QThread):
    output_ready = QtCore.pyqtSignal(str); finished = QtCore.pyqtSignal(int)
    def __init__(self, cmd): super().__init__(); self.cmd = cmd; self.process = None
    def run(self):
        try:
            self.process = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            if self.process.stdout:
                for line in iter(self.process.stdout.readline, ''): self.output_ready.emit(line)
            self.process.wait(); self.finished.emit(self.process.returncode)
        except Exception as e: self.output_ready.emit(f"\n[CRITICAL] {e}\n"); self.finished.emit(1)
        finally:
            if self.process and self.process.stdout: self.process.stdout.close()
    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate() if platform.system() == "Windows" else self.process.send_signal(signal.SIGTERM)
            try: self.process.wait(timeout=3)
            except: self.process.kill()

# ==============================================================================
# MAIN UI: 3-PANE LAYOUT
# ==============================================================================
class SpaceBunnyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPACEBUNNY // CODERABBIT UTILITY")
        self.resize(1200, 800)
        self.setStyleSheet(QSS)
        
        self.icon_path = Path(__file__).parent / "spacebunny_icon.png"
        if self.icon_path.exists(): self.setWindowIcon(QtGui.QIcon(str(self.icon_path)))
        
        self.settings = AppSettings()
        self.selected_path = self.settings.get("last_folder")
        self.healer = EndpointHealer()
        self.git = GitHelper()
        self.worker = None
        
        self._build_3pane_layout()
        self._update_cli_status()

    def play_ui_sound(self, sound_type: str) -> None:
        if not self.settings.get("mute_sounds"):
            try:
                import winsound
                if sound_type == "click": winsound.Beep(800, 40)
                elif sound_type == "success": winsound.Beep(1200, 150)
            except Exception: pass

    def _build_3pane_layout(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QHBoxLayout(central)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)
        
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        # --- LEFT PANE: MENU ---
        left = QtWidgets.QFrame()
        left.setFixedWidth(200)
        left.setStyleSheet(f"background:{C['BG_PANEL']};border-right:1px solid {C['BORDER']};")
        left_lay = QtWidgets.QVBoxLayout(left)
        left_lay.setContentsMargins(0,10,0,10)
        
        left_lay.addWidget(QtWidgets.QLabel("  MENU", objectName="hdr"))
        for txt, func in [("🚀  REVIEW", self.execute_review), ("📂  PROJECT FOLDER", self.browse_folder), ("⚙️  SETTINGS", self.open_settings)]:
            btn = QtWidgets.QPushButton(txt); btn.setObjectName("nav"); btn.setCheckable(True); btn.clicked.connect(func)
            if txt == "  REVIEW": btn.setChecked(True)
            left_lay.addWidget(btn)
        left_lay.addStretch()
        left_lay.addWidget(QtWidgets.QLabel("  v1.2.0 // TATERFACER", styleSheet=f"color:{C['TEXT_MUTED']};font-size:9px;padding:10px;"))
        splitter.addWidget(left)
        
        # --- CENTER PANE: OUTPUT & INPUT ---
        center = QtWidgets.QWidget()
        center_lay = QtWidgets.QVBoxLayout(center)
        center_lay.setContentsMargins(15,15,15,15)
        center_lay.setSpacing(10)
        
        hdr = QtWidgets.QFrame(); hdr.setObjectName("panel"); hdr.setFixedHeight(50)
        hdr_lay = QtWidgets.QHBoxLayout(hdr); hdr_lay.setContentsMargins(15,0,15,0)
        logo = QtWidgets.QLabel()
        if self.icon_path.exists(): logo.setPixmap(QtGui.QPixmap(str(self.icon_path)).scaled(30,30,QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))
        else: logo.setText("🐰"); logo.setStyleSheet("font-size:20px;")
        hdr_lay.addWidget(logo)
        hdr_lay.addWidget(QtWidgets.QLabel("SPACEBUNNY", styleSheet=f"color:{C['ACCENT_RED']};font-size:18px;font-weight:bold;letter-spacing:2px;margin-left:10px;"))
        hdr_lay.addStretch()
        self.lbl_cli = QtWidgets.QLabel(" CLI NOT FOUND"); self.lbl_cli.setStyleSheet(f"color:{C['ACCENT_RED']};font-weight:bold;")
        hdr_lay.addWidget(self.lbl_cli)
        center_lay.addWidget(hdr)
        
        self.txt_output = QtWidgets.QPlainTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setPlaceholderText("> Review output will stream here...")
        center_lay.addWidget(self.txt_output, 1)
        
        inp_frame = QtWidgets.QFrame(); inp_frame.setObjectName("panel")
        inp_lay = QtWidgets.QHBoxLayout(inp_frame); inp_lay.setContentsMargins(10,10,10,10)
        self.entry_directives = QtWidgets.QLineEdit()
        self.entry_directives.setPlaceholderText("Type review directives (e.g., Focus on security flaws) and press Enter...")
        self.entry_directives.returnPressed.connect(self.execute_review)
        inp_lay.addWidget(self.entry_directives, 1)
        self.btn_run = QtWidgets.QPushButton(" RUN REVIEW"); self.btn_run.setObjectName("primary"); self.btn_run.setFixedWidth(150); self.btn_run.clicked.connect(self.execute_review)
        inp_lay.addWidget(self.btn_run)
        center_lay.addWidget(inp_frame)
        splitter.addWidget(center)
        
        # --- RIGHT PANE: SETTINGS ---
        right = QtWidgets.QFrame()
        right.setFixedWidth(300)
        right.setStyleSheet(f"background:{C['BG_PANEL']};border-left:1px solid {C['BORDER']};")
        right_lay = QtWidgets.QVBoxLayout(right)
        right_lay.setContentsMargins(15,15,15,15)
        
        right_lay.addWidget(QtWidgets.QLabel("⚙️ SETTINGS", objectName="hdr"))
        
        auth_frame = QtWidgets.QFrame(); auth_frame.setObjectName("panel")
        auth_lay = QtWidgets.QVBoxLayout(auth_frame); auth_lay.setContentsMargins(10,10,10,10)
        auth_lay.addWidget(QtWidgets.QLabel(" CLI LOGIN", objectName="hdr"))
        self.btn_auth = QtWidgets.QPushButton("Authenticate Browser"); self.btn_auth.clicked.connect(self.run_auth); self.btn_auth.setEnabled(False)
        auth_lay.addWidget(self.btn_auth)
        self.btn_install = QtWidgets.QPushButton("⚙️ Install CLI"); self.btn_install.setObjectName("primary"); self.btn_install.clicked.connect(self._install_cli); self.btn_install.hide()
        auth_lay.addWidget(self.btn_install)
        right_lay.addWidget(auth_frame)
        
        folder_frame = QtWidgets.QFrame(); folder_frame.setObjectName("panel")
        folder_lay = QtWidgets.QVBoxLayout(folder_frame); folder_lay.setContentsMargins(10,10,10,10)
        folder_lay.addWidget(QtWidgets.QLabel(" PROJECT FOLDER", objectName="hdr"))
        self.lbl_path = QtWidgets.QLabel("No folder selected" if not self.selected_path else f"📂 {self.selected_path}")
        self.lbl_path.setStyleSheet(f"color:{C['TEXT_MUTED'] if not self.selected_path else C['TEXT_PRIMARY']};")
        self.lbl_path.setWordWrap(True)
        folder_lay.addWidget(self.lbl_path)
        right_lay.addWidget(folder_frame)
        
        settings_frame = QtWidgets.QFrame(); settings_frame.setObjectName("panel")
        settings_lay = QtWidgets.QVBoxLayout(settings_frame); settings_lay.setContentsMargins(10,10,10,10)
        settings_lay.addWidget(QtWidgets.QLabel("🎛️ OPTIONS", objectName="hdr"))
        self.chk_mute = QtWidgets.QCheckBox("Mute UI Sounds"); self.chk_mute.setChecked(self.settings.get("mute_sounds")); self.chk_mute.stateChanged.connect(lambda: self.settings.set("mute_sounds", self.chk_mute.isChecked()))
        self.chk_git = QtWidgets.QCheckBox("Auto-fix Git issues"); self.chk_git.setChecked(self.settings.get("auto_git_init")); self.chk_git.stateChanged.connect(lambda: self.settings.set("auto_git_init", self.chk_git.isChecked()))
        settings_lay.addWidget(self.chk_mute); settings_lay.addWidget(self.chk_git)
        right_lay.addWidget(settings_frame)
        
        right_lay.addStretch()
        splitter.addWidget(right)
        
        splitter.setSizes([200, 700, 300])
        root.addWidget(splitter)

    def _update_cli_status(self):
        report = self.healer.check_status()
        if report["status"] == "ready":
            self.lbl_cli.setText(f"🟢 CLI READY (v{report['version']})"); self.lbl_cli.setStyleSheet(f"color:{C['STATUS_GREEN']};font-weight:bold;")
            self.btn_install.hide(); self.btn_auth.setEnabled(True)
        else:
            self.lbl_cli.setText("🔴 CLI NOT FOUND"); self.lbl_cli.setStyleSheet(f"color:{C['ACCENT_RED']};font-weight:bold;")
            self.btn_install.show(); self.btn_auth.setEnabled(False)

    def _install_cli(self):
        script = INSTALL_SCRIPTS.get(self.healer.os_name)
        if script:
            subprocess.Popen(script, shell=True)
            QtWidgets.QMessageBox.information(self, "Install", "Installer launched. Restart app when done.")

    def open_settings(self): pass

    def run_auth(self):
        self.play_ui_sound("click")
        if self.healer.cli_path:
            subprocess.Popen([self.healer.cli_path, "auth", "login"])
            QtWidgets.QMessageBox.information(self, "Auth", "Browser opened. Complete login.")

    def browse_folder(self):
        self.play_ui_sound("click")
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "SELECT PROJECT FOLDER")
        if not folder: return
        path = Path(folder).resolve()
        
        if not self.git.is_git_repo(path):
            if self.settings.get("auto_git_init"):
                if QtWidgets.QMessageBox.question(self, "GIT REQUIRED", "Not a Git repo. Initialize now?") == QtWidgets.QMessageBox.Yes:
                    ok, msg = self.git.init_repo(path)
                    if not ok: QtWidgets.QMessageBox.critical(self, "ERR", msg); return
            else:
                QtWidgets.QMessageBox.warning(self, "WARNING", "Not a Git repo and auto-fix is disabled."); return
        else:
            # Fix the "no HEAD" error if it's a repo but has no commits
            if not self.git.has_commits(path):
                if self.settings.get("auto_git_init"):
                    if not self.git.ensure_commits(path):
                        QtWidgets.QMessageBox.warning(self, "WARNING", "Repo has no commits and folder appears empty. Add files first.")
                        return
                else:
                    QtWidgets.QMessageBox.warning(self, "WARNING", "Repo has no commits. CodeRabbit requires at least one commit.")
                    return

        self.selected_path = str(path); self.settings.set("last_folder", self.selected_path)
        self.lbl_path.setText(f"📂 {self.selected_path}"); self.lbl_path.setStyleSheet(f"color:{C['TEXT_PRIMARY']};")

    def execute_review(self):
        self.play_ui_sound("click")
        if not self.healer.cli_path: self._update_cli_status(); QtWidgets.QMessageBox.warning(self, "ERR", "CLI missing."); return
        if not self.selected_path: QtWidgets.QMessageBox.warning(self, "ERR", "Select a project folder."); return
        
        # Double check commits right before running
        if not self.git.has_commits(Path(self.selected_path)):
            QtWidgets.QMessageBox.critical(self, "ERR", "This folder has no Git commits. CodeRabbit cannot run. Please commit your files.")
            return

        self.btn_run.setEnabled(False); self.btn_run.setText("⏳ RUNNING...")
        self.txt_output.clear(); self.txt_output.appendPlainText("> Starting CodeRabbit review...\n")
        
        cmd = [self.healer.cli_path, "review", "--agent", "--uncommitted", "--dir", self.selected_path]
        if instr := self.entry_directives.text().strip():
            tf = Path(tempfile.gettempdir()) / f"sb_{os.getpid()}.md"
            tf.write_text(f"# Review Directives\n{instr}\n", encoding='utf-8')
            cmd.extend(["--config", str(tf)])
            threading.Thread(target=self._cleanup_temp_file, args=(tf,), daemon=True).start()
            
        self.worker = ReviewWorker(cmd)
        self.worker.output_ready.connect(lambda t: self.txt_output.insertPlainText(t))
        self.worker.finished.connect(self._review_finished)
        self.worker.start()

    def _cleanup_temp_file(self, tf_path):
        """Safely remove temp file after a delay"""
        try:
            import time
            time.sleep(5)
            if tf_path.exists():
                tf_path.unlink()
        except Exception:
            pass

    def _review_finished(self, code):
        self.btn_run.setEnabled(True); self.btn_run.setText(" RUN REVIEW")
        self.txt_output.appendPlainText(f"\n> Process terminated. Exit code: {code}")
        if code == 0: self.play_ui_sound("success")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning(): self.worker.stop()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    p = QtGui.QPalette()
    p.setColor(QtGui.QPalette.Window, QtGui.QColor(C['BG_DARK'])); p.setColor(QtGui.QPalette.WindowText, QtGui.QColor(C['TEXT_PRIMARY']))
    p.setColor(QtGui.QPalette.Base, QtGui.QColor(C['BG_INPUT'])); p.setColor(QtGui.QPalette.Text, QtGui.QColor(C['TEXT_PRIMARY']))
    p.setColor(QtGui.QPalette.Button, QtGui.QColor(C['BG_PANEL'])); p.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(C['TEXT_PRIMARY']))
    p.setColor(QtGui.QPalette.Highlight, QtGui.QColor(C['ACCENT_RED'])); p.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#FFFFFF"))
    app.setPalette(p)
    win = SpaceBunnyApp(); win.show(); sys.exit(app.exec_())