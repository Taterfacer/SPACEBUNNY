Here is a complete, professional, and engaging `README.md` template tailored for your GitHub repository. You can copy and paste this directly into your repo.

***

# 🐰 SpaceBunny

**A sleek, third-party GUI Utility for the CodeRabbit CLI.**

> ⚠️ **Disclaimer:** *SpaceBunny is an independent, third-party application. It is NOT affiliated with, endorsed by, or officially associated with CodeRabbit.*

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

SpaceBunny brings a modern, cyberpunk-inspired graphical interface to the CodeRabbit command-line tool. It eliminates the friction of terminal management, auto-heals common Git repository issues, and allows you to inject custom review directives on the fly.

---

## ✨ Features

*   **🖥️ Modern 3-Pane Layout:** A cyberpunk-aesthetic dark UI featuring a navigation menu, a real-time streaming output console, and a dedicated settings/status panel.
*   **🔍 Smart CLI Discovery & Installation:** Automatically scans your system for the CodeRabbit CLI. If missing, it provides 1-click installation scripts for Windows, macOS, and Linux.
*   **🌿 Git Auto-Healing:** CodeRabbit requires a valid Git repository with at least one commit. SpaceBunny detects missing `.git` folders or empty repos and automatically initializes and commits them for you (fully configurable).
*   **🎯 Custom Directives:** Want the AI to focus on something specific? Type custom instructions (e.g., *"Focus on security flaws and memory leaks"*) directly into the UI, and SpaceBunny dynamically generates a temporary config file to pass to the CLI.
*   **📡 Real-Time Streaming:** Watch the CodeRabbit agent's output stream live into the console pane using background threading.
*   **🔊 Retro UI Sounds:** Optional auditory feedback (beeps) for button clicks and successful completions.
*   **⚙️ Persistent Settings:** Remembers your last used project folder, sound preferences, and Git auto-fix settings via a local JSON config.

---

<img width="1200" height="788" alt="PaceBunny_Screenshot " src="https://github.com/user-attachments/assets/53109071-8a6a-4da6-984d-767056bd4475" />

## 🚀 Installation

### Prerequisites
*   **Python 3.8+**
*   **Git** (installed and available in your system PATH)
*   **PyQt5**

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/YourUsername/SpaceBunny.git
   cd SpaceBunny
   ```
2. Install the required dependencies:
   ```bash
   pip install PyQt5
   ```
3. Run the application:
   ```bash
   python SpaceBunny.py
   ```

*(Optional: You can package this into a standalone executable using `pyinstaller`)*

---

## 🛠️ Usage Guide

### 1. Setup the CLI
When you first launch SpaceBunny, it will check for the CodeRabbit CLI. 
* If it's missing, click **⚙️ Install CLI** in the right-hand panel to launch the official installer script for your OS.
* Once installed, click **Authenticate Browser** to log in to your CodeRabbit account via your default web browser.

### 2. Select a Project
Click **📂 PROJECT FOLDER** in the left menu (or use the right panel) to select the codebase you want to review. 
* *Note: If the folder isn't a Git repo, SpaceBunny will prompt you to auto-initialize it.*

### 3. Run a Review
* Type any specific instructions in the **Directives** input box at the bottom (e.g., `Check for PEP8 compliance and SQL injection vulnerabilities`).
* Click **🚀 RUN REVIEW** (or press `Enter`).
* Watch the live output stream in the center pane!

---

## 🎨 UI / UX Details

SpaceBunny uses a custom QSS (Qt Style Sheets) theme inspired by sci-fi/cyberpunk terminals:
* **Backgrounds:** Deep space darks (`#08090C`, `#111318`)
* **Accents:** Crimson Red (`#D90429`) and Cyan (`#00E5FF`)
* **Typography:** Monospace (`Consolas`) for that authentic developer terminal feel.
* **Layout:** Resizable 3-pane splitter (Left: Navigation | Center: Console | Right: Context & Settings).

---

## 🏗️ Architecture

*   **Frontend:** PyQt5 (Custom QSS styling, `QSplitter` 3-pane layout, `QThread` for non-blocking UI).
*   **Backend:** Python `subprocess` for CLI execution and Git operations.
*   **State Management:** Local JSON storage (`~/.spacebunny/settings.json`) for user preferences.
*   **Security:** Custom directives are written to an isolated, auto-deleting temporary file in the OS temp directory to prevent CLI argument injection.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! 
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👨‍💻 Author

**Joshua Alexander**  
*TaterFacer Software*

If you find SpaceBunny useful, consider dropping a ⭐ on the repository!
