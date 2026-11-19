"""
Grocery Budget Assistant
Python 3.10+
Run: python main.py
Optional charts: pip install matplotlib
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "grocery_data.json"
CSV_FILE = BASE_DIR / "grocery_data.csv"
REPORT_DIR = BASE_DIR / "reports"
FIELDS = ["id", "date", "item", "category", "quantity", "unit_price", "total_cost", "budget", "status"]

def money(value: float) -> str:
    return f"₹{value:,.2f}"

def load_records() -> list[dict]:
    """Load JSON records; recover safely if the file is missing or damaged."""
    if not DATA_FILE.exists():
        save_records([])
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Data file must contain a JSON list.")
        return [r for r in data if isinstance(r, dict) and all(k in r for k in FIELDS)]
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        print(f"\n[WARNING] Could not read saved data ({exc}). Starting with an empty list.")
        backup = DATA_FILE.with_suffix(".corrupt.json")
        try:
            DATA_FILE.replace(backup)
            print(f"Damaged file moved to: {backup.name}")
        except OSError:
            pass
        save_records([])
        return []

def save_records(records: list[dict]) -> None:
    DATA_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    with CSV_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

def prompt_text(label: str, allow_blank: bool = False) -> str:
    while True:
        value = input(label).strip()
        if value or allow_blank:
            return value
        print("Please enter a value; it cannot be blank.")

def prompt_number(label: str, minimum: float = 0.01, maximum: float = 1_000_000) -> float:
    while True:
        raw = input(label).strip()
        try:
            value = float(raw)
            if value != value or value in (float("inf"), float("-inf")):
                raise ValueError
            if not minimum <= value <= maximum:
                print(f"Enter a number from {minimum:g} to {maximum:g}.")
                continue
            return round(value, 2)
        except ValueError:
            print("Invalid number. Enter a valid numeric value (example: 45.50).")

def next_id(records: list[dict]) -> int:
    return max((int(r["id"]) for r in records), default=0) + 1

def add_record(records: list[dict]) -> None:
    print("\n--- Add grocery purchase ---")
    item = prompt_text("Item name: ")
    category = prompt_text("Category (Vegetables/Fruits/Dairy/Grains/Snacks/Other): ")
    quantity = prompt_number("Quantity: ")
    unit_price = prompt_number("Price per unit (₹): ")
    budget = prompt_number("Budget for this item (₹): ")
    total = round(quantity * unit_price, 2)
    status = "OVER BUDGET" if total > budget else "WITHIN BUDGET"
    record = {
        "id": next_id(records), "date": datetime.now().strftime("%Y-%m-%d"),
        "item": item, "category": category.title(), "quantity": quantity,
        "unit_price": unit_price, "total_cost": total, "budget": budget, "status": status
    }
    records.append(record)
    save_records(records)
    print(f"\nSaved: {item} | Total: {money(total)} | Budget: {money(budget)}")
    print("⚠️  OVER BUDGET" if status == "OVER BUDGET" else "✓ Within budget")

def print_table(records: list[dict]) -> None:
    if not records:
        print("\nNo matching records found.")
        return
    headers = ["ID", "Date", "Item", "Category", "Qty", "Unit price", "Total", "Budget", "Status"]
    widths = [4, 10, 18, 13, 7, 12, 12, 12, 14]
    print()
    print(" | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("-+-".join("-" * w for w in widths))
    for r in records:
        vals = [str(r["id"]), str(r["date"]), str(r["item"])[:18], str(r["category"])[:13],
                f'{float(r["quantity"]):g}', money(float(r["unit_price"])),
                money(float(r["total_cost"])), money(float(r["budget"])), str(r["status"])]
        print(" | ".join(v[:w].ljust(w) for v, w in zip(vals, widths)))

def search_records(records: list[dict]) -> None:
    print("\n--- Search records ---")
    term = prompt_text("Enter item keyword or category: ").casefold()
    matches = [r for r in records if term in str(r["item"]).casefold()
               or term in str(r["category"]).casefold()]
    print_table(matches)

def show_summary(records: list[dict]) -> None:
    if not records:
        print("\nNo data available yet. Add purchases to see analytics.")
        return
    spent = sum(float(r["total_cost"]) for r in records)
    budget = sum(float(r["budget"]) for r in records)
    overs = [r for r in records if r["status"] == "OVER BUDGET"]
    savings = budget - spent
    avg = spent / len(records)
    print("\n========== EXECUTIVE SUMMARY ==========")
    print(f"Purchase records : {len(records)}")
    print(f"Total spent      : {money(spent)}")
    print(f"Total budget     : {money(budget)}")
    print(f"Budget balance   : {money(savings)}")
    print(f"Average purchase : {money(avg)}")
    print(f"Over-budget items: {len(overs)}")
    print(f"Within budget    : {len(records) - len(overs)}")
    if savings < 0:
        print(f"⚠️  Overall overspending: {money(abs(savings))}")
    else:
        print(f"✓ Overall budget remaining: {money(savings)}")
    by_category = defaultdict(float)
    for r in records:
        by_category[r["category"]] += float(r["total_cost"])
    print("\nSpending by category:")
    for cat, total in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:<16} {money(total)}")

def make_chart(records: list[dict]) -> None:
    if not records:
        print("\nNo data available to plot.")
        return
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nMatplotlib is not installed. Run: pip install matplotlib")
        return
    REPORT_DIR.mkdir(exist_ok=True)
    categories = defaultdict(float)
    for r in records:
        categories[r["category"]] += float(r["total_cost"])
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(categories.keys(), categories.values())
    ax.set_title("Grocery Spending by Category")
    ax.set_ylabel("Amount spent (₹)")
    ax.set_xlabel("Category")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    path = REPORT_DIR / "spending_by_category.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"\nChart saved to: {path}")

def export_reports(records: list[dict]) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    spent = sum(float(r["total_cost"]) for r in records)
    budget = sum(float(r["budget"]) for r in records)
    over = sum(r["status"] == "OVER BUDGET" for r in records)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md = [
        "# Grocery Budget Assistant - Report", "",
        f"- Generated: {datetime.now():%Y-%m-%d %H:%M}",
        f"- Records: {len(records)}",
        f"- Total spent: {money(spent)}",
        f"- Total budget: {money(budget)}",
        f"- Budget balance: {money(budget-spent)}",
        f"- Over-budget records: {over}", "",
        "| Item | Category | Quantity | Total | Budget | Status |",
        "|---|---|---:|---:|---:|---|"
    ]
    for r in records:
        md.append(f'| {r["item"]} | {r["category"]} | {r["quantity"]} | {money(float(r["total_cost"]))} | {money(float(r["budget"]))} | {r["status"]} |')
    (REPORT_DIR / f"summary_{stamp}.md").write_text("\n".join(md), encoding="utf-8")
    (REPORT_DIR / f"audit_{stamp}.txt").write_text(
        f"GROCERY BUDGET ASSISTANT AUDIT\nGenerated: {datetime.now()}\nRecords: {len(records)}\nSpent: {money(spent)}\nBudget: {money(budget)}\nOver budget: {over}\n",
        encoding="utf-8")
    with (REPORT_DIR / f"records_{stamp}.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"\nReports exported to: {REPORT_DIR}")

def import_csv(records: list[dict]) -> None:
    path = Path(prompt_text("CSV file path to import: ")).expanduser()
    if not path.is_file():
        print("File not found.")
        return
    added, errors = 0, []
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            required = {"item", "category", "quantity", "unit_price", "budget"}
            if not required.issubset(set(reader.fieldnames or [])):
                print("CSV must contain columns: item, category, quantity, unit_price, budget")
                return
            for line, row in enumerate(reader, start=2):
                try:
                    item = row["item"].strip()
                    category = row["category"].strip().title()
                    qty, price, budget = (float(row[k]) for k in ("quantity", "unit_price", "budget"))
                    if not item or not category or min(qty, price, budget) <= 0:
                        raise ValueError("blank text or non-positive number")
                    total = round(qty * price, 2)
                    records.append({"id": next_id(records), "date": datetime.now().strftime("%Y-%m-%d"),
                                    "item": item, "category": category, "quantity": qty,
                                    "unit_price": price, "total_cost": total, "budget": budget,
                                    "status": "OVER BUDGET" if total > budget else "WITHIN BUDGET"})
                    added += 1
                except (ValueError, TypeError, KeyError) as exc:
                    errors.append(f"Row {line}: {exc}")
        save_records(records)
        print(f"Imported {added} row(s).")
        for error in errors:
            print("[ROW ERROR]", error)
    except OSError as exc:
        print(f"Could not import CSV: {exc}")

def seed_sample(records: list[dict]) -> None:
    if records:
        print("Sample data is only added when the database is empty.")
        return
    sample = [
        ("Rice","Grains",5,62,350),("Milk","Dairy",3,30,100),("Tomato","Vegetables",2,35,100),
        ("Apple","Fruits",1.5,160,250),("Bread","Bakery",2,40,100),("Eggs","Dairy",12,7,100),
        ("Onion","Vegetables",3,42,150),("Banana","Fruits",2,55,120),("Dal","Grains",2,135,300),
        ("Cooking Oil","Essentials",2,145,300),("Tea","Beverages",1,180,200),("Sugar","Essentials",2,48,100),
        ("Potato","Vegetables",4,30,150),("Curd","Dairy",2,35,80),("Biscuits","Snacks",5,20,80),
        ("Chicken","Meat",1,260,250),("Spinach","Vegetables",2,25,70),("Orange","Fruits",2,90,150),
        ("Wheat Flour","Grains",5,44,250),("Cheese","Dairy",1,125,150),("Soap","Household",3,38,100),
        ("Detergent","Household",1,210,180),("Coffee","Beverages",1,240,250),("Carrot","Vegetables",2,50,120),
        ("Grapes","Fruits",1,110,130),("Yogurt","Dairy",4,28,100),("Noodles","Snacks",6,18,120),
        ("Peanuts","Snacks",1,95,100),("Cucumber","Vegetables",2,32,80),("Ghee","Dairy",1,520,500),
        ("Lentils","Grains",2,115,250),("Mango","Fruits",2,85,180),("Salt","Essentials",2,22,60),
        ("Juice","Beverages",2,75,140),("Cabbage","Vegetables",1,40,60),("Butter","Dairy",1,58,70),
        ("Chips","Snacks",4,25,80),("Garlic","Vegetables",0.5,180,100),("Cereal","Grains",1,195,220),
        ("Dishwash","Household",1,95,100)
    ]
    for item, cat, qty, price, budget in sample:
        total = round(qty * price, 2)
        records.append({"id": next_id(records), "date": datetime.now().strftime("%Y-%m-%d"),
                        "item": item, "category": cat, "quantity": qty, "unit_price": price,
                        "total_cost": total, "budget": budget,
                        "status": "OVER BUDGET" if total > budget else "WITHIN BUDGET"})
    save_records(records)
    print(f"Added {len(sample)} realistic sample records.")

def menu() -> None:
    records = load_records()
    while True:
        print("\n" + "=" * 48)
        print("        🛒 GROCERY BUDGET ASSISTANT")
        print("=" * 48)
        print("1. Add grocery purchase")
        print("2. View all records")
        print("3. Search by item/category")
        print("4. Executive summary")
        print("5. Generate spending chart")
        print("6. Export reports (Markdown/TXT/CSV)")
        print("7. Import records from CSV")
        print("8. Add 40 sample records")
        print("9. Exit")
        choice = input("\nChoose an option (1-9): ").strip()
        if choice == "1": add_record(records)
        elif choice == "2": print_table(records)
        elif choice == "3": search_records(records)
        elif choice == "4": show_summary(records)
        elif choice == "5": make_chart(records)
        elif choice == "6": export_reports(records)
        elif choice == "7": import_csv(records)
        elif choice == "8": seed_sample(records)
        elif choice == "9":
            save_records(records)
            print("Your data is saved. Thank you!")
            break
        else: print("Invalid choice. Please select a number from 1 to 9.")

if __name__ == "__main__":
    menu()
