# 🧠 SmartShell

An AI-powered, multi-platform command-line assistant that translates natural language into executable OS commands, explains complex shell instructions, and keeps a local history of your workflows.

Powered by Groq's lightning-fast API, SmartShell detects your operating system (Windows or Linux) and writes the correct syntax (PowerShell or Bash) automatically.

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
`pip install git+https://github.com/avikumarzs/SmartShell.git`

*(Note: If `pip` is not recognized, use `py -m pip install git+https://github.com/avikumarzs/SmartShell.git`)*

### 🐧 Linux (Ubuntu / Debian / WSL)
Linux environments strictly manage system packages. Install the prerequisites and use the `--user` flag to install safely:

**1. Install prerequisites**
```sudo apt update```
`sudo apt install python3-pip git -y`

**2. Install SmartShell globally for your user**
`pip3 install --user --break-system-packages git+https://github.com/avikumarzs/SmartShell.git`

**3. Add the local bin to your PATH (if not already configured)**
```echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc```
`source ~/.bashrc`

---

## 🔑 Configuration & Setup

Once installed, initialize your assistant and link it to the Groq API:

`smart config`

1. The setup wizard will guide you to generate a free API key from Groq.
2. Paste the key when prompted.
3. **Choose an Alias:** You can type a custom name for your assistant (like `jarvis` or `ronaldo`). If you set an alias, you will use that word instead of `smart` for all future commands!

---

## 🛠️ Usage Guide

*(Note: If you created a custom alias during setup, use it in place of `smart` below)*

### 1. The "Do" Engine (Action)
Tell the AI what you want to achieve in natural language. It will generate the correct command for your OS and ask for permission to execute it.
`smart do "create a folder named test_project and put an empty text file inside it"`
`smart do "find all text files in this directory and sort them by size"`

### 2. The "Explain" Engine (Knowledge)
Paste a confusing command, and the AI will break down exactly what it does, flag by flag.
`smart explain "chmod 777"`
`smart explain "git commit -am 'update'"`

### 3. The History Vault
View a formatted table of all the commands you have successfully executed and explained.
`smart history`

---

## 🗑️ Uninstallation

If you need to completely remove SmartShell and wipe your local database:

**Windows:**
`py -m pip uninstall smartshell -y`
`rmdir /s /q "%USERPROFILE%\.smartshell"`

**Linux / Ubuntu:**
`pip3 uninstall smartshell --break-system-packages -y`
`rm -rf ~/.smartshell`
`rm -f ~/.local/bin/smart`

---

## 💻 Tech Stack

* **Language:** Python 3.x
* **AI Engine:** Groq API (LLaMA 3 / Mixtral)
* **CLI Framework:** Rich (for terminal formatting)
* **Database:** SQLite3 (local history vault)

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! 
If you find a bug or have a suggestion for a new feature (like supporting a new OS or adding a new command engine), please open an issue or submit a pull request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
