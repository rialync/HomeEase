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
from datetime import datetime, timedelta

console = Console()

# ---------------- PATH SETUP ----------------
SCRIPT_PATH = Path(__file__).resolve()
BASE_DIR = SCRIPT_PATH.parent.parent

DATA_FILE = BASE_DIR / "data" / "expenses.csv"
LOG_FILE = BASE_DIR / "logs" / "activity.log"
BACKUP_DIR = BASE_DIR / "backup"
CATEGORY_FILE = BASE_DIR / "data" / "categories.csv"

DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
CATEGORY_FILE.parent.mkdir(parents=True, exist_ok=True)

# ---------------- INITIALIZE CATEGORY FILE ----------------
if not CATEGORY_FILE.exists():
    with open(CATEGORY_FILE, "w", newline="") as f:
        for cat in ["Food", "Transport", "Travel", "Utilities", "Entertainment", "Shopping", "Medical", "Other"]:
            f.write(f"{cat}\n")

def load_categories():
    with open(CATEGORY_FILE) as f:
        return [line.strip() for line in f if line.strip()]

def save_category(new_cat):
    with open(CATEGORY_FILE, "a", newline="") as f:
        f.write(f"{new_cat}\n")

# ---------------- UTILITIES ----------------
def log_activity(message):
    # Manually add 8 hours to the UTC time to match Philippine Time (PHT)
    pht_time = datetime.now() + timedelta(hours=8)
    timestamp = pht_time.strftime("%Y-%m-%d %I:%M:%S %p")
    
    with open(LOG_FILE, "a") as log:
        log.write(f"[{timestamp}] - {message}\n")

def validate_amount(input_amount):
    # 1. Check for negative sign immediately
    if input_amount.strip().startswith("-"):
        console.print("[red]❌ Amount cannot be negative![/red]")
        return None

    # 2. Check for comma typo
    if re.match(r"^\d+,\d+$", input_amount.strip()):
        console.print("[red]❌ Use decimal point, not comma (e.g. 45.7)[/red]")
        return None

    # 3. Clean the input (remove currency symbols or spaces)
    clean = re.sub(r"[^\d.,]", "", input_amount)
    
    # 4. Handle thousands separators vs decimals
    if clean.count(",") and not re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?$", clean):
        console.print("[red]❌ Invalid number format[/red]")
        return None

    try:
        value = float(clean.replace(",", ""))
        # 5. Strict zero and negative check
        if value <= 0:
            console.print("[red]❌ Amount must be greater than zero[/red]")
            return None
        return value
    except ValueError:
        console.print("[red]❌ Please enter a valid number[/red]")
        return None

def is_valid_category(cat):
    if not re.search(r"[A-Za-z]", cat):
        console.print("[red]Category must contain at least one letter[/red]")
        return False
    return True

# ---------------- UI ----------------

def make_header():
    return Panel(
        "[bold cyan]                                         🏠 HOMEEASE EXPENSE TRACKER[/bold cyan]",
        border_style="bright_blue",
        box=box.DOUBLE,
        expand=True
    )

def display_table():
    table = Table(box=box.ROUNDED, header_style="bold magenta", expand=True, show_lines=True)
    table.add_column("ID", justify="center")
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

# ---------------- CATEGORY TABLE ----------------
def display_categories_table(categories):
    table = Table(
        title="Select Category", 
        box=box.ROUNDED, 
        expand=False, 
        show_lines=True
    )
    table.add_column("No.", justify="center", style="cyan")
    table.add_column("Category", style="magenta")

    for i, cat in enumerate(categories, 1):
        table.add_row(str(i), cat)
    
    table.add_row(str(len(categories)+1), "Other / Add New Category")
    
    console.print(table)
# ---------------- CORE ----------------

def add_expense():
    console.print(Panel("[bold green]✙ ADD EXPENSE[/bold green]"))

    categories = load_categories()
    
    while True:
        display_categories_table(categories)
        choice = Prompt.ask("Enter number").strip()
        
        if not choice.isdigit():
            console.print("[red]Enter a valid number[/red]")
            continue
        
        choice = int(choice)
        
        if 1 <= choice <= len(categories):
            category = categories[choice-1]
            break
        elif choice == len(categories)+1:
            while True:
                new_cat = Prompt.ask("Enter new category name").strip()
                if is_valid_category(new_cat):
                    category = new_cat
                    save_category(new_cat)
                    console.print(f"[green]✔ New category '{new_cat}' added[/green]")
                    break
            break
        else:
            console.print("[red]Invalid choice[/red]")
    # Ensure description is not empty
    while True:
        description = Prompt.ask("Description").strip()
        if description:
            break
        console.print("[red]❌ Description cannot be empty![/red]")

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
    # Guard: Check if file exists and has data
    if not DATA_FILE.exists() or os.path.getsize(DATA_FILE) == 0:
        console.print("[yellow]⚠ No records found to edit. Add an expense first![/yellow]")
        return
    # Load rows from the data file
    rows = list(csv.reader(open(DATA_FILE)))
    if not rows:
        return

    # Prompt for ID to edit
    choice_id = Prompt.ask("ID to EDIT").strip()
    if not choice_id.isdigit():
        console.print("[red]Invalid ID[/red]")
        return
        
    idx = int(choice_id) - 1
    if not (0 <= idx < len(rows)):
        console.print("[red]Invalid ID[/red]")
        return

    # --- CATEGORY SELECTION WITH DYNAMIC DEFAULT ---
    categories = load_categories()
    current_cat = rows[idx][1]
    
    # Determine the default number based on existing data
    try:
        # If the category exists in our list, find its number (index + 1)
        current_cat_idx = str(categories.index(current_cat) + 1)
    except ValueError:
        # If the category is custom/not in list, default to "Other / Add New"
        current_cat_idx = str(len(categories) + 1)

    while True:
        display_categories_table(categories)
        # We set the default to the number corresponding to the current category
        choice = Prompt.ask("Enter number", default=current_cat_idx).strip()
        
        if not choice.isdigit():
            console.print("[red]Enter a valid number[/red]")
            continue
            
        choice = int(choice)
        if 1 <= choice <= len(categories):
            rows[idx][1] = categories[choice-1]
            break
        elif choice == len(categories)+1:
            while True:
                # Suggest the current category name as the default text for the new entry
                new_cat = Prompt.ask("Enter new category name", default=current_cat).strip()
                if is_valid_category(new_cat):
                    rows[idx][1] = new_cat
                    # Save to categories list if it's truly a new unique category
                    if new_cat not in categories:
                        save_category(new_cat)
                        console.print(f"[green]✔ New category '{new_cat}' added to list[/green]")
                    break
            break
        else:
            console.print("[red]Invalid choice[/red]")

    # Edit Description
    rows[idx][2] = Prompt.ask("New Description", default=rows[idx][2])

    # Edit Amount
    while True:
        amt_input = Prompt.ask("New Amount", default=rows[idx][3])
        amt = validate_amount(amt_input)
        if amt:
            rows[idx][3] = f"{amt:,.2f}"
            break

    # Save all changes back to the CSV
    with open(DATA_FILE, "w", newline="") as f:
        csv.writer(f).writerows(rows)

    log_activity(f"Edited ID {idx+1}")
    console.print("[bold green]✔ Update successful![/bold green]")

def delete_expense():
    # Guard: Check if file exists and has data
    if not DATA_FILE.exists() or os.path.getsize(DATA_FILE) == 0:
        console.print("[yellow]⚠ No records found to delete![/yellow]")
        return
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
    # Guard: Check if file exists and has data
    if not DATA_FILE.exists() or os.path.getsize(DATA_FILE) == 0:
        console.print("[red]❌ Cannot create backup: There are no records to save.[/red]")
        return
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
    table.add_column("ID", justify="center")
    table.add_column("Filename")

    for i, b in enumerate(backups, 1):
        table.add_row(str(i), b.name)

    console.print(table)
    
    choice = Prompt.ask("Select backup ID").strip()
    
    if not choice.isdigit():
        console.print("[red]❌ Invalid input. Please enter a numeric ID.[/red]")
        return

    idx = int(choice) - 1

    # Validate if the ID exists in our backups list
    if not (0 <= idx < len(backups)):
        console.print(f"[red]❌ Error: Backup ID {choice} does not exist.[/red]")
        return

    console.print("\n[yellow]Overwrite or Append?[/yellow]")
    mode = Prompt.ask("Choose", choices=["overwrite", "append", "cancel"], default="cancel")

    if mode == "cancel":
        console.print("[blue]Recovery cancelled.[/blue]")
        return

    if mode == "overwrite":
        shutil.copy(backups[idx], DATA_FILE)
    else:
        with open(backups[idx], "r") as src, open(DATA_FILE, "a", newline="") as dest:
            reader = csv.reader(src)
            writer = csv.writer(dest)
            writer.writerows(reader)

    log_activity(f"Recovered from {backups[idx].name} using {mode}")
    console.print(f"[bold green]✔ Recovery successful via {mode}![/bold green]")
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
