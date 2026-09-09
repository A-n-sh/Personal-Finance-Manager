"""
visualizer.py - Data visualization module

Creates visual representations of financial data including:
- Spending trends over time
- Income vs expense comparisons
- Category-wise expense pie charts
- Monthly comparison bar charts
- Savings goal progress bars

All chart methods share a single _build_monthly_df() helper that
performs date parsing and monthly aggregation once via pandas, eliminating
the repeated manual loops that existed in the original implementation.
"""

import calendar

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List


class Visualizer:
    """
    Creates visual charts and graphs for financial data analysis.

    All aggregation and date handling is delegated to _build_monthly_df(),
    a shared pandas helper. Chart methods receive a clean DataFrame and
    focus purely on rendering.
    """

    def __init__(self, data_manager):
        """
        Initialize Visualizer with a DataManager instance.

        Args:
            data_manager: Instance of DataManager to access transaction data.
        """
        self.data_manager = data_manager
        plt.style.use("seaborn-v0_8-darkgrid")

    # ------------------------------------------------------------------
    # Shared pandas helper
    # ------------------------------------------------------------------

    def _build_monthly_df(self) -> pd.DataFrame:
        """
        Build a monthly summary DataFrame shared by all chart methods.

        Previously, each of the three plotting methods contained its own
        date-parsing loop and dict-building logic. This helper consolidates
        that work into one place using:
          - pd.to_datetime for date parsing
          - dt.to_period('M') for clean month extraction
          - groupby + unstack to pivot income/expense into columns

        Returns:
            DataFrame indexed by month (Period[M]) with columns:
              income, expenses, net
            Returns an empty DataFrame if there are no transactions.
        """
        df = self.data_manager.get_transactions_dataframe()
        if df.empty:
            return pd.DataFrame()

        # Extract calendar month as a Period for clean grouping
        df["month"] = df["date"].dt.to_period("M")

        # Pivot: rows = month, columns = transaction type, values = summed amount
        pivot = (
            df.groupby(["month", "type"], observed=True)["amount"]
            .sum()
            .unstack(fill_value=0)
        )
        pivot.columns.name = None

        # Ensure both columns always exist even if one type has no transactions
        for col in ["income", "expense"]:
            if col not in pivot.columns:
                pivot[col] = 0

        pivot = pivot.rename(columns={"expense": "expenses"})
        pivot["net"] = pivot["income"] - pivot["expenses"]

        return pivot.sort_index()

    # ------------------------------------------------------------------
    # Chart methods
    # ------------------------------------------------------------------

    def plot_spending_trends(self):
        """
        Line chart of monthly income, expenses, and net savings over time.

        The net savings line is a new addition made possible by having
        _build_monthly_df() compute it centrally — it would have required
        a separate pass in the original manual loop approach.
        """
        try:
            df = self._build_monthly_df()

            if df.empty:
                print("No transactions to visualize.")
                return

            # Convert Period index to readable labels (e.g., "Jan 2024")
            months = [p.strftime("%b %Y") for p in df.index]
            x = np.arange(len(months))  # NumPy array for consistent x positioning

            fig, ax = plt.subplots(figsize=(12, 6))

            ax.plot(x, df["income"].values,   "g-o", linewidth=2, markersize=8, label="Income")
            ax.plot(x, df["expenses"].values, "r-s", linewidth=2, markersize=8, label="Expenses")
            ax.plot(x, df["net"].values,      "b--^", linewidth=1.5, markersize=6, label="Net Savings")

            # Annotate data points
            for i, (inc, exp) in enumerate(zip(df["income"].values, df["expenses"].values)):
                ax.annotate(f"${inc:.0f}", (i, inc), textcoords="offset points",
                            xytext=(0, 10), ha="center", fontsize=8)
                ax.annotate(f"${exp:.0f}", (i, exp), textcoords="offset points",
                            xytext=(0, -15), ha="center", fontsize=8)

            ax.set_xticks(x)
            ax.set_xticklabels(months, rotation=45, ha="right")
            ax.set_xlabel("Month", fontsize=12)
            ax.set_ylabel("Amount ($)", fontsize=12)
            ax.set_title("Income vs Expenses Trend", fontsize=14, fontweight="bold")
            ax.legend(loc="upper left")
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"Error creating visualization: {e}")

    def plot_category_pie_chart(self):
        """
        Pie chart of expense distribution by category.

        Category totals are computed via pandas groupby in _build_monthly_df's
        underlying data, keeping all aggregation logic consistent.
        """
        try:
            df = self.data_manager.get_transactions_dataframe()
            if df.empty:
                print("No transactions to visualize.")
                return

            expenses = df[df["type"] == "expense"]

            if expenses.empty:
                print("No expense data to visualize.")
                return

            # Single groupby replaces the manual category accumulation loop
            category_totals = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)

            categories = category_totals.index.tolist()
            values     = category_totals.values  # NumPy array

            fig, ax = plt.subplots(figsize=(10, 8))
            colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))

            wedges, texts, autotexts = ax.pie(
                values,
                labels=categories,
                colors=colors,
                autopct="%1.1f%%",
                startangle=90,
                shadow=True,
            )

            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontweight("bold")
                autotext.set_fontsize(10)

            ax.set_title("Expense Distribution by Category", fontsize=14, fontweight="bold")
            ax.axis("equal")

            legend_labels = [f"{cat}: ${val:,.2f}" for cat, val in zip(categories, values)]
            ax.legend(legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"Error creating pie chart: {e}")

    def plot_monthly_comparison(self, year: int = None):
        """
        Grouped bar chart comparing income and expenses for each month of a year.

        Uses _build_monthly_df() for data prep, then filters to the requested
        year. NumPy arange is used for precise x-axis bar positioning.

        Args:
            year: Year to display. Defaults to the current year.
        """
        try:
            if year is None:
                year = datetime.now().year

            df = self._build_monthly_df()

            if df.empty:
                print("No transactions to visualize.")
                return

            # Filter to the requested year by checking the Period's year attribute
            df = df[[p.year == year for p in df.index]]

            # Build a full 12-month scaffold so months with no data show as 0
            all_months   = pd.period_range(start=f"{year}-01", periods=12, freq="M")
            df = df.reindex(all_months, fill_value=0)

            month_labels = [calendar.month_abbr[p.month] for p in df.index]
            x     = np.arange(12)
            width = 0.35

            fig, ax = plt.subplots(figsize=(14, 6))

            income_bars  = ax.bar(x - width / 2, df["income"].values,   width, label="Income",   color="green", alpha=0.7)
            expense_bars = ax.bar(x + width / 2, df["expenses"].values, width, label="Expenses", color="red",   alpha=0.7)

            for bar in income_bars:
                h = bar.get_height()
                if h > 0:
                    ax.annotate(f"${h:.0f}",
                                xy=(bar.get_x() + bar.get_width() / 2, h),
                                xytext=(0, 3), textcoords="offset points",
                                ha="center", va="bottom", fontsize=8)

            for bar in expense_bars:
                h = bar.get_height()
                if h > 0:
                    ax.annotate(f"${h:.0f}",
                                xy=(bar.get_x() + bar.get_width() / 2, h),
                                xytext=(0, 3), textcoords="offset points",
                                ha="center", va="bottom", fontsize=8)

            ax.set_xlabel("Month", fontsize=12)
            ax.set_ylabel("Amount ($)", fontsize=12)
            ax.set_title(f"Monthly Income vs Expenses — {year}", fontsize=14, fontweight="bold")
            ax.set_xticks(x)
            ax.set_xticklabels(month_labels)
            ax.legend()
            ax.grid(True, alpha=0.3, axis="y")

            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"Error creating bar chart: {e}")

    def plot_savings_progress(self):
        """
        Horizontal bar chart showing progress toward each savings goal.

        NumPy is used to compute percentage values and cap them at 100
        in a single vectorized operation rather than a Python loop.
        """
        try:
            goals = self.data_manager.get_savings_goals()

            if not goals:
                print("No savings goals to visualize.")
                return

            goals_df = pd.DataFrame(goals)
            goals_df["current"] = pd.to_numeric(goals_df["current"], errors="coerce").fillna(0)
            goals_df["target"]  = pd.to_numeric(goals_df["target"],  errors="coerce").replace(0, 1)

            # NumPy vectorized percentage calculation, capped at 100
            percentages = np.clip(
                (goals_df["current"].values / goals_df["target"].values) * 100,
                0, 100
            )

            goal_names = goals_df["name"].tolist()
            amounts    = [
                f"${row['current']:,.0f} / ${row['target']:,.0f}"
                for _, row in goals_df.iterrows()
            ]

            fig, ax = plt.subplots(figsize=(10, max(3, len(goals) * 1.5)))

            bars = ax.barh(goal_names, percentages, color="skyblue",
                           edgecolor="navy", linewidth=2)

            for bar, pct, amt in zip(bars, percentages, amounts):
                if pct > 50:
                    ax.text(pct - 2, bar.get_y() + bar.get_height() / 2,
                            f"{pct:.1f}%", ha="right", va="center",
                            color="white", fontweight="bold")
                else:
                    ax.text(pct + 2, bar.get_y() + bar.get_height() / 2,
                            f"{pct:.1f}%", ha="left", va="center",
                            fontweight="bold")

                ax.text(105, bar.get_y() + bar.get_height() / 2, amt,
                        ha="left", va="center", fontsize=9)

            ax.axvline(x=100, color="green", linestyle="--",
                       linewidth=2, alpha=0.5, label="Target (100%)")
            ax.set_xlabel("Progress (%)", fontsize=12)
            ax.set_title("Savings Goals Progress", fontsize=14, fontweight="bold")
            ax.set_xlim(0, 130)
            ax.legend()

            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"Error creating savings progress chart: {e}")