import math
import pandas as pd
import streamlit as st
from calculations import (
    REFERENCES, precision, precision_raw, precision_limit, mean_requirement,
    two_proportions, one_proportion, anova_requirement, green, logistic,
    sem_screen, reconcile, count
)

st.set_page_config(page_title="US²DF Sample Size Planner", layout="wide")
st.markdown("""
<style>
.block-container {padding-top:1.3rem;max-width:1180px}
section[data-testid="stSidebar"] {background:var(--secondary-background-color)}
.us2df-intro {padding:1rem;border:1px solid rgba(127,127,127,.22);border-radius:12px;margin-bottom:1rem}
.us2df-info {line-height:1.5}
.us2df-info .head {font-weight:700;font-size:.95rem;margin:.4rem 0}
.us2df-info .prec {color:#17659f}
.us2df-info .pow {color:#20754a}
.us2df-info .mod {color:#a35d05}
.us2df-info p {margin:.25rem 0 .8rem}
div[data-testid="stMetric"] {border:1px solid rgba(127,127,127,.22);border-radius:12px;padding:.8rem}
</style>""", unsafe_allow_html=True)

def info(text, colour, heading):
    st.markdown(f'<div class="us2df-info"><div class="head {colour}">{heading}</div><p>{text}</p></div>', unsafe_allow_html=True)

def component(label, default, colour, description, method, use):
    a,b=st.sidebar.columns([.83,.17])
    enabled=a.checkbox(label,value=default)
    with b.popover("ℹ", use_container_width=True):
        info(description,colour,"What it represents")
        info(method,colour,"What it uses")
        info(use,colour,"When to select")
    return enabled

st.sidebar.title("US²DF Inputs")
st.sidebar.caption("Select the requirements that apply, then enter the assumptions for your study.")
st.sidebar.subheader("1. Components")
use_precision=component("Precision",True,"prec",
    "Minimum sample size needed to estimate a mean or proportion within a chosen accuracy target.",
    "Finite-population precision calculation or a justified estimand-specific requirement.",
    "Descriptive estimation or a stated precision objective.")
use_power=component("Power",True,"pow",
    "Minimum sample size needed to detect a specified effect with the selected statistical test.",
    "Test-specific analytical calculations. Rounded reference values are available only for balanced two-group mean comparisons.",
    "Hypothesis tests, comparisons and other inferential objectives.")
use_model=component("Model",False,"mod",
    "Minimum sample size needed to support the planned model and its parameters.",
    "Regression and logistic screening rules, a simplified CFA screen, or an externally justified requirement.",
    "Regression, logistic regression, CFA/SEM or another model-dependent analysis.")
if not (use_precision or use_power or use_model):
    st.warning("Select at least one component to calculate a recommendation.")
    st.stop()

st.sidebar.subheader("2. Population and estimand")
N=int(st.sidebar.number_input("Population size (N)",min_value=1,value=50000,step=100))
outcome=st.sidebar.selectbox("Measurement scale",["Categorical (proportions)","Continuous (means, scales)"])
confidence=st.sidebar.selectbox("Confidence level",["95%","99%"])
conf=.95 if confidence=="95%" else .99
rho=2 if outcome.startswith("Categorical") else 4

st.sidebar.subheader("3. Precision")
precision_mode=st.sidebar.selectbox("Precision basis",["Adam finite-population formula","Externally justified requirement"],disabled=not use_precision)
e=.05 if rho==2 else .03
if use_precision and precision_mode.startswith("Adam"):
    e=float(st.sidebar.number_input("Accuracy target (e)",min_value=.001,max_value=.20,value=e,step=.001,format="%.3f",key="e_cat" if rho==2 else "e_cont"))
    st.sidebar.caption("The continuous default is an accuracy convention, not a direct half-width of 0.03 standard deviations.")
elif use_precision:
    precision_manual=float(st.sidebar.number_input("Required completed observations",min_value=1.0,value=385.0,step=1.0))
    precision_source=st.sidebar.text_input("Basis or source for this requirement")

st.sidebar.subheader("4. Power")
design=st.sidebar.selectbox("Statistical design",["Two independent means","One-sample mean","Two independent proportions","One proportion","One-way ANOVA"],disabled=not use_power)
power_mode="Analytical calculation"
if use_power and design=="Two independent means":
    power_mode=st.sidebar.radio("Calculation",["Analytical calculation","Rounded reference values"],horizontal=False)
alpha=.05; target=.8; d=.5; p0=.5; p1=.5; p2=.6; groups=3; f_effect=.25
if use_power and power_mode=="Rounded reference values":
    effect=st.sidebar.radio("Reference effect size",list(REFERENCES),index=1)
    st.sidebar.caption("Balanced, equal-variance two-group means only. Two-sided α=0.05, power=0.80. The reference counts are rounded upward from exact t-test minima.")
else:
    if use_power:
        alpha=float(st.sidebar.number_input("Significance level (α)",min_value=.001,max_value=.20,value=.05,step=.001,format="%.3f"))
        target=float(st.sidebar.number_input("Target power (1−β)",min_value=.50,max_value=.99,value=.80,step=.01,format="%.2f"))
        if design in ["Two independent means","One-sample mean"]:
            d=float(st.sidebar.number_input("Cohen d",min_value=-2.0,max_value=2.0,value=.5,step=.05,format="%.2f"))
        elif design=="Two independent proportions":
            p1=float(st.sidebar.number_input("Group 1 proportion (p1)",min_value=.001,max_value=.999,value=.50,step=.01,format="%.3f"))
            complementary=st.sidebar.checkbox("Set p2 = 1 − p1",value=False)
            if complementary:
                p2=1-p1
                st.sidebar.caption(f"Group 2 proportion: {p2:.3f}. Use this only when the two independent groups are expected to have complementary probabilities.")
            else:
                p2=float(st.sidebar.number_input("Group 2 proportion (p2)",min_value=.001,max_value=.999,value=.60,step=.01,format="%.3f"))
        elif design=="One proportion":
            p0=float(st.sidebar.number_input("Null proportion (p0)",min_value=.001,max_value=.999,value=.50,step=.01,format="%.3f"))
            p1=float(st.sidebar.number_input("Alternative proportion (p1)",min_value=.001,max_value=.999,value=.60,step=.01,format="%.3f"))
        else:
            groups=int(st.sidebar.number_input("Number of groups",min_value=3,max_value=100,value=3,step=1))
            f_effect=float(st.sidebar.number_input("Cohen f",min_value=.001,max_value=2.0,value=.25,step=.01,format="%.3f"))

st.sidebar.subheader("5. Model")
model="None"
if use_model:
    model=st.sidebar.selectbox("Model type",["Multiple regression","Logistic regression","SEM / CFA","Externally justified requirement"])
    if model in ["Multiple regression","Logistic regression"]:
        k=int(st.sidebar.number_input("Candidate predictor parameters (k)",min_value=1,value=10,step=1))
    if model=="Multiple regression":
        overall=st.sidebar.checkbox("Overall-model inference",value=True)
        individual=st.sidebar.checkbox("Individual-predictor inference",value=True)
    elif model=="Logistic regression":
        rate=float(st.sidebar.number_input("Anticipated event rate",min_value=.001,max_value=.999,value=.20,step=.01,format="%.3f"))
        epv=int(st.sidebar.number_input("Events per parameter (EPV)",min_value=1,value=10,step=1))
    elif model=="SEM / CFA":
        latents=int(st.sidebar.number_input("Latent variables",min_value=1,value=3,step=1))
        indicators=int(st.sidebar.number_input("Indicators per latent",min_value=2,value=4,step=1))
        ratio=int(st.sidebar.number_input("Observations per parameter",min_value=1,value=10,step=1))
    else:
        model_manual=float(st.sidebar.number_input("Required completed observations",min_value=1.0,value=200.0,step=1.0))
        model_source=st.sidebar.text_input("Basis or source for this requirement")

st.sidebar.subheader("6. Field adjustments")
apply_deff=st.sidebar.checkbox("Apply design effect",value=False)
deff=float(st.sidebar.number_input("DEFF",min_value=1.0,value=1.5,step=.1,disabled=not apply_deff)) if apply_deff else 1.0
apply_hvif=st.sidebar.checkbox("Apply residual HVIF",value=False)
hvif=float(st.sidebar.number_input("Residual HVIF",min_value=1.0,value=1.2,step=.1,disabled=not apply_hvif)) if apply_hvif else 1.0
if apply_hvif:
    hvif_basis=st.sidebar.text_input("Distinct variance contribution not already in DEFF")
else:
    hvif_basis=""
apply_nr=st.sidebar.checkbox("Apply nonresponse adjustment",value=False)
r=float(st.sidebar.number_input("Anticipated nonresponse rate",min_value=0.0,max_value=.90,value=.05,step=.01)) if apply_nr else 0.0

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

st.title("US²DF Sample Size Planner")
st.markdown('<div class="us2df-intro">Select the applicable requirements. Each requirement is calculated for the stated design and rounded upward to a whole observation. The largest valid requirement determines the base sample size. Field adjustments and population feasibility are reported separately.</div>',unsafe_allow_html=True)
if errors:
    for error in errors: st.error(error)
    st.stop()

a,b,c=st.columns(3)
a.metric("Precision",f"{requirements['Precision']:,}" if "Precision" in requirements else "—")
b.metric("Power",f"{requirements['Power']:,}" if "Power" in requirements else "—")
c.metric("Model",f"{requirements['Model']:,}" if "Model" in requirements else "—")
st.subheader("Recommendation")
a,b=st.columns(2)
a.metric("Base sample size",f"{result['base']:,}")
b.metric("Operational recruitment target",f"{result['operational']:,}")
st.success("Binding requirement: "+", ".join(result["binding"]))
if precision_detail:
    st.caption(f"Precision calculation: {precision_detail[0]:.4f} → {requirements['Precision']:,} whole observations. Large-population reference: {precision_detail[1]:,}.")
if power_detail:
    st.caption(f"Power: {power_detail['per_group']:,} per group; {power_detail['total']:,} total. {power_detail['method']}.")
if result["exceeds_population"]:
    st.warning(f"The uncapped recruitment target is {result['uncapped']:,}, exceeding N={N:,}. The operational cap is {result['operational']:,}. A census may be considered, but the original precision or power target is not thereby guaranteed.")
else:
    st.caption(f"Uncapped recruitment target: {result['uncapped']:,}.")
st.caption("A fixed population, subgroup allocation, nonresponse, and model assumptions can affect feasibility. A larger sample does not itself correct nonresponse bias.")

rows=[{"Component":k,"Required n":v,"Basis":notes[k]} for k,v in requirements.items()]
rows += [
    {"Component":"Base sample size","Required n":result["base"],"Basis":"Maximum of applicable requirements"},
    {"Component":"Uncapped recruitment target","Required n":result["uncapped"],"Basis":f"DEFF={deff:g}; residual HVIF={hvif:g}; nonresponse={r:g}"},
    {"Component":"Operational target","Required n":result["operational"],"Basis":"Population cap applied only when necessary"}]
df=pd.DataFrame(rows)
with st.expander("Calculation breakdown",expanded=True):
    st.dataframe(df,hide_index=True,use_container_width=True)
st.download_button("Download breakdown (CSV)",df.to_csv(index=False).encode(),"US2DF_Breakdown.csv","text/csv")

methods="Sample size was determined using US²DF. "
methods+=" ".join(f"The {k.lower()} requirement was {v:,} ({notes[k]})." for k,v in requirements.items())
methods+=f" The base requirement was {result['base']:,}, the maximum of the applicable requirements. "
methods+=f"Field planning used DEFF={deff:g}, residual HVIF={hvif:g}, and anticipated nonresponse={r:g}, giving an uncapped recruitment target of {result['uncapped']:,} and an operational target of {result['operational']:,}."
if result["exceeds_population"]:
    methods+=" The population cap was reported as a feasibility limit and was not interpreted as satisfying an otherwise unattainable statistical target."
st.subheader("Copy-ready Methods text")
st.code(methods,language="text")
st.markdown("---")
st.markdown("**Reference**\n\nAdam, A. M., Gyasi, R. M., Owusu Junior, P., Gyamfi, E. N., Nsiah, F., & Oppong, P. B. (2026). *Unified Sample Size Determination Framework (US²DF): Reconciling Precision, Power, Model Complexity and Field Constraints.* Manuscript.")
st.caption("The reference describes the manuscript. Add the publication details only after they are confirmed.")
