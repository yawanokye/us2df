# US²DF Sample Size Planner

Professional Streamlit implementation of the **Unified Sample Size Determination Framework (US²DF): Reconciling Precision, Power, Model Complexity and Field Constraints**.

## Interface
The application now includes:
- a professional landing/hero section;
- feature cards for Precision, Power, and Model/Field planning;
- five main tabs: Planner, Concepts, How US²DF Works, Interpreting Results, and Methods & Reference;
- explanatory tooltips on every input control, including population, precision, power, model and field-adjustment settings;
- explanatory tooltips on the main output indicators so users can interpret the reported values;
- a dynamic copy-ready Sample Size Justification based on the selected inputs and binding requirement;
- a worked reporting example showing how US²DF and the underlying component methods should be documented;
- the full US²DF calculation engine in the Planner tab;
- whole-number upward rounding for all calculated sample-size requirements;
- test-specific analytical power calculations and design-specific rounded reference values;
- separate base, uncapped recruitment, and finite-population operational targets;
- copy-ready Methods text and CSV export.

## Render deployment
Build command:

`pip install -r requirements.txt`

Start command:

`bash start.sh`

The application binds to Render's `PORT` through `start.sh`. The included `render.yaml` can also be used as a blueprint.

## Local run
`pip install -r requirements.txt`

`streamlit run app.py`

## Checks
`python -m unittest discover -s tests -v`

The package has 19 calculation tests covering precision, exact t-test requirements, proportion calculations, ANOVA, model screens, rounding, max-rule reconciliation, population capping, and application syntax.
