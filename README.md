# US²DF Sample Size Planner

This Streamlit application implements the methods in the accompanying manuscript. It uses the finite-population precision convention, exact noncentral-t calculations for one- and two-sample means, a balanced one-way noncentral-F calculation, and explicitly labelled normal approximations for proportions.

Run locally with `pip install -r requirements.txt` followed by `streamlit run app.py`.

For an existing Render service, retain its URL and set the build command to `pip install -r requirements.txt` and the start command to `bash start.sh`. The service binds to the supplied PORT. The included render.yaml is an optional blueprint for a new service. No database migration or external credentials are required.

The default is an analytical two-group mean calculation. Rounded reference values of 400, 65 and 30 per group are available only for the manuscript's balanced two-group reference design. All required counts use the ceiling, including precision limits, per-group allocations, model screens and recruitment targets. The population cap is reported separately from the uncapped requirement.

Run `python -m unittest discover -s tests -v` for the calculation and interface checks. The application does not claim statistical adequacy outside the assumptions of its selected method.
