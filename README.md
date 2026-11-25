# Smart Life Planner – Pakistan Trip Planner & Monthly Budget Manager

Developed by: **Muhammad Ali Ajaz**  
GitHub: [@muhammadaliajaz](https://github.com/muhammadaliajaz)  
Email: [chaudharyaliajaz@gmail.com](mailto:chaudharyaliajaz@gmail.com)  

---

## 1. Project Overview

**Smart Life Planner** is a modular Python application designed to assist users in planning domestic travel across Pakistan and managing monthly household and personal finances.

The application brings together two primary modules:
1. **Pakistan Trip Planner:** Plans domestic trips across various regions in Pakistan (Mountains, Lakes & Nature, Historical Places) based on user-defined budgets, duration, group size, and category preferences. When an itinerary exceeds the specified budget, the system identifies the shortage and calculates realistic alternatives (group size reduction, duration adjustment, travel category adjustment, or alternative destinations).
2. **Monthly Budget Manager:** Tracks income allocations, records actual day-to-day expenditures, monitors category-wise differences, flags overspending, and calculates net savings.

Both modules feature complete input validation, state management with rollback protection, persistent data storage via JSON, automated unit tests using Pytest, and PDF report generation via ReportLab.

---

## 2. Architecture & Design

The application follows an Object-Oriented Programming (OOP) architecture with clear separation between data models, business logic services, utility helpers, and output generators.

```
                              ┌────────────────────────┐
                              │   Smart Life Planner   │
                              │       (main.py)        │
                              └───────────┬────────────┘
                                          │
                ┌─────────────────────────┴────────────────────────┐
                ▼                                                  ▼
  ┌───────────────────────────┐                      ┌───────────────────────────┐
  │   Pakistan Trip Planner   │                      │  Monthly Budget Manager   │
  └─────────────┬─────────────┘                      └─────────────┬─────────────┘
                │                                                  │
   ┌────────────┴────────────┐                        ┌────────────┴────────────┐
   ▼                         ▼                        ▼                         ▼
┌──────────────┐      ┌──────────────┐         ┌──────────────┐          ┌──────────────┐
│ Deterministic│      │ Intelligent  │         │ Category &   │          │ Overspending │
│ Cost Engine  │      │ Optimizer    │         │ Expense Mgmt │          │ & Analytics  │
└──────────────┘      └──────────────┘         └──────────────┘          └──────────────┘
   │                         │                        │                         │
   └────────────┬────────────┘                        └────────────┬────────────┘
                ▼                                                  ▼
  ┌───────────────────────────┐                      ┌───────────────────────────┐
  │ Confirmation & Validation │                      │ Confirmation & Validation │
  └─────────────┬─────────────┘                      └─────────────┬─────────────┘
                │                                                  │
                ▼                                                  ▼
  ┌───────────────────────────┐                      ┌───────────────────────────┐
  │  Publication-Grade PDF    │                      │  Publication-Grade PDF    │
  │  Report (NumberedCanvas)  │                      │  Report (NumberedCanvas)  │
  └───────────────────────────┘                      └───────────────────────────┘
```

---

## 3. Module Workflows & Calculations

### Module One: Pakistan Trip Planner
- **Inputs:** Available budget in PKR, number of travellers, departure city, destination preference type, destination selection, days, nights (supports 0 nights for day trips), travel tier (Budget, Standard, Premium), and accommodation/transportation preferences.
- **Formulas & Calculations:**
  - $\text{Transportation} = \text{cost per person} \times \text{travellers}$
  - $\text{Required Rooms} = \lceil \text{travellers} / \text{room capacity} \rceil$
  - $\text{Accommodation} = \text{room rate} \times \text{required rooms} \times \text{nights}$ *(PKR 0 for 0-night day trips)*
  - $\text{Food} = \text{food cost per person per day} \times \text{travellers} \times \text{days}$
  - $\text{Activities \& Misc} = \text{activities cost per person} \times \text{travellers}$
  - $\text{Emergency Allowance} = \text{subtotal} \times 10\%$
  - $\text{Total Cost} = \text{subtotal} + \text{emergency allowance}$
  - $\text{Cost Per Person} = \text{total cost} / \text{travellers}$
  - $\text{Remaining / Shortage} = \text{budget} - \text{total cost}$
- **Feasibility Classification:**
  - **Within Budget:** Estimated Cost < Budget
  - **Exactly Within Budget:** Estimated Cost == Budget
  - **Over Budget:** Estimated Cost > Budget
- **Intelligent Optimization (When Over Budget):**
  - **Strategy 1:** Increase Budget (calculates exact shortage needed).
  - **Strategy 2:** Reduce Travellers (iteratively solves for maximum travellers who can travel within budget).
  - **Strategy 3:** Reduce Duration (solves for feasible days and nights).
  - **Strategy 4:** Change Destination (evaluates other destinations matching or expanding preference type).
  - **Strategy 5:** Adjust Category (downgrades to Standard or Budget tier).
  - **Strategy 6:** Multi-factor scoring ranking feasible alternatives based on preserved group size (30%), duration (25%), destination match (20%), category match (15%), and budget utilization (10%).
  - Every recommendation is verified via `TripCostCalculator` to strictly satisfy $\text{total cost} \le \text{budget}$.
- **Dynamic Modifications & Rollback:** Allows updating parameters without restarting. An unconfirmed or cancelled adjustment restores the previous plan without data loss.
- **Day-Wise Itinerary Generator:** Produces detailed schedules adapted to duration and destination highlights (e.g., Attabad Lake in Hunza, Saif-ul-Malook in Naran, Badshahi Mosque in Lahore).

### Module Two: Monthly Budget Manager
- **Budget Initialization:** Month, budget type (`Home & Kitchen`, `Personal Finance`, or `Custom`), and monthly available income in PKR.
- **Category & Expense Management:** Add, update, and remove categories; record, edit, and delete actual expenses with unique IDs (`EXP-...`).
- **Financial Analytics:**
  - $\text{Total Planned} = \sum \text{Planned Category Amounts}$
  - $\text{Total Actual} = \sum \text{Recorded Expenses}$
  - $\text{Unallocated Balance} = \text{Total Available} - \text{Total Planned}$
  - $\text{Remaining Balance} = \text{Total Available} - \text{Total Actual}$
  - $\text{Net Savings} = \max(0, \text{Remaining Balance})$
  - $\text{Savings Percentage} = (\text{Net Savings} / \text{Total Available}) \times 100$
  - Flags category-level and overall overspending.

---

## 4. Project Structure

```text
python-smart-life-planner/
|-- main.py                      # Main interactive CLI application
|-- preview.html                 # Interactive visual dashboard preview
|-- config/
|   |-- developer.json           # Developer profile configuration
|-- models/
|   |-- __init__.py              # Package exports
|   |-- destination.py           # Destination model & tier rates
|   |-- expense.py               # Expense record model & validation
|   |-- trip.py                  # TripPlan model & CostBreakdown namedtuple
|   |-- budget.py                # Budget model with Counter & deque history
|-- services/
|   |-- __init__.py              # Service package exports
|   |-- trip_planner.py          # Orchestrates trip planning & modifications
|   |-- trip_calculator.py       # Deterministic cost calculations
|   |-- feasibility_checker.py   # Budget feasibility evaluation
|   |-- trip_optimizer.py        # Multi-factor intelligent alternative generator
|   |-- budget_manager.py        # Monthly budget creation, categories & expenses
|   |-- report_generator.py      # Structured text/dictionary summary reports
|-- utils/
|   |-- __init__.py              # Utility package exports
|   |-- validators.py            # Input validation routines
|   |-- calculations.py          # Arithmetic, ceiling division & formatters
|   |-- data_manager.py          # JSON data persistence & backup handling
|-- pdf/
|   |-- __init__.py              # PDF generator exports
|   |-- pdf_generator.py         # ReportLab PDF generator & NumberedCanvas
|-- data/
|   |-- destinations.json        # Database of 9 Pakistan destinations
|   |-- trips.json               # Confirmed trip records
|   |-- budgets.json             # Saved monthly budget records
|-- reports/
|   |-- .gitkeep                 # PDF report storage directory
|-- tests/
|   |-- __init__.py              # Test suite initialization
|   |-- test_trip_planner.py     # Tests for trip lifecycle & rollback
|   |-- test_trip_calculator.py  # Tests for cost calculations & boundaries
|   |-- test_feasibility_checker.py # Tests for feasibility diagnostics
|   |-- test_trip_optimizer.py   # Tests for 5-strategy optimizer & scoring
|   |-- test_budget_manager.py   # Tests for budget, expenses & overspending
|   |-- test_validators.py       # Tests for numbers, durations & categories
|   |-- test_data_manager.py     # Tests for atomic JSON & corruption safety
|   |-- test_pdf_generator.py    # Tests for ReportLab PDFs & developer footers
|-- requirements.txt             # Required Python libraries
|-- .gitignore                   # Version control ignore list
|-- README.md                    # Technical documentation
```

---

## 5. Python Concepts & Data Structures Used

### OOP Implementation
- **Encapsulation:** Object states are protected and manipulated through validated class methods.
- **Separation of Concerns:** Distinct responsibilities across data models, calculation services, persistence layers, and interfaces.
- **State Rollback:** `TripPlan` maintains snapshots during modifications to ensure unconfirmed edits are safely reverted.

### Standard Library Collections Integration
1. **`collections.namedtuple` (`CostBreakdown`, `OptimizationOption`, `ValidationResult`):** Immutable structured records for financial summaries and optimization options.
2. **`collections.Counter`:** Aggregates total actual spending per category in `Budget.get_category_actual_totals()`.
3. **`collections.defaultdict`:** Groups destinations by regional category in `TripPlanner` without key-error overhead.
4. **`collections.deque`:** Bounded audit history ring buffers in `TripPlan` and `Budget` maintaining chronological operation logs.

---

## 6. Destination Database & Pricing Assumptions

Destination records are stored in `data/destinations.json` and cover 9 destinations:

| Destination | Region | Category | Room Cap | Base Transport | Base Room / Night | Food / Day | Activities / Person | Highlights |
|---|---|---|---|---|---|---|---|---|
| **Murree** | Punjab | Mountains | 2 | PKR 3,000 | PKR 4,500 | PKR 2,000 | PKR 2,500 | Mall Road, Patriata Cable Car, Pindi Point |
| **Nathiagali** | KP | Mountains | 2 | PKR 3,500 | PKR 5,000 | PKR 2,200 | PKR 2,500 | Mukshpuri Trek, Miranjani Peak, Pipeline Track |
| **Swat** | KP | Lakes & Nature | 2 | PKR 5,000 | PKR 4,500 | PKR 2,200 | PKR 3,000 | Malam Jabba, White Palace Marghazar |
| **Kalam** | KP | Lakes & Nature | 2 | PKR 6,500 | PKR 5,000 | PKR 2,400 | PKR 3,500 | Mahodand Lake Jeep Safari, Ushu Forest |
| **Hunza** | Gilgit-Baltistan | Mountains | 2 | PKR 12,000 | PKR 6,500 | PKR 2,800 | PKR 4,500 | Baltit Fort, Attabad Lake, Passu Cones |
| **Skardu** | Gilgit-Baltistan | Lakes & Nature | 2 | PKR 14,000 | PKR 7,000 | PKR 3,000 | PKR 5,000 | Shangrila Lake, Cold Desert, Deosai Plains |
| **Naran** | KP | Lakes & Nature | 2 | PKR 6,000 | PKR 5,000 | PKR 2,400 | PKR 3,500 | Lake Saiful Muluk, Babusar Top, Kunhar River |
| **Lahore** | Punjab | Historical Places | 2 | PKR 3,500 | PKR 4,000 | PKR 2,500 | PKR 2,000 | Badshahi Mosque, Lahore Fort, Walled City |
| **Islamabad** | Federal Capital | Historical Places | 2 | PKR 3,000 | PKR 4,500 | PKR 2,500 | PKR 2,200 | Faisal Mosque, Daman-e-Koh, Lok Virsa |

*Note: Stored rates are planning estimates based on standard seasonal averages in Pakistan and do not constitute fixed commercial rates.*

---

## 7. Installation and Execution

### Requirements
- Python 3.10+
- Dependencies: `pytest`, `reportlab`

### Setup Steps
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python main.py

# 3. Open the interactive visual dashboard preview
# Open preview.html in any web browser
```

---

## 8. Automated Pytest Testing

The test suite covers unit calculations, financial boundaries, dynamic adjustments, persistence, and PDF creation.

### Running Tests
```bash
python -m pytest -v
```

### Test Coverage Summary
```text
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\aliaj\Documents\PSEB-Bootcamp\Curriculum\Week-01_Python-Basics\Python-Final-Project-Assessment
collected 73 items

tests/test_budget_manager.py .................................. [ 8%]
tests/test_data_manager.py .................................... [17%]
tests/test_feasibility_checker.py ............................. [20%]
tests/test_pdf_generator.py ................................... [26%]
tests/test_trip_calculator.py ................................. [33%]
tests/test_trip_optimizer.py .................................. [36%]
tests/test_trip_planner.py .................................... [45%]
tests/test_validators.py ...................................... [100%]

============================= 73 passed in 0.80s ==============================
```

---

## 9. PDF Report Generation

Confirmed trip plans and monthly budgets can be exported to PDF documents stored in the `reports/` folder.

- **Developer Footer:** Uses a custom `NumberedCanvas` to draw developer information and page numbering on every page:
  `Smart Life Planner | Developer: Muhammad Ali Ajaz | GitHub: @muhammadaliajaz | Email: chaudharyaliajaz@gmail.com | Page X of Y`
- **Output Tables:** Formatted financial tables with PKR currency notation, status badges, and itemized day-wise itineraries.
