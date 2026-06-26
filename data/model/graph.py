import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
import numpy as np
import matplotlib.pyplot as plt
from patsy import bs 
from scipy.stats import poisson


df = pd.read_csv('./data.csv', sep=';',
                 names=['team', 'opponent', 'goals', 'elo_diff', 'rest_diff', 'is_home'])

def get_model(formula):
    return smf.glm(formula=formula, data=df, family=sm.families.Poisson()).fit()

elo = df['elo_diff']
formula = "goals ~ bs(elo_diff, df=5, lower_bound=elo.min(), upper_bound=elo.max()) + is_home"
model = smf.glm(formula=formula, data=df, family=sm.families.Poisson()).fit()

formula1 = "goals ~ elo_diff + is_home"
model1 = get_model(formula1)

print(model.summary())

x = np.linspace(elo.min(), elo.max(), len(elo))

home = pd.DataFrame({
    "elo_diff": x,
    "is_home": 1
})

away = pd.DataFrame({
    "elo_diff": x,
    "is_home": 0
})

linear = pd.DataFrame({
    "elo_diff": x,
    "is_home": 1 
})

plt.scatter(
    df["elo_diff"],
    df["goals"],
    alpha=0.2,
    s=10,
    color='0.8',
    label="Training data"
)

plt.ylabel("Expected goals")
plt.xlabel("ELO difference for a team playing away")

plt.plot(x, model.predict(away), linewidth=2, label="Away for spline model")
plt.plot(x, model1.predict(away), linewidth=2, label="Away for linear model")
# plt.plot(x, model.predict(away), linewidth=2, label="Away")
plt.legend()
plt.show()

