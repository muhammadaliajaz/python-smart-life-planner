from typing import Dict, Any
from models.trip import TripPlan
from models.budget import Budget
from utils.calculations import format_pkr


class ReportGenerator:
    """
    Generates structured text and dictionary summaries for
    Trip Plans and Monthly Budget records.
    """

    @staticmethod
    def generate_trip_text_summary(plan: TripPlan) -> str:
        """Generate human-readable text summary of a trip plan."""
        bk = plan.breakdown
        if not bk:
            return f"Trip Plan {plan.plan_id} (Uncalculated)"

        lines = [
            "=" * 60,
            f"  SMART LIFE PLANNER - PAKISTAN TRIP PLAN",
            "=" * 60,
            f"Plan ID:          {plan.plan_id}",
            f"Created At:       {plan.created_at}",
            f"Status:           {'CONFIRMED' if plan.is_confirmed else 'DRAFT'}",
            "-" * 60,
            f"Destination:      {plan.destination_name} ({plan.destination_type})",
            f"Departure City:   {plan.departure_city}",
            f"Travellers:       {plan.travellers} person(s)",
            f"Duration:         {plan.days} Days / {plan.nights} Nights",
            f"Travel Category:  {plan.travel_category}",
            f"Transport:        {plan.transport_preference}",
            f"Accommodation:    {plan.accommodation_preference} ({bk.required_rooms} Room(s))",
            "-" * 60,
            "FINANCIAL BREAKDOWN (Estimated):",
            f"  Transportation:          {format_pkr(bk.transportation):>16}",
            f"  Accommodation:           {format_pkr(bk.accommodation):>16}",
            f"  Food & Dining:           {format_pkr(bk.food):>16}",
            f"  Activities & Misc:       {format_pkr(bk.activities_misc):>16}",
            f"  Subtotal:                {format_pkr(bk.subtotal):>16}",
            f"  Emergency ({plan.emergency_percentage:.0f}%):          {format_pkr(bk.emergency_allowance):>16}",
            f"  --------------------------------------------------",
            f"  TOTAL ESTIMATED COST:    {format_pkr(bk.total_cost):>16}",
            f"  Cost Per Person:         {format_pkr(bk.cost_per_person):>16}",
            f"  Available Budget:        {format_pkr(plan.available_budget):>16}",
            f"  Remaining Balance:       {format_pkr(bk.remaining_budget):>16}",
            f"  Shortage (if any):       {format_pkr(bk.shortage):>16}",
            f"  Feasibility:             {bk.feasibility_status}",
            "=" * 60
        ]
        return "\n".join(lines)

    @staticmethod
    def generate_budget_text_summary(budget: Budget) -> str:
        """Generate human-readable text summary of a monthly budget."""
        tot_planned = budget.get_total_planned()
        tot_actual = budget.get_total_actual()
        rem_balance = budget.get_remaining_balance()
        savings = budget.get_savings()
        savings_pct = budget.get_savings_percentage()
        unalloc = budget.get_unallocated_amount()

        lines = [
            "=" * 60,
            f"  SMART LIFE PLANNER - MONTHLY FINANCIAL REPORT",
            "=" * 60,
            f"Budget Month:       {budget.month}",
            f"Budget Type:        {budget.budget_type}",
            f"Total Available:    {format_pkr(budget.total_available)}",
            f"Total Planned:      {format_pkr(tot_planned)}",
            f"Total Actual Spent: {format_pkr(tot_actual)}",
            f"Remaining Balance:  {format_pkr(rem_balance)}",
            f"Net Savings:        {format_pkr(savings)} ({savings_pct:.1f}%)",
            f"Unallocated Amount: {format_pkr(unalloc)}",
            f"Overall Status:     {'OVER BUDGET' if budget.is_overall_overspent() else 'WITHIN BUDGET'}",
            "-" * 60,
            f"{'Category':<25} {'Planned':>12} {'Actual':>12} {'Diff':>12} {'Status':>10}",
            "-" * 60
        ]

        for item in budget.get_category_breakdown():
            status = "OVER" if item["is_overspent"] else "OK"
            diff_str = format_pkr(item["difference"])
            lines.append(
                f"{item['category'][:24]:<25} "
                f"{format_pkr(item['planned']):>12} "
                f"{format_pkr(item['actual']):>12} "
                f"{diff_str:>12} "
                f"{status:>10}"
            )
        lines.append("=" * 60)
        return "\n".join(lines)
