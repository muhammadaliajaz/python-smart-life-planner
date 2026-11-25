import sys
import os
from datetime import datetime
from typing import Optional

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.data_manager import DataManager
from utils.validators import (
    validate_positive_number,
    validate_integer_range,
    validate_trip_duration,
    validate_travel_category,
    validate_destination_type,
    validate_email,
    validate_non_empty_string,
    MAX_TRAVELLERS,
    MAX_TRIP_DAYS
)
from utils.calculations import format_pkr
from services.trip_planner import TripPlanner
from services.budget_manager import MonthlyBudgetManager
from services.report_generator import ReportGenerator
from pdf.pdf_generator import PDFReportGenerator


class SmartLifePlannerApp:
    """
    Main interactive CLI application for Smart Life Planner.
    Coordinates Pakistan Trip Planner and Monthly Budget Manager modules.
    """

    def __init__(self):
        self.data_manager = DataManager(base_dir=BASE_DIR)
        self.trip_planner = TripPlanner(data_manager=self.data_manager)
        self.budget_manager = MonthlyBudgetManager(data_manager=self.data_manager)
        self.pdf_generator = PDFReportGenerator(data_manager=self.data_manager)

    # ------------------ Console Formatting Helpers ------------------ #

    @staticmethod
    def print_banner(title: str, subtitle: Optional[str] = None):
        print("\n" + "=" * 65)
        print(f"  {title.center(61)}")
        if subtitle:
            print(f"  {subtitle.center(61)}")
        print("=" * 65)

    @staticmethod
    def prompt_input(prompt: str, default: Optional[str] = None) -> str:
        if default is not None:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "
        val = input(full_prompt).strip()
        if not val and default is not None:
            return str(default)
        return val

    # ------------------ Module One: Trip Planner ------------------ #

    def trip_planner_menu(self):
        while True:
            self.print_banner("MODULE 1: PAKISTAN TRIP PLANNER", "Intelligent Costing & Optimization")
            current_status = "None"
            if self.trip_planner.current_plan:
                p = self.trip_planner.current_plan
                st = "CONFIRMED" if p.is_confirmed else "DRAFT"
                current_status = f"{p.destination_name} ({p.days}D/{p.nights}N, {p.travellers}p) - {st}"
            print(f"  [Active Plan: {current_status}]")
            print("  1. Plan a New Trip")
            print("  2. View Active Plan & Day-Wise Itinerary")
            print("  3. Modify Trip Parameters (Dynamic Adjustment)")
            print("  4. View Intelligent Optimization & Feasibility Alternatives")
            print("  5. Confirm Plan & Generate Official PDF Report")
            print("  6. View Saved Past Trips")
            print("  7. Return to Main Menu")

            choice = self.prompt_input("Select an option (1-7)")
            if choice == "1":
                self.handle_new_trip()
            elif choice == "2":
                self.handle_view_active_trip()
            elif choice == "3":
                self.handle_modify_trip()
            elif choice == "4":
                self.handle_trip_optimization()
            elif choice == "5":
                self.handle_confirm_trip_pdf()
            elif choice == "6":
                self.handle_view_saved_trips()
            elif choice == "7":
                break
            else:
                print(">> [Error] Invalid choice. Please enter a number between 1 and 7.")

    def handle_new_trip(self):
        self.print_banner("NEW TRIP PLANNING", "Enter Trip Constraints")

        # 1. Available Budget
        while True:
            b_input = self.prompt_input("Available Budget (PKR)")
            ok, budget, err = validate_positive_number(b_input, "Available Budget", min_val=1000.0)
            if ok:
                break
            print(f">> [Validation Error] {err}")

        # 2. Travellers
        while True:
            t_input = self.prompt_input(f"Number of Travellers (1-{MAX_TRAVELLERS})", default="2")
            ok, travellers, err = validate_integer_range(t_input, "Travellers", 1, MAX_TRAVELLERS)
            if ok:
                break
            print(f">> [Validation Error] {err}")

        # 3. Departure City
        while True:
            dep_input = self.prompt_input("Departure City (e.g., Islamabad, Lahore, Karachi)", default="Islamabad")
            ok, dep_city, err = validate_non_empty_string(dep_input, "Departure City")
            if ok:
                break
            print(f">> [Validation Error] {err}")

        # 4. Destination Type Filter
        print("\nSelect Preferred Destination Type:")
        print("1. Mountains (Murree, Nathiagali, Hunza)")
        print("2. Lakes & Nature (Swat, Kalam, Naran, Skardu)")
        print("3. Historical Places (Lahore, Islamabad)")
        print("4. Any / All Destinations")
        type_choice = self.prompt_input("Choice (1-4)", default="4")
        type_map = {"1": "Mountains", "2": "Lakes & Nature", "3": "Historical Places", "4": "Any"}
        dest_type = type_map.get(type_choice, "Any")

        dest_options = self.trip_planner.filter_destinations_by_type(dest_type)
        print(f"\nAvailable Destinations ({dest_type}):")
        for i, d in enumerate(dest_options, 1):
            print(f"  {i}. {d.name} ({d.region}) - Type: {d.category}")

        while True:
            dest_choice = self.prompt_input("Enter Destination Name or Number", default="1")
            if dest_choice.isdigit() and 1 <= int(dest_choice) <= len(dest_options):
                selected_dest = dest_options[int(dest_choice) - 1].name
                break
            matched = self.trip_planner.find_destination(dest_choice)
            if matched:
                selected_dest = matched.name
                break
            print(">> [Error] Destination not found. Please choose from the list.")

        # 5. Days and Nights
        while True:
            d_input = self.prompt_input(f"Trip Days (1-{MAX_TRIP_DAYS})", default="3")
            n_input = self.prompt_input(f"Trip Nights (0-{MAX_TRIP_DAYS}, must be <= Days)", default="2")
            ok, days, nights, err = validate_trip_duration(d_input, n_input)
            if ok:
                break
            print(f">> [Validation Error] {err}")

        # 6. Travel Category
        print("\nTravel Category:")
        print("1. Budget   (Economy transport & standard lodging)")
        print("2. Standard (Executive AC transport & comfortable hotels)")
        print("3. Premium  (Luxury 4x4 / private car & upscale resorts)")
        cat_choice = self.prompt_input("Choice (1-3)", default="2")
        cat_map = {"1": "Budget", "2": "Standard", "3": "Premium"}
        category = cat_map.get(cat_choice, "Standard")

        # 7. Transportation & Accommodation Preferences
        trans_pref = self.prompt_input("Transportation Preference", default=f"{category} Transport")
        accom_pref = self.prompt_input("Accommodation Preference", default=f"{category} Hotel Room")

        # Create Plan
        try:
            plan = self.trip_planner.create_trip_plan(
                destination_name=selected_dest,
                departure_city=dep_city,
                travellers=travellers,
                days=days,
                nights=nights,
                available_budget=budget,
                travel_category=category,
                transport_preference=trans_pref,
                accommodation_preference=accom_pref,
                destination_type=dest_type
            )
            print("\n>> [Success] Trip plan created and calculated successfully!")
            print(ReportGenerator.generate_trip_text_summary(plan))

            if plan.breakdown.feasibility_status == "Over Budget":
                print("\n>> [Alert] Estimated costs exceed your available budget!")
                print(f">> Shortage: {format_pkr(plan.breakdown.shortage)}")
                opt_in = self.prompt_input("Would you like to view calculated optimization alternatives? (y/n)", default="y")
                if opt_in.lower().startswith("y"):
                    self.handle_trip_optimization()

        except Exception as e:
            print(f">> [Error] Failed to create trip plan: {e}")

    def handle_view_active_trip(self):
        plan = self.trip_planner.current_plan
        if not plan:
            print(">> [Notice] No active trip plan. Please create one first.")
            return

        print(ReportGenerator.generate_trip_text_summary(plan))

        print("\n--- Day-Wise Itinerary ---")
        for item in plan.itinerary:
            print(f"\n[Day {item['day']}: {item['title']}]")
            print(f"  Description:   {item['description']}")
            print(f"  Accommodation: {item['accommodation']}")
            print(f"  Meals:         {item['meals']}")

    def handle_modify_trip(self):
        plan = self.trip_planner.current_plan
        if not plan:
            print(">> [Notice] No active trip plan to modify.")
            return

        self.print_banner("DYNAMIC TRIP ADJUSTMENT", "Modify Parameters Without Restarting")
        print(f"Current Destination: {plan.destination_name} | Travellers: {plan.travellers} | Duration: {plan.days}D/{plan.nights}N | Budget: {format_pkr(plan.available_budget)}")
        print("\nParameters you can modify:")
        print("1. Budget")
        print("2. Travellers count")
        print("3. Destination")
        print("4. Duration (Days & Nights)")
        print("5. Travel Category")
        print("6. Cancel (Keep previous plan unchanged)")

        choice = self.prompt_input("Select parameter to modify (1-6)")
        if choice == "6":
            print(">> Modification cancelled.")
            return

        try:
            # We will perform modification using snapshot/rollback mechanism
            if choice == "1":
                new_b = self.prompt_input("Enter new budget (PKR)")
                ok, val, err = validate_positive_number(new_b, "Budget")
                if not ok:
                    print(f">> [Error] {err}")
                    return
                self.trip_planner.modify_current_plan(available_budget=val)

            elif choice == "2":
                new_t = self.prompt_input("Enter new traveller count")
                ok, val, err = validate_integer_range(new_t, "Travellers", 1, MAX_TRAVELLERS)
                if not ok:
                    print(f">> [Error] {err}")
                    return
                self.trip_planner.modify_current_plan(travellers=val)

            elif choice == "3":
                all_dest = self.trip_planner.get_all_destinations()
                for i, d in enumerate(all_dest, 1):
                    print(f"  {i}. {d.name} ({d.category})")
                new_d = self.prompt_input("Select new destination number or name")
                if new_d.isdigit() and 1 <= int(new_d) <= len(all_dest):
                    dest_name = all_dest[int(new_d) - 1].name
                else:
                    dest_name = new_d
                self.trip_planner.modify_current_plan(destination_name=dest_name)

            elif choice == "4":
                new_days = self.prompt_input(f"Enter Days (1-{MAX_TRIP_DAYS})")
                new_nights = self.prompt_input(f"Enter Nights (0-{MAX_TRIP_DAYS})")
                ok, d_val, n_val, err = validate_trip_duration(new_days, new_nights)
                if not ok:
                    print(f">> [Error] {err}")
                    return
                self.trip_planner.modify_current_plan(days=d_val, nights=n_val)

            elif choice == "5":
                print("1. Budget  2. Standard  3. Premium")
                cat_c = self.prompt_input("Choice (1-3)", default="2")
                cat_map = {"1": "Budget", "2": "Standard", "3": "Premium"}
                self.trip_planner.modify_current_plan(travel_category=cat_map.get(cat_c, "Standard"))

            # Display recalculated plan for user review
            print("\n>> [Review Recalculated Plan]")
            print(ReportGenerator.generate_trip_text_summary(self.trip_planner.current_plan))

            # Prompt to confirm or cancel
            confirm_choice = self.prompt_input("Confirm these changes? (y = Confirm / n = Revert)", default="y")
            if confirm_choice.lower().startswith("y"):
                self.trip_planner.confirm_modifications()
                print(">> [Confirmed] Changes successfully saved to active plan.")
            else:
                self.trip_planner.cancel_modifications()
                print(">> [Cancelled] Modifications reverted. Previous plan preserved.")

        except Exception as e:
            print(f">> [Error during modification] {e}")
            self.trip_planner.cancel_modifications()

    def handle_trip_optimization(self):
        plan = self.trip_planner.current_plan
        if not plan:
            print(">> [Notice] No active trip plan. Please create one first.")
            return

        if plan.breakdown.feasibility_status in ("Within Budget", "Exactly Within Budget"):
            print(f"\n>> Good news! Your current plan is already {plan.breakdown.feasibility_status.upper()}.")
            print(f"Remaining surplus: {format_pkr(plan.breakdown.remaining_budget)}")
            return

        self.print_banner("INTELLIGENT OPTIMIZATION & ALTERNATIVES", "Calculated Feasible Options")
        alternatives = self.trip_planner.get_optimization_alternatives()
        if "error" in alternatives:
            print(f">> {alternatives['error']}")
            return

        strats = alternatives.get("strategies", {})
        print(f"\n[Shortage Diagnosis]")
        print(f"Current Shortage: {format_pkr(plan.breakdown.shortage)}")

        # 1. Budget Increase
        b_info = strats.get("increase_budget", {})
        print(f"\n1. INCREASE BUDGET:")
        print(f"   {b_info.get('description')}")
        print(f"   Required Budget: {format_pkr(b_info.get('minimum_required_budget', 0))}")

        # 2. Reduce Travellers
        t_info = strats.get("reduce_travellers", {})
        print(f"\n2. REDUCE TRAVELLERS:")
        print(f"   {t_info.get('description')}")

        # 3. Reduce Duration
        d_info = strats.get("reduce_duration", {})
        print(f"\n3. REDUCE DURATION:")
        print(f"   {d_info.get('description')}")

        # 4. Adjust Category
        c_info = strats.get("adjust_category", {})
        print(f"\n4. ADJUST TRAVEL CATEGORY:")
        print(f"   {c_info.get('description')}")

        # 5. Change Destination
        dest_info = strats.get("change_destination", {})
        print(f"\n5. ALTERNATIVE DESTINATIONS:")
        if dest_info.get("feasible"):
            for alt in dest_info.get("destinations", []):
                print(f"   • {alt['destination']} ({alt['type']}) [{alt['category']}]: Total {format_pkr(alt['cost'])} (Surplus: {format_pkr(alt['remaining_budget'])})")
        else:
            print("   No other destinations fit within current budget under current duration/group size.")

        # 6. Ranked Best Alternatives
        ranked = alternatives.get("ranked_alternatives", [])
        if ranked:
            print("\n" + "-" * 65)
            print("  TOP RECOMMENDED FEASIBLE PLANS (Strictly Within Budget):")
            print("-" * 65)
            for i, opt in enumerate(ranked[:3], 1):
                print(f"  Option {i}: [{opt['strategy']}] - Score: {opt['score']}/100")
                print(f"    {opt['description']}")
                print(f"    Destination: {opt['destination_name']} | {opt['travellers']} Person(s) | {opt['days']}D/{opt['nights']}N | Category: {opt['travel_category']}")
                print(f"    Recalculated Cost: {format_pkr(opt['total_cost'])} | Surplus: {format_pkr(opt['remaining_budget'])}")

            apply_c = self.prompt_input("Would you like to adopt one of these recommendations? (Enter 1-3 or 'n')", default="n")
            if apply_c in ("1", "2", "3") and int(apply_c) <= len(ranked):
                selected_opt = ranked[int(apply_c) - 1]
                self.trip_planner.modify_current_plan(
                    destination_name=selected_opt["destination_name"],
                    travellers=selected_opt["travellers"],
                    days=selected_opt["days"],
                    nights=selected_opt["nights"],
                    travel_category=selected_opt["travel_category"]
                )
                self.trip_planner.confirm_modifications()
                print("\n>> [Adopted] Recommended plan successfully applied to active plan!")
                print(ReportGenerator.generate_trip_text_summary(self.trip_planner.current_plan))

    def handle_confirm_trip_pdf(self):
        plan = self.trip_planner.current_plan
        if not plan:
            print(">> [Notice] No active trip plan. Please create one first.")
            return

        print("\n" + "=" * 65)
        print("  FINAL REVIEW & CONFIRMATION BEFORE PDF GENERATION")
        print("=" * 65)
        print(ReportGenerator.generate_trip_text_summary(plan))

        conf = self.prompt_input("Are you sure you want to finalize this plan and generate the official PDF? (y/n)", default="y")
        if not conf.lower().startswith("y"):
            print(">> Plan confirmation cancelled. PDF not generated.")
            return

        # 1. Confirm and save
        self.trip_planner.confirm_and_save_current_plan()

        # 2. Generate PDF
        try:
            pdf_path = self.pdf_generator.generate_trip_pdf(plan)
            print(f"\n>> [SUCCESS] Trip Plan PDF successfully generated!")
            print(f">> File Location: {pdf_path}")
        except Exception as e:
            print(f">> [PDF Generation Error] {e}")

    def handle_view_saved_trips(self):
        trips = self.data_manager.load_trips()
        if not trips:
            print(">> No confirmed trip plans saved yet.")
            return

        self.print_banner("SAVED TRIP PLANS", f"Total Records: {len(trips)}")
        for i, t in enumerate(trips, 1):
            bk = t.get("breakdown", {})
            print(f"  {i}. [{t.get('plan_id')}] {t.get('destination_name')} ({t.get('days')}D/{t.get('nights')}N) - {t.get('travellers')} traveller(s)")
            print(f"     Cost: {format_pkr(bk.get('total_cost', 0))} | Budget: {format_pkr(t.get('available_budget', 0))} | Status: {bk.get('feasibility_status')}")
            print(f"     Confirmed At: {t.get('confirmed_at')}")

    # ------------------ Module Two: Monthly Budget ------------------ #

    def budget_manager_menu(self):
        while True:
            self.print_banner("MODULE 2: MONTHLY BUDGET MANAGER", "Income, Expenses, Savings & Tracking")
            active_info = "None"
            if self.budget_manager.active_budget:
                b = self.budget_manager.active_budget
                active_info = f"{b.month} ({b.budget_type}) - PKR {b.total_available:,.2f}"
            print(f"  [Active Budget: {active_info}]")
            print("  1. Create New Monthly Budget")
            print("  2. Load Existing Monthly Budget from Disk")
            print("  3. View Monthly Financial Summary & Overspending Report")
            print("  4. Manage Planned Categories (Add / Update / Remove)")
            print("  5. Record Actual Expense")
            print("  6. View / Update / Delete Recorded Expenses")
            print("  7. Save Budget & Generate Official PDF Report")
            print("  8. Return to Main Menu")

            choice = self.prompt_input("Select an option (1-8)")
            if choice == "1":
                self.handle_create_budget()
            elif choice == "2":
                self.handle_load_budget()
            elif choice == "3":
                self.handle_view_budget_summary()
            elif choice == "4":
                self.handle_manage_categories()
            elif choice == "5":
                self.handle_record_expense()
            elif choice == "6":
                self.handle_manage_expenses()
            elif choice == "7":
                self.handle_save_budget_pdf()
            elif choice == "8":
                break
            else:
                print(">> [Error] Invalid choice. Please enter a number between 1 and 8.")

    def handle_create_budget(self):
        self.print_banner("CREATE MONTHLY BUDGET")
        default_month = datetime.now().strftime("%B %Y")
        month = self.prompt_input("Budget Month (e.g. 'November 2026')", default=default_month)

        while True:
            avail_input = self.prompt_input("Total Monthly Available Amount (PKR)", default="100000")
            ok, available, err = validate_positive_number(avail_input, "Available Amount", min_val=100.0)
            if ok:
                break
            print(f">> [Validation Error] {err}")

        print("\nSelect Budget Type:")
        print("1. Home & Kitchen (Groceries, Utilities, Rent, Household)")
        print("2. Personal Finance (Cosmetics, Fitness, Shopping, Dining, Investment)")
        print("3. Custom (Start with blank or customized categories)")
        t_choice = self.prompt_input("Choice (1-3)", default="1")
        type_map = {"1": "Home & Kitchen", "2": "Personal Finance", "3": "Custom"}
        budget_type = type_map.get(t_choice, "Home & Kitchen")

        try:
            budget = self.budget_manager.create_budget(
                month=month,
                budget_type=budget_type,
                total_available=available
            )
            print(f"\n>> [Success] Monthly budget created for {budget.month} ({budget.budget_type})!")
            print(f">> Available Funds: {format_pkr(budget.total_available)}")

            # Optionally set planned amounts for default categories
            set_planned = self.prompt_input("Would you like to set planned amounts for categories now? (y/n)", default="y")
            if set_planned.lower().startswith("y"):
                for cat in list(budget.planned_categories.keys()):
                    amt_str = self.prompt_input(f"  Planned allocation for '{cat}' (PKR)", default="0")
                    ok_a, amt, _ = validate_positive_number(amt_str, cat, min_val=0.0)
                    if ok_a:
                        budget.update_category(cat, amt)

            # Auto-save
            self.budget_manager.save_current_budget()
            print(ReportGenerator.generate_budget_text_summary(budget))

        except Exception as e:
            print(f">> [Error] Failed to create budget: {e}")

    def handle_load_budget(self):
        budgets = self.data_manager.load_budgets()
        if not budgets:
            print(">> No saved monthly budgets found on disk.")
            return

        print("\nSaved Monthly Budgets:")
        for i, b in enumerate(budgets, 1):
            print(f"  {i}. {b.get('month')} ({b.get('budget_type')}) - Available: {format_pkr(b.get('total_available', 0))}")

        choice = self.prompt_input("Select budget number to load", default="1")
        if choice.isdigit() and 1 <= int(choice) <= len(budgets):
            selected = budgets[int(choice) - 1]
            b_obj = self.budget_manager.load_budget_for_month(selected.get("month", ""))
            if b_obj:
                print(f">> [Success] Budget for {b_obj.month} loaded into active session!")
                print(ReportGenerator.generate_budget_text_summary(b_obj))
        else:
            print(">> [Error] Invalid selection.")

    def handle_view_budget_summary(self):
        b = self.budget_manager.active_budget
        if not b:
            print(">> [Notice] No active budget. Please create or load one first.")
            return

        print(ReportGenerator.generate_budget_text_summary(b))

        overspent = b.get_overspending_categories()
        if overspent:
            print("\n>> [WARNING] CATEGORIES OVERSPENT:")
            for oc in overspent:
                print(f"   • {oc['category']}: Planned {format_pkr(oc['planned'])}, Spent {format_pkr(oc['actual'])} (Over by {format_pkr(oc['overspent_amount'])})")
        else:
            print("\n>> All categories are within planned budget limits.")

    def handle_manage_categories(self):
        b = self.budget_manager.active_budget
        if not b:
            print(">> [Notice] No active budget. Please create or load one first.")
            return

        while True:
            print("\n--- Category Management ---")
            print(f"Total Available: {format_pkr(b.total_available)} | Total Planned: {format_pkr(b.get_total_planned())} | Unallocated: {format_pkr(b.get_unallocated_amount())}")
            for cat, amt in b.planned_categories.items():
                print(f"  • {cat:<30}: {format_pkr(amt)}")

            print("\n1. Add New Category")
            print("2. Update Planned Amount")
            print("3. Remove Category")
            print("4. Done / Return")
            c = self.prompt_input("Choice (1-4)", default="4")

            if c == "1":
                cat_name = self.prompt_input("New Category Name")
                ok_n, clean_name, err_n = validate_non_empty_string(cat_name, "Category Name")
                if not ok_n:
                    print(f">> [Error] {err_n}")
                    continue
                amt_str = self.prompt_input(f"Planned Amount for '{clean_name}' (PKR)", default="0")
                ok_a, amt, _ = validate_positive_number(amt_str, "Amount", min_val=0.0)
                if self.budget_manager.add_category(clean_name, amt if ok_a else 0.0):
                    self.budget_manager.save_current_budget()
                    print(f">> [Added] Category '{clean_name}' registered.")
                else:
                    print(f">> [Error] Category '{clean_name}' already exists.")

            elif c == "2":
                cat_name = self.prompt_input("Category Name to Update")
                amt_str = self.prompt_input("New Planned Amount (PKR)")
                ok_a, amt, err_a = validate_positive_number(amt_str, "Amount", min_val=0.0)
                if not ok_a:
                    print(f">> [Error] {err_a}")
                    continue
                if self.budget_manager.update_category(cat_name, amt):
                    self.budget_manager.save_current_budget()
                    print(f">> [Updated] Category '{cat_name}' planned allocation updated.")
                else:
                    print(f">> [Error] Category '{cat_name}' not found.")

            elif c == "3":
                cat_name = self.prompt_input("Category Name to Remove")
                if self.budget_manager.remove_category(cat_name):
                    self.budget_manager.save_current_budget()
                    print(f">> [Removed] Category '{cat_name}' deleted.")
                else:
                    print(f">> [Error] Category '{cat_name}' not found.")

            elif c == "4":
                break

    def handle_record_expense(self):
        b = self.budget_manager.active_budget
        if not b:
            print(">> [Notice] No active budget. Please create or load one first.")
            return

        self.print_banner("RECORD ACTUAL EXPENSE")
        cats = list(b.planned_categories.keys())
        print("Available Categories:")
        for i, c in enumerate(cats, 1):
            print(f"  {i}. {c}")

        cat_choice = self.prompt_input("Select Category Number or Name", default="1")
        if cat_choice.isdigit() and 1 <= int(cat_choice) <= len(cats):
            selected_cat = cats[int(cat_choice) - 1]
        else:
            selected_cat = cat_choice.strip()

        while True:
            amt_str = self.prompt_input("Expense Amount (PKR)")
            ok, amt, err = validate_positive_number(amt_str, "Expense Amount")
            if ok:
                break
            print(f">> [Error] {err}")

        desc = self.prompt_input("Description / Notes (e.g. Utility bill payment)")
        default_date = datetime.now().strftime("%Y-%m-%d")
        date_str = self.prompt_input("Date (YYYY-MM-DD)", default=default_date)

        try:
            exp = self.budget_manager.record_expense(
                category=selected_cat,
                amount=amt,
                description=desc,
                date_str=date_str
            )
            self.budget_manager.save_current_budget()
            print(f"\n>> [Success] Recorded Expense [{exp.id}]: {exp.category} - {format_pkr(exp.amount)} on {exp.date}")

            # Check if this caused overspending
            actual_totals = b.get_category_actual_totals()
            spent_cat = actual_totals[selected_cat]
            planned_cat = b.planned_categories.get(selected_cat, 0.0)
            if spent_cat > planned_cat:
                print(f">> [Warning] Category '{selected_cat}' is now over budget by {format_pkr(spent_cat - planned_cat)}!")

        except Exception as e:
            print(f">> [Error] Failed to record expense: {e}")

    def handle_manage_expenses(self):
        b = self.budget_manager.active_budget
        if not b:
            print(">> [Notice] No active budget. Please create or load one first.")
            return

        if not b.expenses:
            print(">> No expenses recorded yet for this month.")
            return

        print(f"\nRecorded Expenses ({len(b.expenses)} Total):")
        print(f"{'ID':<14} {'Date':<12} {'Category':<22} {'Amount':>14}  {'Description'}")
        print("-" * 75)
        for exp in b.expenses:
            print(f"{exp.id:<14} {exp.date:<12} {exp.category[:21]:<22} {format_pkr(exp.amount):>14}  {exp.description}")

        print("\n1. Update an Expense")
        print("2. Delete an Expense")
        print("3. Return")
        c = self.prompt_input("Choice (1-3)", default="3")

        if c == "1":
            exp_id = self.prompt_input("Enter Expense ID to update")
            exp = b.find_expense(exp_id)
            if not exp:
                print(f">> [Error] Expense ID '{exp_id}' not found.")
                return

            print(f"Editing Expense {exp.id} (Category: {exp.category}, Amount: {exp.amount}, Desc: {exp.description})")
            new_cat = self.prompt_input(f"New Category", default=exp.category)
            new_amt_str = self.prompt_input(f"New Amount (PKR)", default=str(exp.amount))
            new_desc = self.prompt_input(f"New Description", default=exp.description)
            new_date = self.prompt_input(f"New Date (YYYY-MM-DD)", default=exp.date)

            ok, new_amt, err = validate_positive_number(new_amt_str, "Amount")
            if not ok:
                print(f">> [Error] {err}")
                return

            b.update_expense(exp.id, category=new_cat, amount=new_amt, description=new_desc, date_str=new_date)
            self.budget_manager.save_current_budget()
            print(f">> [Updated] Expense {exp.id} updated.")

        elif c == "2":
            exp_id = self.prompt_input("Enter Expense ID to delete")
            if b.delete_expense(exp_id):
                self.budget_manager.save_current_budget()
                print(f">> [Deleted] Expense {exp_id} removed.")
            else:
                print(f">> [Error] Expense ID '{exp_id}' not found.")

    def handle_save_budget_pdf(self):
        b = self.budget_manager.active_budget
        if not b:
            print(">> [Notice] No active budget to report.")
            return

        self.print_banner("MONTHLY BUDGET CONFIRMATION & PDF GENERATION")
        print(ReportGenerator.generate_budget_text_summary(b))

        conf = self.prompt_input("Generate official PDF report for this monthly budget? (y/n)", default="y")
        if not conf.lower().startswith("y"):
            print(">> PDF generation cancelled.")
            return

        # Save to disk first
        self.budget_manager.save_current_budget()

        # Generate PDF
        try:
            pdf_path = self.pdf_generator.generate_budget_pdf(b)
            print(f"\n>> [SUCCESS] Monthly Budget PDF successfully generated!")
            print(f">> File Location: {pdf_path}")
        except Exception as e:
            print(f">> [PDF Generation Error] {e}")

    # ------------------ Common Menus ------------------ #

    def view_previous_reports_menu(self):
        self.print_banner("VIEW PREVIOUS PDF REPORTS", "Generated Documents Archive")
        reports = self.data_manager.list_generated_reports()
        if not reports:
            print(">> No PDF reports generated yet.")
            print(f">> Reports Directory: {self.data_manager.reports_dir}")
            return

        print(f"Found {len(reports)} generated PDF report(s):\n")
        for i, filename in enumerate(reports, 1):
            full_path = os.path.join(self.data_manager.reports_dir, filename)
            size_kb = os.path.getsize(full_path) / 1024.0 if os.path.exists(full_path) else 0.0
            print(f"  {i}. {filename}")
            print(f"     Path: {full_path}")
            print(f"     Size: {size_kb:.1f} KB\n")

    def developer_info_menu(self):
        self.print_banner("DEVELOPER INFORMATION", "Smart Life Planner Author Profile")
        dev = self.data_manager.load_developer_config()
        print(f"  Developer Name:    {dev.get('developer_name')}")
        print(f"  GitHub Username:   {dev.get('github_username')}")
        print(f"  Contact Email:     {dev.get('email')}")
        print("-" * 65)

        opt = self.prompt_input("Would you like to update developer configuration? (y/n)", default="n")
        if opt.lower().startswith("y"):
            name = self.prompt_input("Developer Name", default=dev.get("developer_name"))
            gh = self.prompt_input("GitHub Username", default=dev.get("github_username"))
            while True:
                em = self.prompt_input("Email Address", default=dev.get("email"))
                ok_em, err_em = validate_email(em)
                if ok_em:
                    break
                print(f">> [Error] {err_em}")

            new_cfg = {
                "developer_name": name,
                "github_username": gh,
                "email": em
            }
            if self.data_manager.save_developer_config(new_cfg):
                self.pdf_generator.developer_info = new_cfg
                print(">> [Saved] Developer configuration updated successfully.")

    # ------------------ Main Application Loop ------------------ #

    def run(self):
        while True:
            self.print_banner("SMART LIFE PLANNER", "Pakistan Trip Planner & Monthly Budget Manager")
            print("  1. Pakistan Trip Planner")
            print("  2. Monthly Budget Manager")
            print("  3. View Previous PDF Reports")
            print("  4. Developer Information")
            print("  5. Exit")
            print("=" * 65)

            choice = self.prompt_input("Select an option (1-5)")
            if choice == "1":
                self.trip_planner_menu()
            elif choice == "2":
                self.budget_manager_menu()
            elif choice == "3":
                self.view_previous_reports_menu()
            elif choice == "4":
                self.developer_info_menu()
            elif choice == "5":
                print("\nThank you for using Smart Life Planner. Safe travels & happy budgeting!")
                break
            else:
                print(">> [Error] Invalid choice. Please enter a number between 1 and 5.")


def main():
    try:
        app = SmartLifePlannerApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user. Goodbye!")
    except Exception as e:
        print(f"\n[Fatal Error] An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
