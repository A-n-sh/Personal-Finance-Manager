"""
Personal Finance Manager
A command-line application for tracking income, expenses, and savings goals.
"""

import os
import sys
from datetime import datetime
from src.transaction import TransactionManager
from src.data_manager import DataManager
from src.visualizer import Visualizer


class FinanceManager:
    """Main application class for the Personal Finance Manager."""
    
    def __init__(self):
        """Initialize the Finance Manager application."""
        self.data_manager = DataManager()
        self.transaction_manager = TransactionManager(self.data_manager)
        self.visualizer = Visualizer(self.data_manager)
        self.running = True
        
        # Load existing data on startup
        self.data_manager.load_data()
        
        
    def display_menu(self):
        """Display the main menu."""
        print("\n" + "="*50)
        print("PERSONAL FINANCE MANAGER")
        print("="*50)
        print("1. Add Income Transaction")
        print("2. Add Expense Transaction")
        print("3. View All Transactions")
        print("4. Edit Transaction")
        print("5. Delete Transaction")
        print("6. View Monthly Summary")
        print("7. View Category Breakdown")
        print("8. Show Spending Trends (Graph)")
        print("9. Manage Savings Goals")
        print("10. Export Data")
        print("0. Exit")
        print("-"*50)
        

    def get_user_choice(self):
        """Get and validate user menu choice."""
        try:
            choice = input("Enter your choice (0-10): ").strip()
            if choice.isdigit() and 0 <= int(choice) <= 10:
                return int(choice)
            else:
                print("❌ Invalid choice. Please enter a number between 0 and 10.")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
            

    def run(self):
        """Run the main application loop."""
        print("\nWelcome to Personal Finance Manager!")
        print("Loading your financial data...")
        
        while self.running:
            self.display_menu()
            choice = self.get_user_choice()
            
            if choice is None:
                continue
                
            if choice == 0:
                self.exit_app()
            elif choice == 1:
                self.add_transaction('income')
            elif choice == 2:
                self.add_transaction('expense')
            elif choice == 3:
                self.view_transactions()
            elif choice == 4:
                self.edit_transaction()
            elif choice == 5:
                self.delete_transaction()
            elif choice == 6:
                self.view_monthly_summary()
            elif choice == 7:
                self.view_category_breakdown()
            elif choice == 8:
                self.show_spending_trends()
            elif choice == 9:
                self.manage_savings_goals()
            elif choice == 10:
                self.export_data()


    def add_transaction(self, trans_type):
        """Add a new transaction."""
        print(f"\n➕ Adding {trans_type.title()} Transaction")
        print("-"*40)
        
        try:
            # Get transaction details
            amount = self.get_amount()
            if amount is None:
                return
                
            category = self.get_category(trans_type)
            description = input("Description: ").strip()
            
            # Get date (default to today)
            date_str = input("Date (YYYY-MM-DD) or press Enter for today: ").strip()
            if date_str == "":
                date = datetime.now().strftime("%Y-%m-%d")
            else:
                date = self.validate_date(date_str)
                if date is None:
                    return
                    
            # Add transaction
            success = self.transaction_manager.add_transaction(
                trans_type, amount, category, description, date
            )
            
            if success:
                print(f"✅ {trans_type.title()} transaction added successfully!")
                self.data_manager.save_data()
            else:
                print("❌ Failed to add transaction.")
                
        except Exception as e:
            print(f"❌ Error adding transaction: {e}")
            

    def get_amount(self):
        """Get and validate transaction amount."""
        try:
            amount_str = input("Amount: $").strip()
            amount = float(amount_str)
            if amount <= 0:
                print("❌ Amount must be greater than 0.")
                return None
            return amount
        except ValueError:
            print("❌ Invalid amount. Please enter a number.")
            return None
            
            
    def get_category(self, trans_type):
        """Get transaction category."""
        if trans_type == 'expense':
            categories = [
                "Food & Dining", "Transportation", "Entertainment",
                "Shopping", "Bills & Utilities", "Healthcare",
                "Education", "Travel", "Other"
            ]
        else:
            categories = [
                "Salary", "Freelance", "Investment", "Gift",
                "Refund", "Other"
            ]
            
        print("\nCategories:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
            
        try:
            choice = int(input("Select category (number): ").strip())
            if 1 <= choice <= len(categories):
                return categories[choice - 1]
            else:
                print("Invalid choice. Using 'Other'.")
                return "Other"
        except ValueError:
            print("Invalid input. Using 'Other'.")
            return "Other"


    def validate_date(self, date_str):
        """Validate date format."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD.")
            return None


    def view_transactions(self):
        """View all transactions."""
        print("\n📊 All Transactions")
        print("-"*80)
        self.transaction_manager.display_transactions()
        input("\nPress Enter to continue...")
        

    def edit_transaction(self):
        """Edit an existing transaction."""
        print("\n✏️ Edit Transaction")
        print("-"*40)
        
        # Display transactions with IDs
        transactions = self.data_manager.get_all_transactions()
        if not transactions:
            print("No transactions to edit.")
            return
            
        self.transaction_manager.display_transactions()
        
        try:
            trans_id = int(input("\nEnter transaction ID to edit: ").strip())
            
            # Find transaction
            if 0 < trans_id <= len(transactions):
                trans = transactions[trans_id - 1]
                print(f"\nEditing: {trans['description']} - ${trans['amount']:.2f}")
                
                # Get new values (or keep old)
                print("(Press Enter to keep current value)")
                
                new_amount = input(f"New amount (${trans['amount']:.2f}): ").strip()
                if new_amount:
                    trans['amount'] = float(new_amount)
                    
                new_desc = input(f"New description ({trans['description']}): ").strip()
                if new_desc:
                    trans['description'] = new_desc
                    
                new_cat = input(f"New category ({trans['category']}): ").strip()
                if new_cat:
                    trans['category'] = new_cat
                    
                self.data_manager.save_data()
                print("✅ Transaction updated successfully!")
            else:
                print("❌ Invalid transaction ID.")
                
        except (ValueError, IndexError) as e:
            print(f"❌ Error: {e}")


    def delete_transaction(self):
        """Delete a transaction."""
        print("\n🗑️ Delete Transaction")
        print("-"*40)
        
        transactions = self.data_manager.get_all_transactions()
        if not transactions:
            print("No transactions to delete.")
            return
            
        self.transaction_manager.display_transactions()
        
        try:
            trans_id = int(input("\nEnter transaction ID to delete: ").strip())
            
            if 0 < trans_id <= len(transactions):
                trans = transactions[trans_id - 1]
                confirm = input(f"Delete '{trans['description']}' - ${trans['amount']:.2f}? (y/n): ")
                
                if confirm.lower() == 'y':
                    transactions.pop(trans_id - 1)
                    self.data_manager.save_data()
                    print("✅ Transaction deleted successfully!")
                else:
                    print("Deletion cancelled.")
            else:
                print("❌ Invalid transaction ID.")
                
        except (ValueError, IndexError) as e:
            print(f"❌ Error: {e}")
            

    def view_monthly_summary(self):
        """View monthly spending summary."""
        print("\n📅 Monthly Summary")
        print("-"*40)
        
        try:
            month = input("Enter month (1-12) or press Enter for current: ").strip()
            year = input("Enter year or press Enter for current: ").strip()
            
            if month == "":
                month = datetime.now().month
            else:
                month = int(month)
                
            if year == "":
                year = datetime.now().year
            else:
                year = int(year)
                
            summary = self.transaction_manager.get_monthly_summary(month, year)
            
            print(f"\n📊 Summary for {month}/{year}")
            print("-"*40)
            print(f"Total Income:    ${summary['income']:,.2f}")
            print(f"Total Expenses:  ${summary['expenses']:,.2f}")
            print(f"Net Savings:     ${summary['net']:,.2f}")
            print(f"Transactions:    {summary['count']}")
            
            if summary['expenses'] > 0:
                savings_rate = (summary['net'] / summary['income'] * 100) if summary['income'] > 0 else 0
                print(f"Savings Rate:    {savings_rate:.1f}%")
                
        except ValueError as e:
            print(f"❌ Invalid input: {e}")
            
        input("\nPress Enter to continue...")
        

    def view_category_breakdown(self):
        """View expense breakdown by category."""
        print("\n🏷️ Category Breakdown")
        print("-"*40)
        
        breakdown = self.transaction_manager.get_category_breakdown()
        
        if not breakdown:
            print("No expenses to analyze.")
        else:
            total = sum(breakdown.values())
            print(f"\nTotal Expenses: ${total:,.2f}\n")
            
            # Sort by amount
            sorted_cats = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
            
            for category, amount in sorted_cats:
                percentage = (amount / total) * 100
                bar = "█" * int(percentage / 2)
                print(f"{category:20} ${amount:8,.2f} ({percentage:5.1f}%) {bar}")
                
        input("\nPress Enter to continue...")
        

    def show_spending_trends(self):
        """Display spending trends visualization."""
        print("\n📈 Generating Spending Trends Graph...")
        self.visualizer.plot_spending_trends()
        

    def manage_savings_goals(self):
        """Manage savings goals."""
        print("\n💰 Savings Goals")
        print("-"*40)
        
        goals = self.data_manager.get_savings_goals()
        
        print("1. View Goals")
        print("2. Add New Goal")
        print("3. Update Goal Progress")
        print("4. Delete Goal")
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            self.view_savings_goals(goals)
        elif choice == "2":
            self.add_savings_goal()
        elif choice == "3":
            self.update_goal_progress(goals)
        elif choice == "4":
            self.delete_goal(goals)
            

    def view_savings_goals(self, goals):
        """View all savings goals."""
        if not goals:
            print("\nNo savings goals set.")
        else:
            print("\n" + "="*50)
            for i, goal in enumerate(goals, 1):
                progress = (goal['current'] / goal['target']) * 100
                bar = "█" * int(progress / 5)
                spaces = "░" * (20 - int(progress / 5))
                
                print(f"\n{i}. {goal['name']}")
                print(f"   Target: ${goal['target']:,.2f}")
                print(f"   Current: ${goal['current']:,.2f}")
                print(f"   Progress: [{bar}{spaces}] {progress:.1f}%")
                
        input("\nPress Enter to continue...")
        

    def add_savings_goal(self):
        """Add a new savings goal."""
        name = input("Goal name: ").strip()
        try:
            target = float(input("Target amount: $").strip())
            current = float(input("Current amount saved: $").strip())
            
            self.data_manager.add_savings_goal(name, target, current)
            print("✅ Savings goal added!")
            self.data_manager.save_data()
        except ValueError:
            print("❌ Invalid amount.")
            

    def update_goal_progress(self, goals):
        """Update savings goal progress."""
        if not goals:
            print("No goals to update.")
            return
            
        self.view_savings_goals(goals)
        try:
            goal_id = int(input("\nGoal number to update: ").strip()) - 1
            if 0 <= goal_id < len(goals):
                new_amount = float(input("New current amount: $").strip())
                goals[goal_id]['current'] = new_amount
                self.data_manager.save_data()
                print("✅ Goal updated!")
            else:
                print("❌ Invalid goal number.")
        except (ValueError, IndexError):
            print("❌ Invalid input.")


    def delete_goal(self, goals):
        """Delete a savings goal."""
        if not goals:
            print("No goals to delete.")
            return
            
        self.view_savings_goals(goals)
        try:
            goal_id = int(input("\nGoal number to delete: ").strip()) - 1
            if 0 <= goal_id < len(goals):
                confirm = input(f"Delete '{goals[goal_id]['name']}'? (y/n): ")
                if confirm.lower() == 'y':
                    goals.pop(goal_id)
                    self.data_manager.save_data()
                    print("✅ Goal deleted!")
            else:
                print("❌ Invalid goal number.")
        except (ValueError, IndexError):
            print("❌ Invalid input.")


    def export_data(self):
        """Export data to different formats."""
        print("\n💾 Export Data")
        print("-"*40)
        print("1. Export to CSV")
        print("2. Export to JSON")
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            filename = input("Filename (without extension): ").strip()
            if filename:
                self.data_manager.export_to_csv(f"{filename}.csv")
                print(f"✅ Data exported to {filename}.csv")
        elif choice == "2":
            filename = input("Filename (without extension): ").strip()
            if filename:
                self.data_manager.save_data(f"{filename}.json")
                print(f"✅ Data exported to {filename}.json")


    def exit_app(self):
        """Exit the application."""
        print("\n💾 Saving data...")
        self.data_manager.save_data()
        print("Thank you for using Personal Finance Manager!")
        print("👋Goodbye!")
        self.running = False


if __name__ == "__main__":
    # Create data directory if it doesn't exist
    if not os.path.exists("data"):
        os.makedirs("data")
        
    # Run the application
    app = FinanceManager()
    app.run()