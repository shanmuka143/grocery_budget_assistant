# Grocery Budget Assistant

A beginner-friendly Python 3.10+ terminal project for tracking grocery purchases against item budgets.

## Features
- Menu-driven terminal interface and defensive input validation
- Automatic overspending detection
- Persistent JSON database and CSV mirror
- Search by item name or category
- Executive summary with category totals and average spending
- Matplotlib spending chart (optional dependency)
- Markdown, TXT audit, and CSV report exports
- CSV bulk import with row-by-row error messages
- 40 realistic sample records

## Run
```bash
python main.py
```
Optional chart support:
```bash
python -m pip install -r requirements.txt
```
Choose option **8** once to load sample data. Data is stored in `grocery_data.json` and `grocery_data.csv`. Reports and charts are saved in `reports/`.

## CSV import format
```csv
item,category,quantity,unit_price,budget
Rice,Grains,2,60,150
Milk,Dairy,3,30,100
```

## Demo flow
1. Run `python main.py`.
2. Choose `8` to load 40 sample records.
3. Choose `4` to show the executive summary.
4. Choose `3` and search for `Dairy`.
5. Choose `1` and enter a purchase that exceeds its budget.
6. Choose `5` to generate the chart (after installing Matplotlib).
7. Choose `6` to export reports.
8. Exit and restart; choose `2` to verify saved data.
