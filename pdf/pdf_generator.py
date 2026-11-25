import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas

from models.trip import TripPlan
from models.budget import Budget
from utils.data_manager import DataManager
from utils.calculations import format_pkr


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass ReportLab canvas to compute total page count and draw
    developer metadata and 'Page X of Y' in the footer of every page.
    """

    def __init__(self, *args, **kwargs):
        self.developer_info = kwargs.pop("developer_info", {})
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        self.setStrokeColor(colors.HexColor("#D0D3D4"))
        self.setLineWidth(0.6)

        page_w, page_h = self._pagesize

        # Draw footer dividing line
        self.line(40, 42, page_w - 40, 42)

        # Developer info on footer left
        dev_name = self.developer_info.get("developer_name", "Developer")
        gh_user = self.developer_info.get("github_username", "github")
        email = self.developer_info.get("email", "dev@example.com")
        footer_left = f"Smart Life Planner | Developer: {dev_name} | GitHub: @{gh_user} | Email: {email}"
        self.drawString(40, 28, footer_left)

        # Page numbering on footer right
        footer_right = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(page_w - 40, 28, footer_right)

        self.restoreState()


class PDFReportGenerator:
    """
    Generates publication-quality PDF reports for confirmed Trip Plans
    and Monthly Budget analytics.
    Enforces confirmation constraints and embeds developer credentials.
    """

    def __init__(self, data_manager: Optional[DataManager] = None):
        self.data_manager = data_manager or DataManager()
        self.reports_dir = self.data_manager.reports_dir
        self.developer_info = self.data_manager.load_developer_config()

    def _get_unique_filepath(self, prefix: str, identifier: str) -> str:
        """Create unique, non-overwriting PDF filename."""
        clean_id = "".join(c if c.isalnum() else "_" for c in identifier)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_token = uuid.uuid4().hex[:4].upper()
        filename = f"{prefix}_{clean_id}_{timestamp}_{unique_token}.pdf"
        return os.path.join(self.reports_dir, filename)

    def generate_trip_pdf(self, plan: TripPlan) -> str:
        """
        Generate PDF report for a confirmed trip plan.
        Raises ValueError if plan is not confirmed.
        """
        if not plan.is_confirmed:
            raise ValueError("Cannot generate final PDF report for an unconfirmed trip plan.")

        if not plan.breakdown:
            raise ValueError("Trip plan has no calculated cost breakdown.")

        filepath = self._get_unique_filepath("Trip_Report", plan.destination_name)
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=55
        )

        styles = getSampleStyleSheet()
        normal = styles["Normal"]

        # Custom styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0E6655")
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=normal,
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1B4F72")
        )
        meta_style = ParagraphStyle(
            "MetaText",
            parent=normal,
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#5D6D7E")
        )
        section_h = ParagraphStyle(
            "SectionH",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#154360"),
            spaceBefore=12,
            spaceAfter=6
        )
        cell_style = ParagraphStyle(
            "TableCell",
            parent=normal,
            fontName="Helvetica",
            fontSize=9,
            leading=12
        )
        cell_bold = ParagraphStyle(
            "TableCellBold",
            parent=cell_style,
            fontName="Helvetica-Bold"
        )

        story = []

        # Header Title
        story.append(Paragraph("Smart Life Planner", title_style))
        story.append(Paragraph("Pakistan Trip Plan & Cost Feasibility Report", subtitle_style))
        story.append(Spacer(1, 4))
        
        # Metadata banner
        rep_date = datetime.now().strftime("%B %d, %Y - %I:%M %p")
        meta_text = f"<b>Report ID:</b> {plan.plan_id} &nbsp;|&nbsp; <b>Generated:</b> {rep_date} &nbsp;|&nbsp; <b>Status:</b> CONFIRMED"
        story.append(Paragraph(meta_text, meta_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0E6655"), spaceAfter=12))

        # 1. Trip Summary Table
        story.append(Paragraph("1. Trip Parameters & Preferences", section_h))
        bk = plan.breakdown

        trip_params = [
            [Paragraph("<b>Destination</b>", cell_bold), Paragraph(f"{plan.destination_name} ({plan.destination_type})", cell_style),
             Paragraph("<b>Departure City</b>", cell_bold), Paragraph(plan.departure_city, cell_style)],
            [Paragraph("<b>Travellers</b>", cell_bold), Paragraph(f"{plan.travellers} Person(s)", cell_style),
             Paragraph("<b>Duration</b>", cell_bold), Paragraph(f"{plan.days} Days / {plan.nights} Nights", cell_style)],
            [Paragraph("<b>Travel Category</b>", cell_bold), Paragraph(plan.travel_category, cell_style),
             Paragraph("<b>Required Rooms</b>", cell_bold), Paragraph(f"{bk.required_rooms} Room(s)", cell_style)],
            [Paragraph("<b>Transport Preference</b>", cell_bold), Paragraph(plan.transport_preference, cell_style),
             Paragraph("<b>Accommodation</b>", cell_bold), Paragraph(plan.accommodation_preference, cell_style)]
        ]
        t_params = Table(trip_params, colWidths=[120, 145, 120, 145])
        t_params.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9F9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EAEDED")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_params)
        story.append(Spacer(1, 12))

        # 2. Financial Breakdown
        story.append(Paragraph("2. Financial Cost Breakdown (Estimated in PKR)", section_h))
        fin_data = [
            [Paragraph("<b>Expense Category</b>", cell_bold), Paragraph("<b>Calculation Basis</b>", cell_bold), Paragraph("<b>Estimated Amount</b>", cell_bold)],
            [Paragraph("Transportation", cell_style), Paragraph(f"{plan.travellers} traveller(s) × Per Person Rate", cell_style), Paragraph(format_pkr(bk.transportation), cell_bold)],
            [Paragraph("Accommodation", cell_style), Paragraph(f"{bk.required_rooms} room(s) × {plan.nights} night(s)", cell_style), Paragraph(format_pkr(bk.accommodation), cell_bold)],
            [Paragraph("Food & Dining", cell_style), Paragraph(f"{plan.travellers} traveller(s) × {plan.days} day(s)", cell_style), Paragraph(format_pkr(bk.food), cell_bold)],
            [Paragraph("Activities & Misc", cell_style), Paragraph(f"{plan.travellers} traveller(s) × Activity Rate", cell_style), Paragraph(format_pkr(bk.activities_misc), cell_bold)],
            [Paragraph("Subtotal Expenses", cell_bold), Paragraph("Direct trip costs", cell_style), Paragraph(format_pkr(bk.subtotal), cell_bold)],
            [Paragraph(f"Emergency Cushion ({plan.emergency_percentage:.0f}%)", cell_style), Paragraph("Contingency buffer", cell_style), Paragraph(format_pkr(bk.emergency_allowance), cell_bold)],
            [Paragraph("<b>TOTAL ESTIMATED TRIP COST</b>", cell_bold), Paragraph("<b>Subtotal + Emergency</b>", cell_bold), Paragraph(f"<b>{format_pkr(bk.total_cost)}</b>", cell_bold)],
            [Paragraph("Cost Per Person", cell_style), Paragraph(f"Total / {plan.travellers} traveller(s)", cell_style), Paragraph(format_pkr(bk.cost_per_person), cell_bold)],
            [Paragraph("Available Budget", cell_bold), Paragraph("Allocated by user", cell_style), Paragraph(format_pkr(plan.available_budget), cell_bold)],
            [Paragraph("Remaining Balance / (Shortage)", cell_bold),
             Paragraph(f"Budget Feasibility: <b>{bk.feasibility_status}</b>", cell_style),
             Paragraph(f"<b>{format_pkr(bk.remaining_budget if bk.remaining_budget > 0 else -bk.shortage)}</b>", cell_bold)]
        ]

        t_fin = Table(fin_data, colWidths=[180, 200, 150])
        status_color = colors.HexColor("#D4EFDF") if bk.feasibility_status in ("Within Budget", "Exactly Within Budget") else colors.HexColor("#FADBD8")
        t_fin.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B4F72")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#1B4F72")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D3D4")),
            ("BACKGROUND", (0, 7), (-1, 7), colors.HexColor("#EAECEE")),
            ("BACKGROUND", (0, 10), (-1, 10), status_color),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_fin)
        story.append(Spacer(1, 12))

        # 3. Day-Wise Itinerary
        story.append(Paragraph("3. Detailed Day-Wise Itinerary", section_h))
        itinerary_data = [
            [Paragraph("<b>Day</b>", cell_bold), Paragraph("<b>Itinerary & Activities</b>", cell_bold), Paragraph("<b>Meals & Lodging</b>", cell_bold)]
        ]

        for item in plan.itinerary:
            day_label = f"Day {item.get('day', 1)}"
            title_desc = f"<b>{item.get('title', '')}</b><br/>{item.get('description', '')}"
            meals_stay = f"<b>Stay:</b> {item.get('accommodation', 'N/A')}<br/><b>Meals:</b> {item.get('meals', 'N/A')}"
            itinerary_data.append([
                Paragraph(day_label, cell_bold),
                Paragraph(title_desc, cell_style),
                Paragraph(meals_stay, cell_style)
            ])

        t_itin = Table(itinerary_data, colWidths=[60, 310, 160])
        t_itin.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0E6655")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#0E6655")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D3D4")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t_itin)
        story.append(Spacer(1, 14))

        # Disclaimer
        disclaimer = (
            "<i>Note: All estimates are calculated based on standard seasonal approximations in Pakistan "
            "and are not guaranteed commercial market rates. Unforeseen weather conditions, fuel price fluctuations, "
            "and peak tourism surge pricing may affect actual expenditures.</i>"
        )
        story.append(Paragraph(disclaimer, meta_style))

        # Build document with NumberedCanvas
        def canvas_maker(*args, **kwargs):
            return NumberedCanvas(*args, developer_info=self.developer_info, **kwargs)

        doc.build(story, canvasmaker=canvas_maker)
        return filepath

    def generate_budget_pdf(self, budget: Budget) -> str:
        """
        Generate publication-grade PDF report for Monthly Budget analytics.
        """
        filepath = self._get_unique_filepath("Budget_Report", budget.month)
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=55
        )

        styles = getSampleStyleSheet()
        normal = styles["Normal"]

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1B4F72")
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=normal,
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0E6655")
        )
        meta_style = ParagraphStyle(
            "MetaText",
            parent=normal,
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#5D6D7E")
        )
        section_h = ParagraphStyle(
            "SectionH",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#154360"),
            spaceBefore=12,
            spaceAfter=6
        )
        cell_style = ParagraphStyle(
            "TableCell",
            parent=normal,
            fontName="Helvetica",
            fontSize=9,
            leading=12
        )
        cell_bold = ParagraphStyle(
            "TableCellBold",
            parent=cell_style,
            fontName="Helvetica-Bold"
        )

        story = []

        # Header Title
        story.append(Paragraph("Smart Life Planner", title_style))
        story.append(Paragraph("Monthly Financial Management & Budget Report", subtitle_style))
        story.append(Spacer(1, 4))

        rep_date = datetime.now().strftime("%B %d, %Y - %I:%M %p")
        rep_id = f"BUD-{uuid.uuid4().hex[:8].upper()}"
        meta_text = f"<b>Report ID:</b> {rep_id} &nbsp;|&nbsp; <b>Budget Month:</b> {budget.month} &nbsp;|&nbsp; <b>Report Date:</b> {rep_date}"
        story.append(Paragraph(meta_text, meta_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1B4F72"), spaceAfter=12))

        # Financial Snapshot Table
        story.append(Paragraph("1. Executive Financial Summary", section_h))
        tot_planned = budget.get_total_planned()
        tot_actual = budget.get_total_actual()
        rem_balance = budget.get_remaining_balance()
        savings = budget.get_savings()
        savings_pct = budget.get_savings_percentage()
        unallocated = budget.get_unallocated_amount()
        is_over = budget.is_overall_overspent()

        snap_data = [
            [Paragraph("<b>Total Monthly Available</b>", cell_bold), Paragraph(format_pkr(budget.total_available), cell_bold),
             Paragraph("<b>Budget Type</b>", cell_bold), Paragraph(budget.budget_type, cell_style)],
            [Paragraph("<b>Total Planned Budget</b>", cell_bold), Paragraph(format_pkr(tot_planned), cell_style),
             Paragraph("<b>Unallocated Funds</b>", cell_bold), Paragraph(format_pkr(unallocated), cell_style)],
            [Paragraph("<b>Total Actual Expenses</b>", cell_bold), Paragraph(format_pkr(tot_actual), cell_bold),
             Paragraph("<b>Remaining Balance</b>", cell_bold), Paragraph(format_pkr(rem_balance), cell_bold)],
            [Paragraph("<b>Net Savings Achieved</b>", cell_bold), Paragraph(f"<b>{format_pkr(savings)}</b>", cell_bold),
             Paragraph("<b>Savings Rate</b>", cell_bold), Paragraph(f"<b>{savings_pct:.1f}%</b>", cell_bold)],
            [Paragraph("<b>Overall Budget Health</b>", cell_bold),
             Paragraph(f"<b>{'DEFICIT / OVER BUDGET' if is_over else 'HEALTHY / WITHIN BUDGET'}</b>", cell_bold),
             Paragraph("<b>Recorded Expenses</b>", cell_bold), Paragraph(f"{len(budget.expenses)} Transactions", cell_style)]
        ]

        t_snap = Table(snap_data, colWidths=[140, 125, 130, 135])
        health_color = colors.HexColor("#FADBD8") if is_over else colors.HexColor("#D4EFDF")
        t_snap.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9F9")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#BDC3C7")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EAEDED")),
            ("BACKGROUND", (1, 4), (1, 4), health_color),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_snap)
        story.append(Spacer(1, 12))

        # Category Breakdown Table
        story.append(Paragraph("2. Category-Wise Budget Allocations & Spending", section_h))
        cat_data = [
            [
                Paragraph("<b>Category</b>", cell_bold),
                Paragraph("<b>Planned (PKR)</b>", cell_bold),
                Paragraph("<b>Actual (PKR)</b>", cell_bold),
                Paragraph("<b>Difference (PKR)</b>", cell_bold),
                Paragraph("<b>Status</b>", cell_bold)
            ]
        ]

        for item in budget.get_category_breakdown():
            st_str = "<font color='red'><b>OVERSPENT</b></font>" if item["is_overspent"] else "<font color='green'>OK</font>"
            diff_val = item["difference"]
            diff_display = format_pkr(abs(diff_val))
            if diff_val < 0:
                diff_display = f"-{diff_display}"
            
            cat_data.append([
                Paragraph(item["category"], cell_style),
                Paragraph(format_pkr(item["planned"]), cell_style),
                Paragraph(format_pkr(item["actual"]), cell_style),
                Paragraph(diff_display, cell_style),
                Paragraph(st_str, cell_style)
            ])

        # Summary total row
        diff_total = tot_planned - tot_actual
        diff_total_str = format_pkr(abs(diff_total))
        if diff_total < 0:
            diff_total_str = f"-{diff_total_str}"

        cat_data.append([
            Paragraph("<b>TOTAL</b>", cell_bold),
            Paragraph(f"<b>{format_pkr(tot_planned)}</b>", cell_bold),
            Paragraph(f"<b>{format_pkr(tot_actual)}</b>", cell_bold),
            Paragraph(f"<b>{diff_total_str}</b>", cell_bold),
            Paragraph(f"<b>{'DEFICIT' if is_over else 'SURPLUS'}</b>", cell_bold)
        ])

        t_cats = Table(cat_data, colWidths=[160, 95, 95, 95, 85])
        t_cats.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B4F72")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#1B4F72")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D3D4")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EAECEE")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_cats)
        story.append(Spacer(1, 14))

        # Overspending Highlights if any
        overspent = budget.get_overspending_categories()
        if overspent:
            story.append(Paragraph("3. Overspending Warnings & Action Required", section_h))
            over_lines = []
            for oc in overspent:
                over_lines.append(
                    f"• <b>{oc['category']}:</b> Planned {format_pkr(oc['planned'])}, but spent {format_pkr(oc['actual'])} (Over budget by <b>{format_pkr(oc['overspent_amount'])}</b>)."
                )
            warn_p = Paragraph("<br/>".join(over_lines), cell_style)
            warn_table = Table([[warn_p]], colWidths=[530])
            warn_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FADBD8")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E74C3C")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(warn_table)
            story.append(Spacer(1, 12))

        # Recent transactions if available
        if budget.expenses:
            story.append(Paragraph("4. Itemized Expense Log (Recent Transactions)", section_h))
            exp_data = [
                [
                    Paragraph("<b>ID</b>", cell_bold),
                    Paragraph("<b>Date</b>", cell_bold),
                    Paragraph("<b>Category</b>", cell_bold),
                    Paragraph("<b>Description</b>", cell_bold),
                    Paragraph("<b>Amount (PKR)</b>", cell_bold)
                ]
            ]
            # Show up to 15 recent expenses
            recent_exp = list(reversed(budget.expenses))[:15]
            for exp in recent_exp:
                exp_data.append([
                    Paragraph(exp.id, cell_style),
                    Paragraph(exp.date, cell_style),
                    Paragraph(exp.category, cell_style),
                    Paragraph(exp.description, cell_style),
                    Paragraph(format_pkr(exp.amount), cell_bold)
                ])

            t_exp = Table(exp_data, colWidths=[70, 75, 110, 185, 90])
            t_exp.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#34495E")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EAEDED")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(t_exp)

        # Build document with NumberedCanvas
        def canvas_maker(*args, **kwargs):
            return NumberedCanvas(*args, developer_info=self.developer_info, **kwargs)

        doc.build(story, canvasmaker=canvas_maker)
        return filepath
