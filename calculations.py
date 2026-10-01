"""US2DF planning calculations. Counts are always rounded upward."""
import math
from scipy.stats import norm, t, nct, f
from scipy.optimize import brentq

REFERENCES = {"Small": (0.20, 400), "Medium": (0.50, 65), "Large": (0.80, 30)}

def count(value):
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError("A finite, nonnegative requirement is needed.")
    return math.ceil(value)

def precision_raw(N, rho, e, confidence):
    if N < 1 or rho <= 0 or e <= 0 or not 0 < confidence < 1:
        raise ValueError("Check population, accuracy and confidence.")
    z = norm.ppf((1 + confidence) / 2)
    eps = rho * e / z
    return N / (1 + N * eps**2)

def precision(N, rho, e, confidence):
    return count(precision_raw(N, rho, e, confidence))

def precision_limit(rho, e, confidence):
    z = norm.ppf((1 + confidence) / 2)
    return count((z / (rho * e))**2)

def validate_test(alpha, power, effect):
    if not 0 < alpha < 1 or not 0 < power < 1 or not math.isfinite(effect) or effect == 0:
        raise ValueError("Specify a nonzero effect, significance level and target power.")

def _integer_search(fn, start=2, limit=10000000):
    high = start
    while fn(high) < 0:
        high *= 2
        if high > limit:
            raise ValueError("Required sample size exceeds the calculation limit.")
    low = start
    while low < high:
        mid = (low + high) // 2
        if fn(mid) >= 0:
            high = mid
        else:
            low = mid + 1
    return low

def mean_power(n, d, alpha=.05, groups=2):
    validate_test(alpha, .8, d)
    if groups not in (1, 2) or n < 2:
        raise ValueError("Use one or two groups and at least two observations per group.")
    df = n - 1 if groups == 1 else 2*n - 2
    nc = d*math.sqrt(n if groups == 1 else n/2)
    critical = t.ppf(1-alpha/2, df)
    return float(nct.sf(critical, df, nc) + nct.cdf(-critical, df, nc))

def mean_requirement(d, alpha=.05, power=.8, groups=2):
    validate_test(alpha, power, d)
    n = _integer_search(lambda n: mean_power(n, d, alpha, groups)-power)
    return {"per_group":n, "total":n*groups, "method":"Exact noncentral-t power"}

def two_proportions(p1, p2, alpha=.05, power=.8):
    if not 0 < p1 < 1 or not 0 < p2 < 1:
        raise ValueError("Proportions must be between zero and one.")
    delta = abs(p1-p2)
    validate_test(alpha, power, delta)
    pbar = (p1+p2)/2
    raw = ((norm.ppf(1-alpha/2)*math.sqrt(2*pbar*(1-pbar))
            + norm.ppf(power)*math.sqrt(p1*(1-p1)+p2*(1-p2)))**2)/delta**2
    n = count(raw)
    return {"per_group":n,"total":2*n,"method":"Balanced two-sided normal approximation"}

def one_proportion(p0, p1, alpha=.05, power=.8):
    if not 0 < p0 < 1 or not 0 < p1 < 1:
        raise ValueError("Proportions must be between zero and one.")
    delta = abs(p1-p0)
    validate_test(alpha, power, delta)
    raw = ((norm.ppf(1-alpha/2)*math.sqrt(p0*(1-p0))
            + norm.ppf(power)*math.sqrt(p1*(1-p1)))**2)/delta**2
    n = count(raw)
    return {"per_group":n,"total":n,"method":"One-proportion two-sided normal approximation"}

def anova_requirement(f_effect, groups, alpha=.05, power=.8):
    validate_test(alpha, power, f_effect)
    if groups < 3 or f_effect <= 0:
        raise ValueError("Specify at least three groups and positive Cohen f.")
    def achieved(n):
        df1, df2 = groups-1, groups*(n-1)
        crit = f.ppf(1-alpha, df1, df2)
        return float(f.sf(crit, df1, df2, groups*n*f_effect**2))
    n = _integer_search(lambda n: achieved(n)-power)
    return {"per_group":n,"total":n*groups,"method":"Balanced one-way noncentral-F power"}

def green(k, overall=True, individual=True):
    if k < 1 or not (overall or individual):
        raise ValueError("Choose a regression objective and at least one parameter.")
    return max(([50+8*k] if overall else []) + ([104+k] if individual else []))

def logistic(k, rate, epv):
    if k < 1 or epv <= 0 or not 0 < rate < 1:
        raise ValueError("Check parameter count, event rate and EPV.")
    from decimal import Decimal, ROUND_CEILING
    q = Decimal(str(rate))
    raw = Decimal(str(epv))*Decimal(k)/min(q,Decimal(1)-q)
    return int(raw.to_integral_value(rounding=ROUND_CEILING))

def sem_screen(latents, indicators, ratio):
    if latents < 1 or indicators < 2 or ratio <= 0:
        raise ValueError("Check the simplified CFA screening assumptions.")
    params = (indicators-1)*latents + latents*indicators + latents*(latents+1)//2
    return count(params*ratio), params

def reconcile(requirements, N, deff=1, hvif=1, nonresponse=0):
    if not requirements or N < 1 or deff < 1 or hvif < 1 or not 0 <= nonresponse < 1:
        raise ValueError("Select a valid requirement and field assumptions.")
    values = {k:count(v) for k,v in requirements.items()}
    base = max(values.values())
    # Decimal conversion avoids a floating-point error at exact integer boundaries.
    from decimal import Decimal, ROUND_CEILING
    raw = Decimal(base)*Decimal(str(deff))*Decimal(str(hvif))/(Decimal(1)-Decimal(str(nonresponse)))
    uncapped = int(raw.to_integral_value(rounding=ROUND_CEILING))
    return {"components":values,"base":base,
            "binding":[k for k,v in values.items() if v==base],
            "uncapped":uncapped,"operational":min(uncapped,int(N)),
            "exceeds_population":uncapped>N}
