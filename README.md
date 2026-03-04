import os

readme_content = """# 🧠 SmartShell

An AI-powered, multi-platform command-line assistant that translates natural language into executable OS commands, explains complex shell instructions, and keeps a local history of your workflows.

Powered by Groq's lightning-fast API, SmartShell detects your operating system (Windows, Linux, or macOS) and writes the correct syntax (PowerShell or Bash) automatically.

---

## 🚀 Features

* **OS-Aware Execution:** Automatically detects your environment and generates native commands.
* **Custom Aliases:** Name your assistant whatever you want (e.g., `jarvis`, `khet`, `nova`) during setup.
* **Smart Explanations:** Clean, bulleted breakdowns of complex terminal commands without the fluff.
* **Local Vault:** A secure, local SQLite database stores your command history and API key.
* **WSL Support:** Engineered to bridge headless Linux subsystems with Windows host browsers.

---

## ⚙️ Installation

SmartShell can be installed globally directly from GitHub. Choose your operating system below:

### 🪟 Windows (CMD / PowerShell)
Open your standard terminal and run:
```cmd
pip install git+[https://github.com/avikumarzs/SmartShell.git](https://github.com/avikumarzs/SmartShell.git)