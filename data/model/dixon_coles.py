import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
from scipy.stats import poisson

data = pd.read_csv('./dixon-coles', sep=';',
                   names=['year', 'month', 'day', 'us', 'opp', 'goals', 'home_advantage'])

data['goals'] = data['goals'].astype(int)
data['home_advantage'] = data['home_advantage'].astype(int)

match_counts = data['us'].value_counts()
valid_teams = match_counts[match_counts >= 20].index

data = data[data['us'].isin(valid_teams) & data['opp'].isin(valid_teams)]

formula = "goals ~ C(us) + C(opp) + home_advantage"
model = smf.glm(formula=formula, data=data, family=sm.families.Poisson()).fit()

ratings = model.params.to_dict()
intercept = ratings['Intercept']
gamma = ratings['home_advantage']
def calculate_xg(us_team, opp_team, is_home):
    us_key = f"C(us)[T.{us_team}]"
    opp_key = f"C(opp)[T.{opp_team}]"
    
    alpha = ratings.get(us_key, 0.0)
    beta = ratings.get(opp_key, 0.0)
    
    home_boost = gamma if is_home == 1 else 0.0
    
    lam = np.exp(intercept + alpha + beta + home_boost)
    
    return lam

backtest = pd.read_csv('./backtest_dixon_coles.csv', sep='\t',
                       names=['date', 'us', 'opp', 'goals', 'opp_goals', 'torunament', 'city', 'country', 'neutral'])

l = len(backtest)
mean_goals = data['goals'].mean()
mae_baseline = 0
log_loss_baseline = 0
baseline = 0
for row in backtest.itertuples(index=False):
    mae_baseline += abs(mean_goals - row.goals)
    log_loss_baseline -= np.log(poisson.pmf(row.goals, mean_goals))

    if (row.goals == 1):
        baseline += 1

print('Baseline MAE (mean only):', mae_baseline / l)
print('Baseline log loss (mean only):', log_loss_baseline / l)
print('Always guess 1 correct: ', baseline)

l = 0
mae = 0
log_loss = 0
correct = 0
failed = 0
for row in backtest.itertuples(index=False):
    try:
        model_lambda = calculate_xg(row.us, row.opp, row.us == row.country)
    except:
        failed += 1 
        continue

    l += 1
    probs = [poisson.pmf(g, model_lambda) for g in range(10)]
    most_probable = probs.index(max(probs))

    mae += abs(model_lambda - row.goals)
    log_loss -= np.log(poisson.pmf(row.goals, model_lambda))

    if most_probable == row.goals:
        correct += 1


print('===')
print('Model guessed correctly ', correct, ' out of ', l)
print('Mean absolute error: ', mae / l)
print('Log loss: ', log_loss / l)
print('Failed', failed)
print('len', l)
