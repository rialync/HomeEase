import csv
from datetime import datetime
import os
import shutil
import re

DATA_FILE = "../data/expenses.csv"
LOG_FILE = "../logs/activity.log"
BACKUP_DIR = "../backup"

# ------------------ UTILITIES ------------------

def log_activity(message):
    with open(LOG_FILE, "a") as log:
        log.write(f"{datetime.now()} - {message}\n")

def format_amount(amount):
    return f"{amount:,.2f}"

def validate_amount(input_amount):
    # Accepts: 5000 | 5,000 | 5000.00 | 5,000.00
    pattern = r"^\d{1,3}(,\d{3})*(\.\d{1,2})?$|^\d+(\.\d{1,2})?$"
    if not re.match(pattern, input_amount):
        return None
    try:
        value = float(input_amount.replace(",", ""))
        if value <= 0:
            return None
        return value
    except ValueError:
        return None

def validate_text(text, field_name):
    if not text.strip():
        print(f"{field_name} cannot be empty.")
        return None
    if len(text) > 50:
        print(f"{field_name} is too long (max 50 characters).")
        return None
    return text.strip()

# ------------------ CORE FEATURES ------------------

def add_expense():
    print("\nAdd Expense")
    print("-" * 30)

    category = validate_text(input("Category: "), "Category")
    if not category:
        return

    description = validate_text(input("Description: "), "Description")
    if not description:
        return

    amount_input = input("Amount (e.g. 5000 or 5,000): ")
    amount = validate_amount(amount_input)

    if amount is None:
        print("Invalid amount format.")
        print("Valid examples: 5000 | 5,000 | 5,000.00")
        print("Invalid examples: 5,0,0 | 5,00.00")
        return

    date = datetime.now().strftime("%Y-%m-%d")

    with open(DATA_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([date, category, description, format_amount(amount)])

    log_activity("Expense added")
    print("Expense successfully added.")

def view_expenses():
    print("\nExpense Records")
    print("-" * 60)

    if not os.path.exists(DATA_FILE):
        print("No records found.")
        return

    with open(DATA_FILE, "r") as file:
        reader = csv.reader(file)
        for i, row in enumerate(reader, start=1):
            print(f"{i}. {row[0]} | {row[1]} | {row[2]} | {row[3]}")

def load_expenses():
    with open(DATA_FILE, "r") as file:
        return list(csv.reader(file))

def save_expenses(rows):
    with open(DATA_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

def edit_expense():
    expenses = load_expenses()
    view_expenses()

    try:
        index = int(input("Enter expense number to edit: ")) - 1
        if index < 0 or index >= len(expenses):
            raise ValueError
    except ValueError:
        print("Invalid selection.")
        return

    category = validate_text(input("New Category: "), "Category")
    if not category:
        return

    description = validate_text(input("New Description: "), "Description")
    if not description:
        return

    amount_input = input("New Amount: ")
    amount = validate_amount(amount_input)
    if amount is None:
        print("Invalid amount format.")
        return

    expenses[index][1] = category
    expenses[index][2] = description
    expenses[index][3] = format_amount(amount)

    save_expenses(expenses)
    log_activity("Expense edited")
    print("Expense updated successfully.")

def delete_expense():
    expenses = load_expenses()
    view_expenses()

    try:
        index = int(input("Enter expense number to delete: ")) - 1
        if index < 0 or index >= len(expenses):
            raise ValueError
    except ValueError:
        print("Invalid selection.")
        return

    confirm = input("Confirm delete? (y/n): ").lower()
    if confirm == "y":
        expenses.pop(index)
        save_expenses(expenses)
        log_activity("Expense deleted")
        print("Expense deleted.")

def backup_data():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_name = f"expenses_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    shutil.copy(DATA_FILE, f"{BACKUP_DIR}/{backup_name}")
    log_activity("Backup created")
    print("Backup completed successfully.")

# ------------------ UI ------------------

def show_menu():
    print("\n" + "=" * 50)
    print("        HomeEase Expense Tracker")
    print("=" * 50)
    print("1. Add Expense")
    print("2. View Expenses")
    print("3. Edit Expense")
    print("4. Delete Expense")
    print("5. Backup Data")
    print("6. Exit")
    print("=" * 50)

def main():
    while True:
        show_menu()
        choice = input("Select option (1-6): ")

        if choice == "1":
            add_expense()
        elif choice == "2":
            view_expenses()
        elif choice == "3":
            edit_expense()
        elif choice == "4":
            delete_expense()
        elif choice == "5":
            backup_data()
        elif choice == "6":
            log_activity("System exited")
            print("Goodbye.")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
