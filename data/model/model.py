import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm

df = pd.read_csv('./data.csv', sep=';', 
                 names=['team', 'opponent', 'goals', 'elo_diff', 'rest_diff', 'is_home'])

formula = "goals ~ elo_diff + rest_diff + is_home"
model = smf.glm(formula=formula, data=df, family=sm.families.Poisson()).fit()

print(model.summary())

