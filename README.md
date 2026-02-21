# Personal Finance Tracker

A command-line personal finance application built in Python that lets you log transactions, categorize spending, track savings goals, and generate visual reports. The analytics layer is powered by pandas and NumPy, with charts rendered via matplotlib.

---

## Features

- Log income and expense transactions with category, description, and date
- View, edit, and delete transactions from an interactive CLI menu
- Monthly summaries showing income, expenses, net savings, and savings rate
- Category breakdown with inline ASCII bar chart
- Savings goals with progress tracking
- Visual reports: spending trends, category pie chart, monthly bar chart, goal progress bars
- Export transactions to CSV and import from CSV
- Automatic JSON persistence between sessions with backup support

---

## Tech Stack

| Library | Usage |
|---|---|
| Python 3.8+ | Core application, CLI, data models |
| pandas | DataFrame-based filtering, groupby aggregation, CSV I/O |
| NumPy | Vectorized balance calculation, statistics (`np.sum`, `np.max`, `np.std`) |
| matplotlib | Line charts, bar charts, pie charts, horizontal progress bars |

---

## Project Structure
```
personal-finance-tracker/
├── PFM.py                  # Entry point — main menu loop and CLI handlers
├── src/
│   ├── __init__.py
│   ├── transaction.py      # Transaction business logic (pandas + NumPy)
│   ├── data_manager.py     # JSON persistence, CSV import/export, statistics
│   └── visualizer.py       # All matplotlib chart generation
├── data/
│   └── finance_data.json   # Auto-created on first run
└── README.md
```

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/your-username/personal-finance-tracker.git
cd personal-finance-tracker
```

**2. Install dependencies**
```bash
pip install pandas numpy matplotlib
```

**3. Create the required directories**
```bash
mkdir -p data src
```

**4. Run the application**
```bash
python PFM.py
```

---

## Usage

On launch you will see the main menu:
```
==================================================
PERSONAL FINANCE MANAGER
==================================================
1.  Add Income Transaction
2.  Add Expense Transaction
3.  View All Transactions
4.  Edit Transaction
5.  Delete Transaction
6.  View Monthly Summary
7.  View Category Breakdown
8.  Show Spending Trends (Graph)
9.  Manage Savings Goals
10. Export Data
0.  Exit
```

### Adding a Transaction

Select `1` (income) or `2` (expense), then follow the prompts:
```
➕ Adding Expense Transaction
Amount: $85.50
Categories:
1. Food & Dining  2. Transportation  3. Entertainment ...
Select category (number): 1
Description: Weekly groceries
Date (YYYY-MM-DD) or press Enter for today:
✅ Expense transaction added successfully!
```

### Viewing Reports

Select `8` to open the spending trends graph. Three chart types are available through separate menu options — the trend line chart, category pie chart, and monthly comparison bar chart are all generated from the same underlying pandas aggregation.

### Managing Savings Goals

Select `9` to create a goal, update progress, or view the horizontal progress bar chart showing how close you are to each target.

### Exporting Data

Select `10` to export all transactions to a `.csv` file, which can be opened in Excel or Google Sheets.

---

## How pandas and NumPy Are Used

### pandas

All transaction data is loaded into a typed DataFrame through a central `_get_df()` helper in `TransactionManager`. This enforces numeric types on amounts and parses dates once, so every downstream method works with a clean DataFrame instead of raw JSON dicts.

Key operations:

- **`get_category_breakdown()`** — `groupby('category')['amount'].sum()` replaces a manual accumulation loop
- **`get_monthly_summary()`** — boolean indexing on `df['date'].dt.month` and `df['date'].dt.year` replaces a date-string parsing loop
- **`get_spending_by_month()`** — `dt.to_period('M')` + `groupby` + `unstack` builds a pivot of income vs. expenses by month
- **`search_transactions()`** — `.str.contains()` vectorized string matching replaces a `for` loop
- **`export_to_csv()` / `import_from_csv()`** — `df.to_csv()` and `pd.read_csv()` with `errors='coerce'` replace the `csv` standard library

In the `Visualizer`, a shared `_build_monthly_df()` helper consolidates the date-parsing and aggregation logic that previously existed in three separate methods, feeding a single clean DataFrame to all chart functions.

### NumPy

NumPy operates on raw `.values` arrays extracted from DataFrames for explicit numerical computation:

- **`get_balance()`** — `np.where` applies income/expense sign transformation in a single vectorized pass, then `np.sum` reduces it
- **`get_statistics()`** — `np.sum`, `np.max`, `np.mean`, and `np.std` on separated income/expense arrays
- **Spending std deviation** — `np.std(all_amounts)` surfaces spending consistency as a number — a low value means stable, predictable spending and a high value flags irregular patterns
- **`plot_savings_progress()`** — `np.clip` caps goal percentages at 100 in one vectorized step
- **`plot_spending_trends()`** — `np.arange` provides consistent x-axis positioning for chart annotations

---

## Data Storage

Transactions and savings goals are stored in `data/finance_data.json`. The file is created automatically on first run.
```json
{
  "transactions": [
    {
      "type": "expense",
      "amount": 85.50,
      "category": "Food & Dining",
      "description": "Weekly groceries",
      "date": "2025-03-14",
      "timestamp": "2025-03-14T10:23:45.123456"
    }
  ],
  "savings_goals": [],
  "settings": {
    "currency": "USD",
    "date_format": "YYYY-MM-DD"
  }
}
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'src'`**
Make sure you are running `python PFM.py` from the project root directory, not from inside `src/`.

**Matplotlib shows no window**
Add the following near the top of `visualizer.py`:
```python
import matplotlib
matplotlib.use('TkAgg')  # alternatives: 'Qt5Agg', 'MacOSX'
```

**`finance_data.json` not found**
The file is created automatically on first run. Make sure the `data/` directory exists:
```bash
mkdir -p data
```

---

## Author

Ansh Gupta — University of Florida, Computer Science
