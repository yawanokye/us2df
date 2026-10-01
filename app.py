import math
import pandas as pd
import streamlit as st
from calculations import (
    REFERENCES, precision, precision_raw, precision_limit, mean_requirement,
    two_proportions, one_proportion, anova_requirement, green, logistic,
    sem_screen, reconcile, count
)

st.set_page_config(
    page_title="US²DF | Unified Sample Size Determination Framework",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {
    padding-top: 1.15rem;
    padding-bottom: 2.5rem;
    max-width: 1240px;
}
section[data-testid="stSidebar"] {
    background: var(--secondary-background-color);
    border-right: 1px solid rgba(127,127,127,.14);
}
.us2df-hero {
    border: 1px solid rgba(127,127,127,.18);
    border-radius: 18px;
    padding: 1.6rem 1.75rem 1.45rem 1.75rem;
    margin: .25rem 0 1rem 0;
    background: linear-gradient(135deg, rgba(38,99,235,.07), rgba(14,116,144,.035));
}
.us2df-eyebrow {
    font-size: .78rem;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    opacity: .72;
    margin-bottom: .35rem;
}
.us2df-title {
    font-size: clamp(2rem, 4vw, 3.15rem);
    line-height: 1.08;
    font-weight: 780;
    margin: 0 0 .55rem 0;
}
.us2df-subtitle {
    font-size: 1.12rem;
    line-height: 1.62;
    opacity: .82;
    max-width: 980px;
}
.us2df-card {
    border: 1px solid rgba(127,127,127,.18);
    border-radius: 14px;
    padding: 1rem 1.05rem;
    min-height: 132px;
    background: rgba(255,255,255,.02);
}
.us2df-card-title {
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: .38rem;
}
.us2df-card-text {
    font-size: .92rem;
    line-height: 1.48;
    opacity: .78;
}
.us2df-intro {
    padding: 1rem 1.05rem;
    border: 1px solid rgba(127,127,127,.20);
    border-radius: 12px;
    margin-bottom: 1rem;
}
.us2df-info {line-height:1.5}
.us2df-info .head {font-weight:700;font-size:.95rem;margin:.4rem 0}
.us2df-info .prec {color:#17659f}
.us2df-info .pow {color:#20754a}
.us2df-info .mod {color:#a35d05}
.us2df-info p {margin:.25rem 0 .8rem}
.us2df-step {
    border-left: 4px solid rgba(38,99,235,.55);
    padding: .15rem 0 .15rem .85rem;
    margin: .65rem 0 1rem 0;
}
.us2df-note {
    padding: .8rem .95rem;
    border-radius: 10px;
    background: rgba(127,127,127,.075);
    line-height: 1.5;
}
div[data-testid="stMetric"] {
    border:1px solid rgba(127,127,127,.18);
    border-radius:14px;
    padding:.85rem;
    background:rgba(255,255,255,.02);
}
div[data-testid="stTabs"] button p {
    font-weight: 650;
    font-size: .96rem;
}
</style>""", unsafe_allow_html=True)

def info(text, colour, heading):
    st.markdown(f'<div class="us2df-info"><div class="head {colour}">{heading}</div><p>{text}</p></div>', unsafe_allow_html=True)

def component(label, default, colour, description, method, use):
    a,b=st.sidebar.columns([.83,.17])
    enabled=a.checkbox(
        label,
        value=default,
        help=f"{description} {method} Select this component when: {use}",
    )
    with b.popover("ℹ", use_container_width=True):
        info(description,colour,"What it represents")
        info(method,colour,"What it uses")
        info(use,colour,"When to select")
    return enabled

st.sidebar.title("US²DF Inputs")
st.sidebar.caption("Select the requirements that apply, then enter the assumptions for your study.")
st.sidebar.subheader("1. Components")
use_precision=component(
    "Precision",True,"prec",
    "Minimum sample size needed to estimate a mean or proportion within a chosen accuracy target.",
    "Finite-population precision calculation or a justified estimand-specific requirement.",
    "Descriptive estimation or a stated precision objective.",
)
use_power=component(
    "Power",True,"pow",
    "Minimum sample size needed to detect a specified effect with the selected statistical test.",
    "Test-specific analytical calculations. Rounded reference values are available only for balanced two-group mean comparisons.",
    "Hypothesis tests, comparisons and other inferential objectives.",
)
use_model=component(
    "Model",False,"mod",
    "Minimum sample size needed to support the planned model and its parameters.",
    "Regression and logistic screening rules, a simplified CFA screen, or an externally justified requirement.",
    "Regression, logistic regression, CFA/SEM or another model-dependent analysis.",
)
if not (use_precision or use_power or use_model):
    st.sidebar.warning("Select at least one component to calculate a recommendation.")

st.sidebar.subheader("2. Population and estimand")
N=int(st.sidebar.number_input(
    "Population size (N)",
    min_value=1,value=50000,step=100,
    help="Total number of eligible units in the population from which the sample may be drawn. It is used in the finite-population precision calculation and to assess whether the final recruitment target exceeds the available population.",
))
outcome=st.sidebar.selectbox(
    "Measurement scale",
    ["Categorical (proportions)","Continuous (means, scales)"],
    help="Choose the form of the main outcome used for precision planning. Categorical outcomes are represented by proportions; continuous outcomes are represented by means or scale scores. This selection determines the default precision parameter ρ and accuracy setting.",
)
confidence=st.sidebar.selectbox(
    "Confidence level",
    ["95%","99%"],
    help="Confidence level used for the precision calculation. A higher confidence level requires a larger sample because the interval must provide greater coverage.",
)
conf=.95 if confidence=="95%" else .99
rho=2 if outcome.startswith("Categorical") else 4

st.sidebar.subheader("3. Precision")
precision_mode=st.sidebar.selectbox(
    "Precision basis",
    ["Adam finite-population formula","Externally justified requirement"],
    disabled=not use_precision,
    help="Choose how the precision requirement is obtained. Use the built-in finite-population formula for the manuscript's precision convention, or enter an externally justified requirement when another estimand-specific method is more appropriate.",
)
e=.05 if rho==2 else .03
if use_precision and precision_mode.startswith("Adam"):
    e=float(st.sidebar.number_input(
        "Accuracy target (e)",
        min_value=.001,max_value=.20,value=e,step=.001,format="%.3f",
        key="e_cat" if rho==2 else "e_cont",
        help="Accuracy parameter used in the finite-population precision formula. Smaller values impose a stricter accuracy requirement and therefore increase the sample size. Interpret e according to the scale convention used by the formula rather than as a universal margin of error.",
    ))
    st.sidebar.caption("The continuous default is an accuracy convention, not a direct half-width of 0.03 standard deviations.")
elif use_precision:
    precision_manual=float(st.sidebar.number_input(
        "Required completed observations",
        min_value=1.0,value=385.0,step=1.0,
        help="Enter a precision-based minimum sample size obtained from another defensible formula, simulation, software package or study-specific calculation. The value will be rounded upward to a whole observation.",
    ))
    precision_source=st.sidebar.text_input(
        "Basis or source for this requirement",
        help="Briefly state the formula, software, publication, simulation or study-specific rationale supporting the externally justified precision requirement. This description is retained in the calculation breakdown.",
    )

st.sidebar.subheader("4. Power")
design=st.sidebar.selectbox(
    "Statistical design",
    ["Two independent means","One-sample mean","Two independent proportions","One proportion","One-way ANOVA"],
    disabled=not use_power,
    help="Choose the hypothesis-testing design for the power requirement. The selected design determines the effect-size definition and analytical power formula used by the planner.",
)
power_mode="Analytical calculation"
if use_power and design=="Two independent means":
    power_mode=st.sidebar.radio(
        "Calculation",
        ["Analytical calculation","Rounded reference values"],
        horizontal=False,
        help="Analytical calculation uses the selected test, effect size, significance level, power target and allocation. Rounded reference values are available only for the balanced two-group mean design reported in the manuscript.",
    )
alpha=.05; target=.8; d=.5; p0=.5; p1=.5; p2=.6; groups=3; f_effect=.25
if use_power and power_mode=="Rounded reference values":
    effect=st.sidebar.radio(
        "Reference effect size",
        list(REFERENCES),index=1,
        help="Select the Cohen d reference category for the balanced two-group mean design. Rounded per-group values are Small = 400, Medium = 65 and Large = 30, corresponding to d = 0.20, 0.50 and 0.80 under two-sided α = 0.05 and 80% power.",
    )
    st.sidebar.caption("Balanced, equal-variance two-group means only. Two-sided α=0.05, power=0.80. The reference counts are rounded upward from exact t-test minima.")
else:
    if use_power:
        alpha=float(st.sidebar.number_input(
            "Significance level (α)",
            min_value=.001,max_value=.20,value=.05,step=.001,format="%.3f",
            help="Probability of a Type I error under the null hypothesis. The conventional value is 0.05. A smaller α imposes a stricter evidential threshold and generally increases the required sample size.",
        ))
        target=float(st.sidebar.number_input(
            "Target power (1−β)",
            min_value=.50,max_value=.99,value=.80,step=.01,format="%.2f",
            help="Desired probability of detecting the specified effect when it truly exists. A common planning target is 0.80. Higher target power requires a larger sample size.",
        ))
        if design in ["Two independent means","One-sample mean"]:
            d=float(st.sidebar.number_input(
                "Cohen d",
                min_value=-2.0,max_value=2.0,value=.5,step=.05,format="%.2f",
                help="Standardised mean difference to be detected. It expresses the expected mean difference in standard-deviation units. The nonzero effect is combined with α and target power to calculate the required sample size.",
            ))
        elif design=="Two independent proportions":
            p1=float(st.sidebar.number_input(
                "Group 1 proportion (p1)",
                min_value=.001,max_value=.999,value=.50,step=.01,format="%.3f",
                help="Expected outcome proportion in the first independent group. Together with p2, this defines the difference the study is powered to detect.",
            ))
            complementary=st.sidebar.checkbox(
                "Set p2 = 1 − p1",value=False,
                help="Automatically set the second independent-group proportion to 1 − p1. Use this only when there is a substantive reason to expect complementary probabilities across the two independent groups; do not use it merely for convenience.",
            )
            if complementary:
                p2=1-p1
                st.sidebar.caption(f"Group 2 proportion: {p2:.3f}. Use this only when the two independent groups are expected to have complementary probabilities.")
            else:
                p2=float(st.sidebar.number_input(
                    "Group 2 proportion (p2)",
                    min_value=.001,max_value=.999,value=.60,step=.01,format="%.3f",
                    help="Expected outcome proportion in the second independent group. The absolute difference between p1 and p2 is the effect to be detected. Equal values imply a zero difference and cannot define a finite sample size for detecting a nonzero effect.",
                ))
        elif design=="One proportion":
            p0=float(st.sidebar.number_input(
                "Null proportion (p0)",
                min_value=.001,max_value=.999,value=.50,step=.01,format="%.3f",
                help="Proportion specified under the null hypothesis for a one-proportion test. The alternative proportion must differ from this value to define a detectable effect.",
            ))
            p1=float(st.sidebar.number_input(
                "Alternative proportion (p1)",
                min_value=.001,max_value=.999,value=.60,step=.01,format="%.3f",
                help="Expected true proportion under the alternative hypothesis. The difference between this value and p0 determines the effect to be detected.",
            ))
        else:
            groups=int(st.sidebar.number_input(
                "Number of groups",
                min_value=3,max_value=100,value=3,step=1,
                help="Number of independent groups in the balanced one-way ANOVA. The analytical calculation assumes equal group sizes.",
            ))
            f_effect=float(st.sidebar.number_input(
                "Cohen f",
                min_value=.001,max_value=2.0,value=.25,step=.01,format="%.3f",
                help="Standardised effect size for one-way ANOVA. Cohen f summarises the dispersion of group means relative to within-group variability. Larger values represent stronger group differences.",
            ))

st.sidebar.subheader("5. Model")
model="None"
if use_model:
    model=st.sidebar.selectbox(
        "Model type",
        ["Multiple regression","Logistic regression","SEM / CFA","Externally justified requirement"],
        help="Choose the analytical model whose sample-size requirement should be checked. Built-in regression, logistic and CFA/SEM options are planning screens; use an externally justified requirement when a formal model-specific calculation is available.",
    )
    if model in ["Multiple regression","Logistic regression"]:
        k=int(st.sidebar.number_input(
            "Candidate predictor parameters (k)",
            min_value=1,value=10,step=1,
            help="Number of predictor parameters planned for the model. Count parameters to be estimated rather than only conceptual variables when dummy variables, interactions or nonlinear terms create additional coefficients.",
        ))
    if model=="Multiple regression":
        overall=st.sidebar.checkbox(
            "Overall-model inference",value=True,
            help="Select when the analysis will assess the overall multiple-regression model. The Green screening rule for this objective is 50 + 8k.",
        )
        individual=st.sidebar.checkbox(
            "Individual-predictor inference",value=True,
            help="Select when the analysis will interpret tests of individual regression coefficients. The Green screening rule for this objective is 104 + k. When both objectives apply, the larger screen is used.",
        )
    elif model=="Logistic regression":
        rate=float(st.sidebar.number_input(
            "Anticipated event rate",
            min_value=.001,max_value=.999,value=.20,step=.01,format="%.3f",
            help="Expected proportion in the rarer binary outcome category. Sparse outcomes require a larger total sample to obtain the selected number of events per parameter.",
        ))
        epv=int(st.sidebar.number_input(
            "Events per parameter (EPV)",
            min_value=1,value=10,step=1,
            help="Planning screen for the number of observations in the rarer outcome category per candidate model parameter. EPV is a heuristic, not a universal guarantee of model performance; use a formal model-development sample-size method when possible.",
        ))
    elif model=="SEM / CFA":
        latents=int(st.sidebar.number_input(
            "Latent variables",
            min_value=1,value=3,step=1,
            help="Number of latent constructs in the simplified CFA/SEM screening model. This contributes to the approximate count of free parameters.",
        ))
        indicators=int(st.sidebar.number_input(
            "Indicators per latent",
            min_value=2,value=4,step=1,
            help="Number of observed indicators assigned to each latent variable in the simplified screen. The actual parameter count may differ with unequal indicators, cross-loadings, correlated residuals or structural paths.",
        ))
        ratio=int(st.sidebar.number_input(
            "Observations per parameter",
            min_value=1,value=10,step=1,
            help="Selected observations-to-free-parameter ratio used only as an illustrative CFA/SEM planning screen. It is not a universal minimum; model-specific SEM power or precision calculations are preferable when available.",
        ))
    else:
        model_manual=float(st.sidebar.number_input(
            "Required completed observations",
            min_value=1.0,value=200.0,step=1.0,
            help="Enter a model-specific minimum obtained from a formal power, precision, shrinkage, simulation or other defensible calculation. The value will be rounded upward to a whole observation.",
        ))
        model_source=st.sidebar.text_input(
            "Basis or source for this requirement",
            help="State the method, software, publication, simulation or rationale supporting the externally entered model requirement. This description is retained in the calculation breakdown.",
        )

st.sidebar.subheader("6. Field adjustments")
apply_deff=st.sidebar.checkbox(
    "Apply design effect",value=False,
    help="Turn on when the sampling design is expected to inflate estimator variance relative to the reference simple-random-sampling design, for example because of clustering or unequal weighting.",
)
deff=float(st.sidebar.number_input(
    "DEFF",
    min_value=1.0,value=1.5,step=.1,disabled=not apply_deff,
    help="Design effect: ratio of estimator variance under the planned sampling design to its variance under the reference design. DEFF = 1 means no inflation. Use a study- or design-justified value where possible.",
)) if apply_deff else 1.0

apply_hvif=st.sidebar.checkbox(
    "Apply residual HVIF",value=False,
    help="Turn on only when there is an additional, separately justified variance-inflation contribution not already contained in DEFF. Do not apply it when it would duplicate variance already represented by the design effect.",
)
hvif=float(st.sidebar.number_input(
    "Residual HVIF",
    min_value=1.0,value=1.2,step=.1,disabled=not apply_hvif,
    help="Residual Heterogeneity Variance Inflation Factor. Use a value above 1 only for a distinct variance contribution not already incorporated in DEFF. If no independently justified residual inflation exists, leave this adjustment off.",
)) if apply_hvif else 1.0
if apply_hvif:
    hvif_basis=st.sidebar.text_input(
        "Distinct variance contribution not already in DEFF",
        help="Describe the specific residual source of variance inflation represented by HVIF and why it is not already included in DEFF. This explanation helps prevent double-counting.",
    )
else:
    hvif_basis=""

apply_nr=st.sidebar.checkbox(
    "Apply nonresponse adjustment",value=False,
    help="Turn on when fewer than 100% of approached eligible units are expected to provide usable responses. The adjustment increases the recruitment target so the planned number of completed observations can still be achieved.",
)
r=float(st.sidebar.number_input(
    "Anticipated nonresponse rate",
    min_value=0.0,max_value=.90,value=.05,step=.01,
    help="Expected proportion of approached eligible units that will not provide a usable response. For example, 0.20 means 20% nonresponse. This inflates recruitment but does not correct nonresponse bias.",
)) if apply_nr else 0.0

errors=[]; requirements={}; notes={}; precision_detail=None; power_detail=None
try:
    if use_precision:
        if precision_mode.startswith("Adam"):
            raw=precision_raw(N,rho,e,conf)
            requirements["Precision"]=precision(N,rho,e,conf)
            precision_detail=(raw,precision_limit(rho,e,conf))
            notes["Precision"]=f"Adam formula; N={N:,}, rho={rho}, e={e:g}, confidence={confidence}."
        else:
            if not precision_source.strip(): raise ValueError("Enter the basis for the external precision requirement.")
            requirements["Precision"]=count(precision_manual)
            notes["Precision"]=precision_source
    if use_power:
        if power_mode=="Rounded reference values":
            d,pg=REFERENCES[effect]
            power_detail={"per_group":pg,"total":2*pg,"method":f"Rounded reference for d={d:.2f}"}
        elif design=="Two independent means":
            power_detail=mean_requirement(d,alpha,target,2)
        elif design=="One-sample mean":
            power_detail=mean_requirement(d,alpha,target,1)
        elif design=="Two independent proportions":
            power_detail=two_proportions(p1,p2,alpha,target)
        elif design=="One proportion":
            power_detail=one_proportion(p0,p1,alpha,target)
        else:
            power_detail=anova_requirement(f_effect,groups,alpha,target)
        requirements["Power"]=power_detail["total"]
        notes["Power"]=power_detail["method"]
        if power_mode=="Analytical calculation":
            notes["Power"]+=f"; alpha={alpha:g}, target power={target:g}."
    if use_model:
        if model=="Multiple regression":
            requirements["Model"]=green(k,overall,individual)
            notes["Model"]=f"Green screening rule; k={k}. This is not a general power guarantee."
        elif model=="Logistic regression":
            requirements["Model"]=logistic(k,rate,epv)
            notes["Model"]=f"EPV screen; k={k}, event rate={rate:g}, EPV={epv}. Check model-specific requirements."
        elif model=="SEM / CFA":
            requirements["Model"],params=sem_screen(latents,indicators,ratio)
            notes["Model"]=f"Simplified CFA screen; {params} free parameters, ratio={ratio}:1. Model-specific validation is needed."
        else:
            if not model_source.strip(): raise ValueError("Enter the basis for the external model requirement.")
            requirements["Model"]=count(model_manual)
            notes["Model"]=model_source
    if apply_hvif and hvif>1 and not hvif_basis.strip():
        raise ValueError("Explain the separate variance contribution before applying residual HVIF.")
    result=reconcile(requirements,N,deff,hvif,r)
except ValueError as exc:
    errors.append(str(exc))

# ---------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------
st.markdown("""
<div class="us2df-hero">
  <div class="us2df-eyebrow">Unified Sample Size Determination Framework</div>
  <div class="us2df-title">US²DF Sample Size Planner</div>
  <div class="us2df-subtitle">
    <b>Reconciling Precision, Power, Model Complexity and Field Constraints.</b><br>
    A transparent planning environment for identifying the statistical requirement
    that determines sample size, translating it into a field recruitment target,
    and documenting the assumptions behind the decision.
  </div>
</div>
""", unsafe_allow_html=True)

fc1,fc2,fc3=st.columns(3)
with fc1:
    st.markdown("""
    <div class="us2df-card">
      <div class="us2df-card-title">Precision</div>
      <div class="us2df-card-text">
        Determine the whole-number sample required for a stated accuracy target in a
        finite population or enter another justified precision requirement.
      </div>
    </div>""",unsafe_allow_html=True)
with fc2:
    st.markdown("""
    <div class="us2df-card">
      <div class="us2df-card-title">Power</div>
      <div class="us2df-card-text">
        Use a test-specific analytical calculation. Rounded reference values are
        available only for the balanced two-group mean design examined in the study.
      </div>
    </div>""",unsafe_allow_html=True)
with fc3:
    st.markdown("""
    <div class="us2df-card">
      <div class="us2df-card-title">Model & field planning</div>
      <div class="us2df-card-text">
        Add model-specific requirements and translate the base requirement into an
        operational target using justified, non-overlapping field adjustments.
      </div>
    </div>""",unsafe_allow_html=True)

st.markdown("")
planner_tab, concepts_tab, process_tab, interpretation_tab, reference_tab = st.tabs([
    "Planner",
    "Concepts",
    "How US²DF Works",
    "Interpreting Results",
    "Methods & Reference",
])

with planner_tab:
    st.subheader("Sample Size Planner")
    st.markdown(
        '<div class="us2df-intro">'
        'Use the numbered controls in the left panel. Each selected requirement is '
        'calculated for the stated design and rounded upward to a whole observation. '
        'The largest compatible requirement determines the base sample size. Field '
        'adjustments and population feasibility are reported separately.'
        '</div>',
        unsafe_allow_html=True,
    )

    if errors:
        for error in errors:
            st.error(error)
        st.info("Adjust the inputs in the left panel. The explanatory tabs remain available while you refine the calculation.")
    else:
        a,b,c=st.columns(3)
        a.metric("Precision",f"{requirements['Precision']:,}" if "Precision" in requirements else "—",help="Whole-number completed-observation requirement generated by the selected precision method. A dash means the precision component was not selected.")
        b.metric("Power",f"{requirements['Power']:,}" if "Power" in requirements else "—",help="Whole-number requirement generated by the selected statistical power calculation. For group designs, the displayed value is the total sample across groups.")
        c.metric("Model",f"{requirements['Model']:,}" if "Model" in requirements else "—",help="Whole-number requirement associated with the selected model screen or externally justified model-specific calculation.")

        st.subheader("Recommendation")
        a,b=st.columns(2)
        a.metric("Base sample size",f"{result['base']:,}",help="Largest of the applicable compatible precision, power and model requirements. This is the minimum completed-observation target before field adjustments.")
        b.metric("Operational recruitment target",f"{result['operational']:,}",help="Recruitment target after applicable DEFF, residual HVIF and nonresponse adjustments, capped at the finite population when necessary. The uncapped target remains reported separately.")

        st.success("Binding requirement: "+", ".join(result["binding"]))

        if precision_detail:
            st.caption(
                f"Precision calculation: {precision_detail[0]:.4f} → "
                f"{requirements['Precision']:,} whole observations. "
                f"Large-population reference: {precision_detail[1]:,}."
            )
        if power_detail:
            st.caption(
                f"Power: {power_detail['per_group']:,} per group; "
                f"{power_detail['total']:,} total. {power_detail['method']}."
            )
        if result["exceeds_population"]:
            st.warning(
                f"The uncapped recruitment target is {result['uncapped']:,}, exceeding N={N:,}. "
                f"The operational cap is {result['operational']:,}. A census may be considered, "
                "but the original precision or power target is not thereby guaranteed."
            )
        else:
            st.caption(f"Uncapped recruitment target: {result['uncapped']:,}.")

        st.caption(
            "A fixed population, subgroup allocation, nonresponse and model assumptions can affect feasibility. "
            "A larger sample does not itself correct nonresponse bias."
        )

        rows=[{"Component":k,"Required n":v,"Basis":notes[k]} for k,v in requirements.items()]
        rows += [
            {"Component":"Base sample size","Required n":result["base"],"Basis":"Maximum of applicable requirements"},
            {"Component":"Uncapped recruitment target","Required n":result["uncapped"],"Basis":f"DEFF={deff:g}; residual HVIF={hvif:g}; nonresponse={r:g}"},
            {"Component":"Operational target","Required n":result["operational"],"Basis":"Population cap applied only when necessary"},
        ]
        df=pd.DataFrame(rows)
        with st.expander("Calculation breakdown",expanded=True):
            st.dataframe(df,hide_index=True,use_container_width=True)
        st.download_button(
            "Download breakdown (CSV)",
            df.to_csv(index=False).encode(),
            "US2DF_Breakdown.csv",
            "text/csv",
        )

        component_text = []
        for k,v in requirements.items():
            component_text.append(f"the {k.lower()} requirement was n = {v:,} ({notes[k]})")
        if len(component_text) == 1:
            components_sentence = component_text[0]
        elif len(component_text) == 2:
            components_sentence = " and ".join(component_text)
        else:
            components_sentence = ", ".join(component_text[:-1]) + ", and " + component_text[-1]

        binding_text = ", ".join(result["binding"]).lower()
        justification = (
            "Sample size was determined using the Unified Sample Size Determination Framework (US²DF), "
            "which reconciles applicable precision, power and model-based requirements by selecting the "
            "largest valid lower bound as the base sample size. For the present study, "
            f"{components_sentence}. Accordingly, the {binding_text} requirement was binding and a base "
            f"sample size of n = {result['base']:,} was adopted. "
        )
        if deff != 1 or hvif != 1 or r != 0:
            justification += (
                f"Field planning then applied DEFF = {deff:g}, residual HVIF = {hvif:g}, and an anticipated "
                f"nonresponse rate of {r:.0%}, giving an uncapped recruitment target of n = {result['uncapped']:,} "
                f"and an operational recruitment target of n = {result['operational']:,}."
            )
        else:
            justification += (
                f"No field inflation was applied, so the operational recruitment target remained "
                f"n = {result['operational']:,}."
            )
        if result["exceeds_population"]:
            justification += (
                " Because the uncapped target exceeded the available population, the population cap was "
                "reported as a feasibility limit rather than as evidence that the original statistical target had been attained."
            )

        st.subheader("Copy-ready Sample Size Justification")
        st.caption(
            "Use this as a reporting template. In a manuscript, cite US²DF for the decision framework and "
            "also cite or describe the statistical method that generated each component requirement."
        )
        st.code(justification,language="text")

with concepts_tab:
    st.subheader("Concepts")
    st.markdown("""
<div class="us2df-step"><b>Precision requirement</b><br>
The number of completed observations required to estimate the intended quantity at the selected
accuracy and confidence setting. The built-in finite-population option follows the precision
convention used in the manuscript. Every calculated requirement is rounded upward to a whole
observation.</div>

<div class="us2df-step"><b>Power requirement</b><br>
The number of observations needed for a specified statistical test, effect size, significance level,
power target and allocation. The analytical method should match the planned design. For balanced
two-group means, the study reports exact noncentral-t requirements of 394, 64 and 26 per group
for Cohen's d = 0.20, 0.50 and 0.80 at two-sided α = 0.05 and 80% power. Optional rounded
reference values are 400, 65 and 30 per group.</div>

<div class="us2df-step"><b>Model requirement</b><br>
A sample-size constraint associated with the planned model. The built-in regression, logistic
and simplified CFA options are screening tools. A defensible model-specific calculation should
replace a heuristic whenever the information needed for that calculation is available.</div>

<div class="us2df-step"><b>Field adjustments</b><br>
Design effect and residual heterogeneity adjustments concern variance inflation, whereas
nonresponse changes the number of units that may need to be approached. DEFF and residual
HVIF should be multiplied only when they represent distinct sources.</div>
""",unsafe_allow_html=True)

    st.markdown("#### Whole-number rule")
    st.markdown(
        '<div class="us2df-note">A sample size represents people or observations and is therefore '
        'reported as a whole number. US²DF applies the ceiling to every calculated requirement. '
        'For example, 384.15 becomes 385 and 266.77 becomes 267.</div>',
        unsafe_allow_html=True,
    )

with process_tab:
    st.subheader("How US²DF Works")
    st.markdown("The framework treats sample-size planning as a sequence of explicit decisions.")

    st.markdown("#### 1. Identify applicable requirements")
    st.write(
        "Select only the objectives that apply to the study: precision, inferential power, model complexity, "
        "or an externally justified requirement."
    )

    st.markdown("#### 2. Put compatible requirements on a common scale")
    st.write(
        "Each applicable calculation is expressed as a lower bound on completed, usable observations. "
        "Per-group or subgroup requirements must first be translated into the allocation needed for the design."
    )

    st.markdown("#### 3. Determine the base sample size")
    st.latex(r"n^{*}=\max\{n_j:j\in J\}")
    st.write(
        "When the component requirements are valid, compatible lower bounds, their maximum is the smallest "
        "whole-number sample that satisfies all selected requirements."
    )

    st.markdown("#### 4. Translate the base requirement into field recruitment")
    st.latex(r"n_{\mathrm{recruit}}=\left\lceil \frac{n^{*}\times DEFF\times HVIF}{1-r}\right\rceil")
    st.write(
        "The residual HVIF is used only for a distinct variance contribution not already represented by DEFF. "
        "The nonresponse term is a recruitment assumption, not a correction for nonresponse bias."
    )

    st.markdown("#### 5. Assess finite-population feasibility")
    st.write(
        "The uncapped requirement is retained. If it exceeds the available population, the application reports "
        "the operational cap separately; the cap does not imply that an otherwise unattainable statistical target has been met."
    )

with interpretation_tab:
    st.subheader("Interpreting Results")
    i1,i2=st.columns(2)
    with i1:
        st.markdown("#### Component requirements")
        st.write(
            "**Precision**, **Power** and **Model** show the completed-observation requirements generated by "
            "the selected methods. A dash means that component was not selected."
        )
        st.markdown("#### Base sample size")
        st.write(
            "The base sample size is the maximum of the applicable compatible requirements. "
            "The component attaining that maximum is reported as the binding requirement."
        )
    with i2:
        st.markdown("#### Operational recruitment target")
        st.write(
            "This is the number to recruit after justified field adjustments. The application also retains the "
            "uncapped target so a finite-population cap is not mistaken for achievement of the statistical target."
        )
        st.markdown("#### Feasibility warning")
        st.write(
            "When the target exceeds the population, a census or near-census may be operationally sensible. "
            "The intended power or precision should still be interpreted in light of the finite population and analysis design."
        )

    st.markdown("#### What the planner does not do")
    st.markdown(
        "- It does not make a generic benchmark valid for every statistical design.\n"
        "- It does not make overlapping inflation factors independent.\n"
        "- It does not turn a population cap into achieved power.\n"
        "- It does not replace a study-specific model calculation when one is available."
    )

with reference_tab:
    st.subheader("Methods & Reference")
    st.markdown("#### Research article")
    st.markdown(
        "**Adam, A. M., Gyasi, R. M., Owusu Junior, P., Gyamfi, E. N., Nsiah, F., & Oppong, P. B. (2026).**  \n"
        "*Unified Sample Size Determination Framework (US²DF): Reconciling Precision, Power, Model Complexity and Field Constraints.*  \n"
        "Manuscript."
    )
    st.caption("Replace the manuscript citation with the final publication details after publication.")

    st.markdown("#### Application scope")
    st.write(
        "The planner implements the methods described in the accompanying manuscript. Its output is conditional "
        "on the assumptions entered by the user and can provide a structured basis for justifying the final sample size. "
        "The justification should be reported together with the selected design, effect definition, underlying component methods, "
        "model requirements and field adjustments."
    )

    st.markdown("#### Example of a complete sample-size justification")
    st.markdown(
        '<div class="us2df-note">'
        'Sample size was determined using the Unified Sample Size Determination Framework (US²DF), '
        'which treats precision, statistical power and model complexity as potentially competing '
        'lower-bound requirements and selects the largest applicable requirement as the base sample size. '
        'For the study, the precision requirement was n = 385, the power requirement was n = 260, '
        'and the model-based requirement was n = 130. Accordingly, the precision requirement was binding '
        'and a base sample size of n = 385 was adopted. After allowing for 10% anticipated nonresponse, '
        'the recruitment target was increased to n = 428 participants.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "This is an illustration only. Replace the values and assumptions with those generated for the actual study. "
        "US²DF should be cited for the decision framework, while the underlying precision, power or model method should also be reported."
    )

    st.markdown("#### Key implementation principles")
    st.markdown(
        "- Whole-number requirements are always rounded upward.\n"
        "- Analytical power calculations are design-specific.\n"
        "- Rounded 400/65/30 values are restricted to the balanced two-group mean reference design.\n"
        "- Model rules are screening requirements unless a formal model-specific calculation is supplied.\n"
        "- DEFF and residual HVIF are multiplied only when their variance contributions are distinct.\n"
        "- The uncapped recruitment target remains visible when a population cap applies."
    )

st.markdown("---")
st.caption("US²DF Sample Size Planner • Research planning and transparent sample-size documentation")

