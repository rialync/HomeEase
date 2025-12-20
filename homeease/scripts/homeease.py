import csv
import os
import shutil
import re
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box

console = Console()

# ---------------- PATH SETUP ----------------
SCRIPT_PATH = Path(__file__).resolve()
BASE_DIR = SCRIPT_PATH.parent.parent

DATA_FILE = BASE_DIR / "data" / "expenses.csv"
LOG_FILE = BASE_DIR / "logs" / "activity.log"
BACKUP_DIR = BASE_DIR / "backup"

DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- UTILITIES ----------------

def log_activity(message):
    with open(LOG_FILE, "a") as log:
        log.write(f"{datetime.now()} - {message}\n")

def validate_amount(input_amount):
    if re.match(r"^\d+,\d+$", input_amount.strip()):
        console.print("[red]❌ Use decimal point, not comma (e.g. 45.7)[/red]")
        return None

    clean = re.sub(r"[^\d.,]", "", input_amount)
    if clean.count(",") and not re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?$", clean):
        console.print("[red]❌ Invalid number format[/red]")
        return None

    try:
        value = float(clean.replace(",", ""))
        if value <= 0:
            console.print("[red]❌ Amount must be greater than zero[/red]")
            return None
        return value
    except ValueError:
        return None

def is_valid_category(cat):
    if not re.search(r"[A-Za-z]", cat):
        console.print("[red]Category must contain at least one letter[/red]")
        return False
    return True

# ---------------- UI ----------------

def make_header():
    return Panel(
        "[bold cyan]🏠 HOMEEASE EXPENSE TRACKER[/bold cyan]",
        border_style="bright_blue",
        box=box.DOUBLE,
        expand=True
    )

def display_table():
    table = Table(box=box.ROUNDED, header_style="bold magenta", expand=True)
    table.add_column("ID", justify="center", width=4)
    table.add_column("Date")
    table.add_column("Category", style="cyan")
    table.add_column("Description")
    table.add_column("Amount", justify="right", style="bold green")

    total = 0.0

    if not DATA_FILE.exists() or os.path.getsize(DATA_FILE) == 0:
        return Panel("[yellow]No records yet. Add an expense![/yellow]")

    with open(DATA_FILE) as f:
        for i, row in enumerate(csv.reader(f), start=1):
            if len(row) == 4:
                table.add_row(str(i), row[0], row[1], row[2], f"₱{row[3]}")
                total += float(row[3].replace(",", ""))

    table.add_section()
    table.add_row("", "", "", "[bold]TOTAL[/bold]", f"[bold yellow]₱{total:,.2f}[/bold yellow]")
    return table

# ---------------- CORE ----------------

def add_expense():
    console.print(Panel("[bold green]✙ ADD EXPENSE[/bold green]"))

    while True:
        category = Prompt.ask("Category")
        if category and is_valid_category(category):
            break

    description = Prompt.ask("Description")

    while True:
        amount = validate_amount(Prompt.ask("Amount"))
        if amount:
            break

    with open(DATA_FILE, "a", newline="") as f:
        csv.writer(f).writerow([
            datetime.now().strftime("%Y-%m-%d"),
            category,
            description,
            f"{amount:,.2f}"
        ])

    log_activity(f"Added expense {category} - {amount}")
    console.print("[bold green]✔ Expense added successfully![/bold green]")

def edit_expense():
    rows = list(csv.reader(open(DATA_FILE)))
    if not rows:
        return

    idx = int(Prompt.ask("ID to EDIT")) - 1
    if not (0 <= idx < len(rows)):
        console.print("[red]Invalid ID[/red]")
        return

    rows[idx][1] = Prompt.ask("New Category", default=rows[idx][1])
    rows[idx][2] = Prompt.ask("New Description", default=rows[idx][2])

    while True:
        amt = validate_amount(Prompt.ask("New Amount", default=rows[idx][3]))
        if amt:
            rows[idx][3] = f"{amt:,.2f}"
            break

    with open(DATA_FILE, "w", newline="") as f:
        csv.writer(f).writerows(rows)

    log_activity(f"Edited ID {idx+1}")
    console.print("[bold green]✔ Update successful![/bold green]")

def delete_expense():
    rows = list(csv.reader(open(DATA_FILE)))
    if not rows:
        return

    console.print(
        Panel(
            "[bold red]DELETE OPTIONS[/bold red]\n\n"
            "• Single ID → 3\n"
            "• Multiple IDs → 1,2,5\n"
            "• Delete ALL → ALL",
            border_style="red"
        )
    )

    choice = Prompt.ask("Enter delete option").strip().upper()

    if choice == "ALL":
        if Confirm.ask("[bold red]This will delete ALL data. Continue?[/bold red]"):
            open(DATA_FILE, "w").close()
            log_activity("Deleted ALL expenses")
            console.print("[bold green]✔ All data deleted[/bold green]")
        return

    try:
        ids = sorted({int(i.strip()) - 1 for i in choice.split(",")})
        valid_ids = [i for i in ids if 0 <= i < len(rows)]

        if not valid_ids:
            console.print("[red]No valid IDs provided[/red]")
            return

        if Confirm.ask(f"[red]Delete {len(valid_ids)} selected record(s)?[/red]"):
            for i in reversed(valid_ids):
                rows.pop(i)

            with open(DATA_FILE, "w", newline="") as f:
                csv.writer(f).writerows(rows)

            log_activity(f"Deleted IDs: {', '.join(str(i+1) for i in valid_ids)}")
            console.print("[bold green]✔ Selected expenses deleted[/bold green]")

    except ValueError:
        console.print("[red]Invalid input format[/red]")

def backup_data():
    name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    shutil.copy(DATA_FILE, BACKUP_DIR / name)
    log_activity("Backup created")
    console.print(f"[bold green]💾 Backup saved: {name}[/bold green]")

def recover_data():
    backups = sorted(BACKUP_DIR.glob("backup_*.csv"))
    if not backups:
        console.print("[red]No backups found[/red]")
        return

    table = Table(title="Available Backups")
    table.add_column("ID")
    table.add_column("Filename")

    for i, b in enumerate(backups, 1):
        table.add_row(str(i), b.name)

    console.print(table)
    idx = int(Prompt.ask("Select backup ID")) - 1

    console.print("[yellow]Overwrite or Append?[/yellow]")
    mode = Prompt.ask("Choose", choices=["overwrite", "append", "cancel"], default="cancel")

    if mode == "cancel":
        return

    if mode == "overwrite":
        shutil.copy(backups[idx], DATA_FILE)
    else:
        with open(backups[idx]) as src, open(DATA_FILE, "a", newline="") as dest:
            csv.writer(dest).writerows(csv.reader(src))

    log_activity(f"Recovered using {mode}")
    console.print("[bold green]✔ Recovery successful![/bold green]")

# ---------------- MAIN ----------------

def main():
    while True:
        console.clear()
        console.print(make_header())
        console.print(display_table())

        console.print("\n[bold]Menu[/bold]")
        console.print("[1] ✙ Add")
        console.print("[2] 🖊 Edit")
        console.print("[3] 🗑 Delete")
        console.print("[4] 💾 Backup")
        console.print("[5] ♻ Recover")
        console.print("[6] ✖ Exit")

        choice = Prompt.ask("Choose", choices=[str(i) for i in range(1, 7)])

        if choice == "1": add_expense()
        elif choice == "2": edit_expense()
        elif choice == "3": delete_expense()
        elif choice == "4": backup_data()
        elif choice == "5": recover_data()
        elif choice == "6":
            console.print("[italic]Goodbye! 👋[/italic]")
            break

        Prompt.ask("\nPress Enter to continue")

if __name__ == "__main__":
    main()
