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
from rich.markdown import Markdown

# --- GLOBAL CONFIGURATION ---
# This ensures the DB and API key are saved to the user's home directory (e.g., ~/.smartshell)
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
    """Initial setup to save your API key globally."""
    console.print("[bold cyan]Welcome to SmartShell Setup![/bold cyan]")
    key = Prompt.ask("Please paste your Groq API Key")
    
    with open(ENV_FILE, "w") as f:
        f.write(f"GROQ_API_KEY={key}\n")
    
    console.print(f"[bold green]✅ Key saved securely in {ENV_FILE}[/bold green]")
    console.print("You can now run [bold yellow]smart do[/bold yellow] from any folder!")

# 2. Database Manager
class HistoryManager:
    def __init__(self):
        # We use the global DB_PATH now
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            task TEXT,
            command TEXT,
            os_info TEXT
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def save(self, task, command, os_info):
        try:
            query = "INSERT INTO history (timestamp, task, command, os_info) VALUES (?, ?, ?, ?)"
            self.conn.execute(query, (datetime.now().strftime("%Y-%m-%d %H:%M"), task, command, os_info))
            self.conn.commit() 
            return True
        except Exception as e:
            console.print(f"[dim red]Database Error: {e}[/]")
            return False

    def get_all(self, limit=10):
        return self.conn.execute("SELECT timestamp, task, command FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    def clear_all(self):
        self.conn.execute("DELETE FROM history")
        self.conn.commit()

history_db = HistoryManager()

# --- KEEP THE REST OF YOUR CODE EXACTLY THE SAME BELOW THIS LINE ---
# def get_system_info(): ...

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
        
        # IMPROVED CLEANING: Strips backticks, code blocks, and extra whitespace
        command = response.choices[0].message.content.strip()
        command = command.replace("```powershell", "").replace("```bash", "").replace("```", "").replace("`", "").strip()
        
        risks = check_risk(command)
        border_color = "red" if risks else "green"
        
        console.print(f"\n")
        console.print(Panel(f"[bold white on black] {command} [/]", title="SUGGESTION", border_style=border_color))
        
        if risks:
            console.print(f"[bold red]WARNING:[/bold red] Destructive action detected: {', '.join(risks)}.")
        
        if Confirm.ask(f"Run and log this command?"):
            if history_db.save(task, command, os_name):
                console.print("[dim green]✔ Logged to history[/]")
            
            flag = "-Command" if os_name == "Windows" else "-c"
            subprocess.run([executable, flag, command])
            
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")

@app.command()
def explain(command: str):
    """Explains a command in detail."""
    prompt = f"Explain this command as a Senior DevOps Engineer in Markdown: `{command}`"
    try:
        with console.status("[bold blue]Analyzing...[/]"):
            response = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama-3.1-8b-instant")
        explanation = Markdown(response.choices[0].message.content.strip())
        console.print(Panel(explanation, title="EXPLANATION", border_style="blue", padding=(1, 2)))
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
    table.add_column("Intent", style="green")
    table.add_column("Command", style="magenta")

    for item in items:
        table.add_row(item[0], item[1], item[2])
    console.print(table)

@app.command()
def clear():
    """Wipes the database."""
    if Confirm.ask("[bold red]Delete everything?[/]"):
        history_db.clear_all()
        console.print("[bold green]History cleared.[/bold green]")

if __name__ == "__main__":
    app()