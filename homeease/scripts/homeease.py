import csv
import os
import shutil
import re
from datetime import datetime
from pathlib import Path

# Import Rich components
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box

console = Console()

# --- DYNAMIC PATH HANDLING ---
SCRIPT_PATH = Path(__file__).resolve()
BASE_DIR = SCRIPT_PATH.parent.parent 

DATA_FILE = BASE_DIR / "data" / "expenses.csv"
LOG_FILE = BASE_DIR / "logs" / "activity.log"
BACKUP_DIR = BASE_DIR / "backup"

# Ensure directories exist
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ------------------ UTILITIES ------------------

def log_activity(message):
    with open(LOG_FILE, "a") as log:
        log.write(f"{datetime.now()} - {message}\n")

def validate_amount(input_amount):
    clean_amt = re.sub(r'[^\d.]', '', input_amount)
    try:
        val = float(clean_amt)
        return val if val > 0 else None
    except ValueError:
        return None

def is_valid_category(cat):
    """
    Checks if category contains at least one letter (a-z or A-Z).
    Allows special characters and numbers as long as a letter is present.
    """
    if not re.search(r'[a-zA-Z]', cat):
        console.print("[red]Category must contain at least one letter (e.g., 'Food' or 'Apt-101').[/red]")
        return False
    return True

# ------------------ UI COMPONENTS ------------------

def make_header():
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_row(
        Panel("[bold cyan]🏠 HOMEEASE EXPENSE TRACKER[/bold cyan]",   
              border_style="bright_blue", 
              box=box.DOUBLE)
    )
    return grid

def display_table():
    table = Table(box=box.ROUNDED, header_style="bold magenta", expand=True)
    table.add_column("ID", justify="center", style="dim", width=4)
    table.add_column("Date", justify="center")
    table.add_column("Category", justify="center", style="cyan")
    table.add_column("Description", justify="center")
    table.add_column("Amount", justify="right", style="bold green")

    total = 0.0
    if not DATA_FILE.exists() or os.path.getsize(DATA_FILE) == 0:
        return Panel("[yellow]No records found. Choose [1] to add an expense![/yellow]", border_style="dim")

    with open(DATA_FILE, "r") as file:
        reader = csv.reader(file)
        for i, row in enumerate(reader, start=1):
            if row:
                table.add_row(str(i), row[0], row[1], row[2], f"₱{row[3]}")
                total += float(row[3].replace(",", ""))
    
    table.add_section()
    table.add_row("", "", "", "[bold white]TOTAL[/bold white]", f"[bold yellow]₱{total:,.2f}[/bold yellow]")
    return table

# ------------------ CORE FEATURES ------------------

def add_expense():
    console.print(Panel("[bold green]✙ ADD EXPENSE[/bold green]", expand=False))
    
    while True:
        category = Prompt.ask("Category").strip()
        if category and is_valid_category(category):
            break
        elif not category:
            console.print("[red]Category cannot be empty.[/red]")

    while True:
        description = Prompt.ask("Description").strip()
        if description:
            break
        console.print("[red]Description cannot be empty.[/red]")
    
    while True:
        amt_str = Prompt.ask("Amount")
        amount = validate_amount(amt_str)
        if amount: break
        console.print("[red]Invalid amount. Try again.[/red]")

    date = datetime.now().strftime("%Y-%m-%d")
    with open(DATA_FILE, "a", newline="") as file:
        csv.writer(file).writerow([date, category, description, f"{amount:,.2f}"])
    
    log_activity(f"Added: {category} - {amount}")
    console.print("[bold green]✔ Expense added successfully![/bold green]")

def edit_expense():
    if not DATA_FILE.exists(): return
    rows = list(csv.reader(open(DATA_FILE, "r")))
    if not rows: return
    
    val = Prompt.ask("ID to [bold yellow]EDIT[/bold yellow]")
    try:
        idx = int(val) - 1
        if 0 <= idx < len(rows):
            console.print(f"[yellow]Editing entry: {rows[idx][2]} ({rows[idx][1]})[/yellow]")
            
            while True:
                new_cat = Prompt.ask("New Category", default=rows[idx][1]).strip()
                if new_cat and is_valid_category(new_cat):
                    break
                elif not new_cat:
                    console.print("[red]Category cannot be empty.[/red]")

            while True:
                new_desc = Prompt.ask("New Description", default=rows[idx][2]).strip()
                if new_desc:
                    break
                console.print("[red]Description cannot be empty.[/red]")

            new_amt_str = Prompt.ask("New Amount", default=rows[idx][3])
            new_amt = validate_amount(new_amt_str)
            
            if new_amt:
                rows[idx][1] = new_cat
                rows[idx][2] = new_desc
                rows[idx][3] = f"{new_amt:,.2f}"
                with open(DATA_FILE, "w", newline="") as file:
                    csv.writer(file).writerows(rows)
                log_activity(f"Edited ID {idx+1}")
                console.print("[bold green]✔ Update successful.[/bold green]")
            else:
                console.print("[red]Invalid amount. Edit cancelled.[/red]")
        else:
            console.print("[red]Invalid ID.[/red]")
    except ValueError:
        console.print("[red]Enter a numeric ID.[/red]")

def delete_expense():
    if not DATA_FILE.exists(): return
    rows = list(csv.reader(open(DATA_FILE, "r")))
    if not rows: return
    
    val = Prompt.ask("ID to [red]DELETE[/red]")
    try:
        idx = int(val) - 1
        if 0 <= idx < len(rows):
            if Confirm.ask(f"Delete '{rows[idx][1]}'?"):
                rows.pop(idx)
                with open(DATA_FILE, "w", newline="") as file:
                    csv.writer(file).writerows(rows)
                log_activity(f"Deleted ID {idx+1}")
                console.print("[green]Deleted.[/green]")
        else:
            console.print("[red]Invalid ID.[/red]")
    except ValueError:
        console.print("[red]Enter a number.[/red]")

def backup_data():
    fname = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    shutil.copy(DATA_FILE, BACKUP_DIR / fname)
    log_activity("Backup created")
    console.print(f"[bold green]💾 Backup saved to /backup/{fname}[/bold green]")

# ------------------ MAIN LOOP ------------------

def main():
    while True:
        console.clear()
        console.print(make_header())
        console.print(display_table())
        
        console.print("\n[bold]Menu:[/bold]")
        console.print("[1] ✙ Add")
        console.print("[2] 🖊  Edit")
        console.print("[3] 🗑 Delete")
        console.print("[4] ↺ Backup")
        console.print("[5] ✖ Exit")
        
        choice = Prompt.ask("\nChoice [bold cyan][1-5][/bold cyan]", choices=["1", "2", "3", "4", "5"], 
            show_choices=False)

        if choice == "1":
            add_expense()
            Prompt.ask("\nPress Enter to return")
        elif choice == "2":
            edit_expense()
            Prompt.ask("\nPress Enter to return")
        elif choice == "3":
            delete_expense()
            Prompt.ask("\nPress Enter to return")
        elif choice == "4":
            backup_data()
            Prompt.ask("\nPress Enter to return")
        elif choice == "5":
            console.print("[italic]Exiting... Goodbye![/italic]")
            break

if __name__ == "__main__":
    main()