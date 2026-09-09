"""
transaction.py - Transaction management module
Handles all transaction-related operations using pandas and NumPy
for vectorized data processing.
"""

from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class TransactionManager:
    """Manages financial transactions."""

    def __init__(self, data_manager):
        """Initialize TransactionManager with a DataManager instance."""
        self.data_manager = data_manager

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _get_df(self) -> pd.DataFrame:
        """
        Load all transactions through the shared typed DataFrame boundary.

        Returns:
            pd.DataFrame with columns: date, type, amount, category,
                                       description, timestamp
        """
        return self.data_manager.get_transactions_dataframe()

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def add_transaction(
        self,
        trans_type: str,
        amount: float,
        category: str,
        description: str,
        date: str,
    ) -> bool:
        """
        Add a new transaction.

        Args:
            trans_type:  'income' or 'expense'
            amount:      Transaction amount (must be > 0)
            category:    Transaction category
            description: Free-text description
            date:        Date string in YYYY-MM-DD format

        Returns:
            True if the transaction was added successfully, False otherwise.
        """
        try:
            transaction = {
                "type": trans_type,
                "amount": amount,
                "category": category,
                "description": description,
                "date": date,
                "timestamp": datetime.now().isoformat(),
            }
            self.data_manager.add_transaction(transaction)
            return True

        except Exception as e:
            print(f"Error adding transaction: {e}")
            return False

    def display_transactions(self, limit: Optional[int] = None):
        """
        Display all transactions in a formatted table, most recent first.

        Args:
            limit: Maximum number of rows to display. None = show all.
        """
        df = self._get_df()

        if df.empty:
            print("No transactions found.")
            return

        # Sort newest first, optionally truncate
        df = df.sort_values("date", ascending=False)
        if limit:
            df = df.head(limit)

        # Header
        print(
            f"{'ID':<4} {'Date':<12} {'Type':<8} {'Category':<18} "
            f"{'Description':<25} {'Amount':>10}"
        )
        print("-" * 90)

        for i, (_, row) in enumerate(df.iterrows(), 1):
            trans_type = row.get("type", "N/A")
            symbol = "+" if trans_type == "income" else "-"
            color = "\033[92m" if trans_type == "income" else "\033[91m"
            reset = "\033[0m"

            date_str = row["date"].strftime("%Y-%m-%d") if pd.notna(row["date"]) else "N/A"
            print(
                f"{i:<4} {date_str:<12} "
                f"{str(trans_type).title():<8} "
                f"{str(row.get('category', 'N/A'))[:18]:<18} "
                f"{str(row.get('description', 'N/A'))[:25]:<25} "
                f"{color}{symbol}${row.get('amount', 0):>9,.2f}{reset}"
            )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_transaction(self, transaction: Dict) -> bool:
        """
        Validate transaction data before persistence.

        Args:
            transaction: Transaction dictionary

        Returns:
            True if all fields are present and valid, False otherwise.
        """
        required_fields = ["type", "amount", "category", "description", "date"]

        for field in required_fields:
            if field not in transaction:
                print(f"Missing required field: {field}")
                return False

        if transaction["type"] not in ["income", "expense"]:
            print("Invalid transaction type. Must be 'income' or 'expense'.")
            return False

        try:
            amount = float(transaction["amount"])
            if amount <= 0:
                print("Amount must be greater than 0.")
                return False
        except (ValueError, TypeError):
            print("Invalid amount format.")
            return False

        try:
            datetime.strptime(transaction["date"], "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")
            return False

        return True

    # ------------------------------------------------------------------
    # Analytics  (all pandas / NumPy — no manual loops)
    # ------------------------------------------------------------------

    def get_balance(self) -> float:
        """
        Calculate current balance using a NumPy vectorized sign transform.

        Income rows are treated as positive, expense rows as negative.
        np.where applies this in a single pass over the amount array.

        Returns:
            Net balance as a float.
        """
        df = self._get_df()
        if df.empty:
            return 0.0

        # np.where: income → positive amount, expense → negative amount
        signed = np.where(df["type"] == "income", df["amount"], -df["amount"])
        return float(np.sum(signed))

    def get_monthly_summary(self, month: int, year: int) -> Dict:
        """
        Get income/expense summary for a specific month using pandas
        boolean indexing on parsed date columns.

        Args:
            month: Month number (1–12)
            year:  Four-digit year

        Returns:
            Dict with keys: income, expenses, net, count
        """
        df = self._get_df()

        if df.empty:
            return {"income": 0, "expenses": 0, "net": 0, "count": 0}

        # Boolean mask on the parsed datetime column — no string parsing in a loop
        mask = (df["date"].dt.month == month) & (df["date"].dt.year == year)
        filtered = df[mask]

        income   = filtered.loc[filtered["type"] == "income",  "amount"].sum()
        expenses = filtered.loc[filtered["type"] == "expense", "amount"].sum()

        return {
            "income":   float(income),
            "expenses": float(expenses),
            "net":      float(income - expenses),
            "count":    len(filtered),
        }

    def get_category_breakdown(self) -> Dict[str, float]:
        """
        Get total expenses grouped by category.

        Uses pandas groupby + sum, replacing an 8-line manual accumulation loop.

        Returns:
            Dict mapping category name → total expense amount.
        """
        df = self._get_df()
        if df.empty:
            return {}

        expenses = df[df["type"] == "expense"]

        if expenses.empty:
            return {}

        # groupby aggregation replaces the entire manual loop
        breakdown = expenses.groupby("category")["amount"].sum()
        return breakdown.to_dict()

    def get_spending_by_month(self) -> Dict[str, Dict[str, float]]:
        """
        Get income and expense totals grouped by calendar month.

        Uses dt.to_period('M') for clean month extraction, then groupby +
        unstack to pivot the data — no manual date string parsing.

        Returns:
            Dict mapping 'YYYY-MM' strings → {'income': float, 'expenses': float}
        """
        df = self._get_df()
        if df.empty:
            return {}

        df = df.dropna(subset=["date"])
        df["month_key"] = df["date"].dt.to_period("M").astype(str)

        # groupby on two columns, then unstack 'type' into columns
        grouped = (
            df.groupby(["month_key", "type"], observed=True)["amount"]
            .sum()
            .unstack(fill_value=0)
        )

        result = {}
        for month in grouped.index:
            result[month] = {
                "income":   float(grouped.loc[month].get("income",  0)),
                "expenses": float(grouped.loc[month].get("expense", 0)),
            }

        return result

    def search_transactions(self, keyword: str) -> List[Dict]:
        """
        Search transactions by keyword in description or category.

        Uses pandas vectorized string operations (.str.contains) instead of
        iterating and calling .lower() on each row manually.

        Args:
            keyword: Case-insensitive search string

        Returns:
            List of matching transaction dicts.
        """
        df = self._get_df()
        if df.empty:
            return []

        kw = keyword.lower()
        mask = (
            df["description"].str.lower().str.contains(kw, na=False)
            | df["category"].str.lower().str.contains(kw, na=False)
        )

        # Convert date back to string for JSON-serializable output
        result = df[mask].copy()
        result["date"] = result["date"].dt.strftime("%Y-%m-%d").where(
            result["date"].notna(), other="N/A"
        )
        return result.to_dict("records")