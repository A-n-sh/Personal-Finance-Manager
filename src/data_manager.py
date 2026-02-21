"""
data_manager.py - Data persistence and management module

Handles all storage and retrieval operations:
- Saving / loading JSON for persistence
- Exporting and importing CSV via pandas
- Calculating statistics with NumPy
- Managing the data structure for transactions and savings goals
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class DataManager:
    """
    Manages data persistence for the finance tracker.

    Handles all file I/O, keeping data in JSON format for the application
    and providing CSV export/import via pandas. Statistics are calculated
    using NumPy for explicit numerical array operations.
    """

    def __init__(self, data_file: str = "data/finance_data.json"):
        """
        Initialize DataManager with a default data file path.

        Args:
            data_file: Path to the main JSON data file.
        """
        self.data_file = data_file

        self.data = {
            "transactions": [],
            "savings_goals": [],
            "settings": {
                "currency": "USD",
                "date_format": "YYYY-MM-DD",
            },
        }

    # ------------------------------------------------------------------
    # JSON persistence
    # ------------------------------------------------------------------

    def load_data(self) -> bool:
        """
        Load data from the JSON file into memory.

        Returns:
            True if data was loaded from file, False if starting fresh.
        """
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    self.data = json.load(f)

                trans_count = len(self.data.get("transactions", []))
                print(f"✅ Loaded {trans_count} transactions")
                return True
            else:
                print("📁 No existing data file found. Starting fresh.")
                return False

        except json.JSONDecodeError as e:
            print(f"❌ Error reading data file: {e}")
            print("Starting with empty data.")
            return False

        except Exception as e:
            print(f"❌ Unexpected error loading data: {e}")
            return False

    def save_data(self, filename: Optional[str] = None) -> bool:
        """
        Save current in-memory data to a JSON file.

        Args:
            filename: Optional override path. Defaults to self.data_file.

        Returns:
            True if save succeeded, False otherwise.
        """
        try:
            save_file = filename or self.data_file
            dir_name = os.path.dirname(save_file)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            with open(save_file, "w") as f:
                json.dump(self.data, f, indent=2)

            return True

        except Exception as e:
            print(f"❌ Error saving data: {e}")
            return False

    # ------------------------------------------------------------------
    # Transaction accessors
    # ------------------------------------------------------------------

    def add_transaction(self, transaction: Dict):
        """
        Append a transaction to the in-memory list.

        Note: changes are not persisted until save_data() is called.

        Args:
            transaction: Dict with keys type, amount, category, description, date.
        """
        if "transactions" not in self.data:
            self.data["transactions"] = []

        self.data["transactions"].append(transaction)

    def get_all_transactions(self) -> List[Dict]:
        """
        Return all transactions as a list of dicts.

        Returns:
            List of transaction dicts, or an empty list.
        """
        return self.data.get("transactions", [])

    # ------------------------------------------------------------------
    # Savings goal accessors
    # ------------------------------------------------------------------

    def get_savings_goals(self) -> List[Dict]:
        """Return all savings goals."""
        return self.data.get("savings_goals", [])

    def add_savings_goal(self, name: str, target: float, current: float = 0):
        """
        Add a new savings goal.

        Args:
            name:    Descriptive name for the goal.
            target:  Dollar amount to reach.
            current: Amount already saved (default 0).
        """
        if "savings_goals" not in self.data:
            self.data["savings_goals"] = []

        goal = {
            "name": name,
            "target": target,
            "current": current,
            "created_date": datetime.now().strftime("%Y-%m-%d"),
        }
        self.data["savings_goals"].append(goal)

    # ------------------------------------------------------------------
    # CSV export / import  (pandas replaces csv module)
    # ------------------------------------------------------------------

    def export_to_csv(self, filename: str) -> bool:
        """
        Export all transactions to a CSV file using pandas.

        pandas handles quoting, encoding, and edge cases automatically,
        replacing the manual csv.DictWriter implementation.

        Args:
            filename: Output file path (e.g. 'exports/transactions.csv').

        Returns:
            True if export succeeded, False otherwise.
        """
        try:
            transactions = self.get_all_transactions()

            if not transactions:
                print("No transactions to export.")
                return False

            df = pd.DataFrame(transactions)

            # Keep only the canonical columns in a predictable order
            columns = ["date", "type", "category", "description", "amount"]
            df = df[[c for c in columns if c in df.columns]]

            dir_name = os.path.dirname(filename)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            df.to_csv(filename, index=False)
            print(f"✅ Exported {len(df)} transactions to {filename}")
            return True

        except Exception as e:
            print(f"❌ Error exporting to CSV: {e}")
            return False

    def import_from_csv(self, filename: str) -> bool:
        """
        Import transactions from a CSV file using pandas.

        pandas read_csv handles type coercion and malformed rows more
        robustly than a manual row-by-row try/except loop. Invalid amounts
        are coerced to NaN and dropped in a single vectorized pass.

        Args:
            filename: Path to the CSV file to import.

        Returns:
            True if at least one row was imported, False otherwise.
        """
        try:
            if not os.path.exists(filename):
                print(f"❌ File {filename} not found.")
                return False

            df = pd.read_csv(filename)

            # Coerce and filter invalid amounts in one vectorized step
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
            df = df.dropna(subset=["amount"])
            df = df[df["amount"] > 0]

            if df.empty:
                print("⚠️ No valid transactions found in CSV file.")
                return False

            # Normalise transaction type; default to 'expense' for unknown values
            df["type"] = df["type"].str.lower()
            df["type"] = df["type"].where(
                df["type"].isin(["income", "expense"]), other="expense"
            )

            df["timestamp"] = datetime.now().isoformat()

            for record in df.to_dict("records"):
                self.add_transaction(record)

            self.save_data()
            print(f"✅ Successfully imported {len(df)} transactions from {filename}")
            return True

        except Exception as e:
            print(f"❌ Error importing from CSV: {e}")
            return False

    # ------------------------------------------------------------------
    # Statistics  (NumPy for explicit array operations)
    # ------------------------------------------------------------------

    def get_statistics(self) -> Dict:
        """
        Calculate overall financial statistics using NumPy.

        Extracts raw NumPy arrays from the DataFrame with .values so that
        np.sum, np.max, np.mean, and np.std operate directly on arrays
        rather than through pandas aggregation methods. This also enables
        the spending standard deviation metric — a measure of consistency
        not present in the original implementation.

        Returns:
            Dict of aggregated statistics.
        """
        transactions = self.get_all_transactions()

        if not transactions:
            return {}

        df = pd.DataFrame(transactions)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

        # Extract raw NumPy arrays for explicit numerical computation
        income_amounts  = df.loc[df["type"] == "income",  "amount"].values
        expense_amounts = df.loc[df["type"] == "expense", "amount"].values
        all_amounts     = df["amount"].values

        stats = {
            "total_transactions": len(df),
            # np.sum / np.max / np.mean / np.std operate on arrays directly
            "total_income":    float(np.sum(income_amounts))  if len(income_amounts)  else 0.0,
            "total_expenses":  float(np.sum(expense_amounts)) if len(expense_amounts) else 0.0,
            "balance":         float(np.sum(income_amounts) - np.sum(expense_amounts)),
            "avg_transaction": float(np.mean(all_amounts))    if len(all_amounts)     else 0.0,
            # Standard deviation: measures spending consistency (new metric)
            "std_transaction": float(np.std(all_amounts))     if len(all_amounts)     else 0.0,
            "largest_income":  float(np.max(income_amounts))  if len(income_amounts)  else 0.0,
            "largest_expense": float(np.max(expense_amounts)) if len(expense_amounts) else 0.0,
        }

        # Date range — min/max on the date column
        if "date" in df.columns:
            dates = df["date"].dropna()
            stats["first_transaction"] = dates.min() if not dates.empty else None
            stats["last_transaction"]  = dates.max() if not dates.empty else None
        else:
            stats["first_transaction"] = None
            stats["last_transaction"]  = None

        return stats

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def clear_all_data(self):
        """Reset all transactions and goals, preserving settings."""
        settings = self.data.get(
            "settings", {"currency": "USD", "date_format": "YYYY-MM-DD"}
        )
        self.data = {
            "transactions": [],
            "savings_goals": [],
            "settings": settings,
        }
        print("⚠️ All data has been cleared.")

    def get_backup_filename(self) -> str:
        """Generate a timestamped backup filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"data/backup_finance_data_{timestamp}.json"

    def create_backup(self) -> bool:
        """
        Write a timestamped backup of current data.

        Returns:
            True if backup succeeded, False otherwise.
        """
        try:
            backup_file = self.get_backup_filename()
            if self.save_data(backup_file):
                print(f"✅ Backup created: {backup_file}")
                return True
            return False

        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False