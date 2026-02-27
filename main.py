import shutil
import sys
import stat
import typer
import os
import platform
import subprocess
import sqlite3
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.panel import Panel
import webbrowser
from rich.markdown import Markdown

# --- GLOBAL CONFIGURATION ---
USER_HOME = os.path.expanduser("~")
CONFIG_DIR = os.path.join(USER_HOME, ".smartshell")
os.makedirs(CONFIG_DIR, exist_ok=True)

ENV_FILE = os.path.join(CONFIG_DIR, ".env")
DB_PATH = os.path.join(CONFIG_DIR, "smartshell.db")

console = Console()
app = typer.Typer()

# 1. Setup & Auth
load_dotenv(ENV_FILE)
api_key = os.getenv("GROQ_API_KEY")

# Create a dummy client initially to avoid crashing before config
client = Groq(api_key=api_key) if api_key else None

@app.command()
def config():
    """Initial setup to save your API key and set assistant name."""
    console.print("[bold cyan]Welcome to SmartShell Setup![/bold cyan]")
    
    # --- NEW: Helpful Redirect ---
    console.print("\nTo use this tool, you need a free API key from Groq.")
    console.print("Get one here: [bold blue][link=https://console.groq.com/keys]https://console.groq.com/keys[/link][/bold blue]")
    
    if Confirm.ask("Would you like to open this link in your browser now?"):
        webbrowser.open("https://console.groq.com/keys")
        console.print("[dim]Opening browser... Once you have your key, return here.[/dim]")
    
    key = Prompt.ask("\nPlease paste your Groq API Key").strip()
    
    with open(ENV_FILE, "w") as f:
        f.write(f"GROQ_API_KEY={key}\n")
    
    console.print(f"\n[bold green]✅ Key saved securely in {ENV_FILE}[/bold green]")
    
    # --- ALIAS GENERATOR ---
    custom_name = Prompt.ask(
        "What would you like to name your AI assistant? (Default key => smart)"
    ).strip().lower()

    if custom_name != "smart":
        smart_path = shutil.which("smart")
        
        if smart_path:
            scripts_dir = os.path.dirname(smart_path)
            
            try:
                # 1. Create Windows Batch File (.bat)
                bat_path = os.path.join(scripts_dir, f"{custom_name}.bat")
                with open(bat_path, "w") as f:
                    f.write(f"@echo off\nsmart %*\n")
                
                # 2. Create Mac/Linux Shell Script
                sh_path = os.path.join(scripts_dir, f"{custom_name}")
                with open(sh_path, "w") as f:
                    f.write(f'#!/bin/sh\nsmart "$@"\n')
                
                st = os.stat(sh_path)
                os.chmod(sh_path, st.st_mode | stat.S_IEXEC)
                
                console.print(f"\n[bold green]✅ Assistant successfully renamed to '{custom_name}'![/bold green]")
                console.print(f"You can now run [bold yellow]{custom_name} do[/bold yellow] from any folder!")
            except Exception as e:
                console.print(f"\n[bold red]❌ Could not create alias: {e}[/bold red]")
                console.print("You can still run [bold yellow]smart do[/bold yellow].")
        else:
            console.print("\n[bold red]❌ Could not locate installation path.[/bold red]")
    else:
        console.print("\nYou can now run [bold yellow]smart do[/bold yellow] from any folder!")
# 2. Database Manager
class HistoryManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_table()
        self.migrate() # Automatically updates old databases!

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cmd_type TEXT,
            task TEXT,
            command TEXT,
            os_info TEXT
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def migrate(self):
        """Adds the new cmd_type column to existing databases without deleting them."""
        try:
            self.conn.execute("ALTER TABLE history ADD COLUMN cmd_type TEXT DEFAULT 'do'")
            self.conn.commit()
        except sqlite3.OperationalError:
            # If the column already exists, SQLite throws an error, which we just ignore.
            pass

    def save(self, cmd_type, task, command, os_info):
        try:
            query = "INSERT INTO history (timestamp, cmd_type, task, command, os_info) VALUES (?, ?, ?, ?, ?)"
            self.conn.execute(query, (datetime.now().strftime("%Y-%m-%d %H:%M"), cmd_type, task, command, os_info))
            self.conn.commit() 
            return True
        except Exception as e:
            console.print(f"[dim red]Database Error: {e}[/]")
            return False

    def get_all(self, limit=10):
        # We now pull 4 columns: timestamp, cmd_type, task, command
        return self.conn.execute("SELECT timestamp, cmd_type, task, command FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    def clear_all(self):
        self.conn.execute("DELETE FROM history")
        self.conn.commit()

history_db = HistoryManager()

def get_system_info():
    system = platform.system()
    if system == "Windows":
        return "Windows", "PowerShell", "powershell"
    return (system, "Bash", "bash")

def check_risk(command: str):
    dangerous_keywords = ["rm", "del", "format", "erase", "drop", "truncate", "shutdown", "reboot", "remove-item", "ri ", "rd /s"]
    found_risks = [word for word in dangerous_keywords if word in command.lower()]
    return found_risks

@app.command()
def do(task: str):
    """Generates, logs, and executes a command."""
    os_name, shell_name, executable = get_system_info()
    console.print(f"\n[bold cyan]Env:[/bold cyan] {os_name} | [bold green]Task:[/bold green] {task}")
    
    prompt = f"Translate to a single {shell_name} command for {os_name} (output ONLY the command): {task}"
    
    try:
        with console.status("[bold blue]Consulting AI...[/]"):
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
            )
        
        command = response.choices[0].message.content.strip()
        command = command.replace("```powershell", "").replace("```bash", "").replace("```", "").replace("`", "").strip()
        
        risks = check_risk(command)
        border_color = "red" if risks else "green"
        
        console.print(f"\n")
        console.print(Panel(f"[bold white on black] {command} [/]", title="SUGGESTION", border_style=border_color))
        
        if risks:
            console.print(f"[bold red]WARNING:[/bold red] Destructive action detected: {', '.join(risks)}.")
        
        if Confirm.ask(f"Run and log this command?"):
            # Passing "do" as the new first argument
            if history_db.save("do", task, command, os_name):
                console.print("[dim green]✔ Logged to history[/]")
            
            flag = "-Command" if os_name == "Windows" else "-c"
            subprocess.run([executable, flag, command])
            
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")

@app.command()
def explain(command: str):
    """Explains a command or answers a CLI question in detail."""
    prompt = f"""You are a technical CLI expert. The user asked: `{command}`.

    Directly answer the question or explain the command.
    - If the user provided a raw command, explain its purpose, key flags, and give examples.
    - If the user asked a question, answer it directly, completely, and precisely.

    CRITICAL RULES:
    1. Format your response in clean Markdown using bullet points and bold text for readability.
    2. Do NOT use triple backticks (```) for code blocks. Use single backticks (`code`) instead.
    3. STRICTLY NO FLUFF: Do not write introductions, overviews, or conclusions. Never say "Here is the explanation" or "As a DevOps Engineer". Start immediately with the technical facts.
    """
    
    try:
        with console.status("[bold blue]Analyzing...[/]"):
            response = client.chat.completions.create(
                messages=[{"role":"user","content":prompt}], 
                model="llama-3.1-8b-instant"
            )
            
        raw_content = response.choices[0].message.content.strip()
        # Clean out any rogue backticks just in case
        clean_content = raw_content.replace("```bash", "").replace("```powershell", "").replace("```", "")
        
        explanation = Markdown(clean_content)
        # Simplified the title so it doesn't stretch too long with long questions
        console.print(Panel(explanation, title="EXPLANATION", border_style="blue", padding=(1, 2)))
        
        # Log this interaction to the database
        os_name, _, _ = get_system_info()
        history_db.save("explain", "Explanation Request", command, os_name)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@app.command()
def history(limit: int = 10):
    """Shows recent history."""
    items = history_db.get_all(limit)
    if not items:
        console.print("[yellow]History is empty.[/yellow]")
        return

    table = Table(title="Recent Tasks")
    table.add_column("Time", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Intent", style="green")
    table.add_column("Command", style="magenta")

    for item in items:
        # Accessing indices 0-3 correctly to match the 4 returned columns
        table.add_row(item[0], item[1], item[2], item[3])
    console.print(table)

@app.command()
def clear():
    """Wipes the database."""
    if Confirm.ask("[bold red]Delete everything?[/]"):
        history_db.clear_all()
        console.print("[bold green]History cleared.[/bold green]")

if __name__ == "__main__":
    app()