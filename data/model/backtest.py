import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
import numpy as np
from scipy.stats import poisson

df = pd.read_csv('./data.csv', sep=';',
                 names=['team', 'opponent', 'goals', 'elo_diff', 'rest_diff', 'is_home'])

formula = "goals ~ elo_diff + is_home"
model = smf.glm(formula=formula, data=df, family=sm.families.Poisson()).fit()

print(model.summary())

backtest = pd.read_csv('../backtest/backtest.csv', sep=';',
                       names=['team', 'opponent', 'goals', 'elo_diff', 'rest_diff', 'is_home'])

backtest_dedup = backtest[backtest['team'] < backtest['opponent']].reset_index(drop=True)
l = len(backtest_dedup)

mae = 0
log_loss = 0
correct = 0
for row in backtest_dedup.itertuples(index=False):
    match_data = pd.DataFrame({
        'elo_diff': [row.elo_diff],
        'is_home': [row.is_home]
    })

    model_lambda = model.predict(match_data).iloc[0]
    probs = [poisson.pmf(g, model_lambda) for g in range(10)]
    most_probable = probs.index(max(probs))

    mae += abs(model_lambda - row.goals)
    log_loss -= np.log(poisson.pmf(row.goals, model_lambda)) 

    if most_probable == row.goals:
        correct += 1

    print(model_lambda, ' ', most_probable, ' ', row.goals)

print('Model guessed correctly ', correct, ' out of ', l)
print('Mean absolute error: ', mae / l)
print('Log loss: ', log_loss / l)

baseline_correct = sum(1 for row in backtest_dedup.itertuples(index=False) if row.goals == 1)
print('Baseline (always guess 1):', baseline_correct, '/', l)

mean_goals = df['goals'].mean()  
mae_baseline = 0
log_loss_baseline = 0
for row in backtest_dedup.itertuples(index=False):
    mae_baseline += abs(mean_goals - row.goals)
    log_loss_baseline -= np.log(poisson.pmf(row.goals, mean_goals))

print('Baseline MAE (mean only):', mae_baseline / l)
print('Baseline log loss (mean only):', log_loss_baseline / l) 

print("Model validity test")
from scipy.stats import wilcoxon

model_errors = []
baseline_errors = []
mean_goals = df['goals'].mean()

for row in backtest_dedup.itertuples(index=False):
    match_data = pd.DataFrame({'elo_diff': [row.elo_diff], 'is_home': [row.is_home]})
    model_lambda = model.predict(match_data).iloc[0]
    model_errors.append(abs(model_lambda - row.goals))
    baseline_errors.append(abs(mean_goals - row.goals))

stat, p = wilcoxon(model_errors, baseline_errors)
print('Wilcoxon p-value:', p)

print(df['goals'].mean())  # what's mean_goals actually equal to?
lambdas = [model.predict(pd.DataFrame({'elo_diff':[r.elo_diff],'is_home':[r.is_home]})).iloc[0] for r in backtest.itertuples(index=False)]
print(pd.Series(lambdas).describe())

print(len(backtest))
print(len(backtest.drop_duplicates(subset=['team','opponent'])))

has_mirror = backtest.apply(
    lambda r: ((backtest['team'] == r.opponent) & (backtest['opponent'] == r.team)).any(),
    axis=1
)
print('Rows with a mirror match:', has_mirror.sum(), 'out of', len(backtest))

backtest['abs_elo_diff'] = backtest['elo_diff'].abs()
merged = backtest.merge(
    backtest,
    left_on=['team', 'opponent', 'abs_elo_diff'],
    right_on=['opponent', 'team', 'abs_elo_diff'],
    suffixes=('_A', '_B')
)
merged = merged[merged['team_A'] < merged['team_B']].reset_index(drop=True)
print(len(merged))  # should be 64 now

baseline_match_errors = []
model_match_errors = []
print(merged.columns.tolist())
print(len(merged))

for row in merged.itertuples(index=False):
    lambda_A = model.predict(pd.DataFrame({
        'elo_diff': [row.elo_diff_A], 'is_home': [row.is_home_A]
    })).iloc[0]
    lambda_B = model.predict(pd.DataFrame({
        'elo_diff': [row.elo_diff_B], 'is_home': [row.is_home_B]
    })).iloc[0]

    match_loss_model = (
        -np.log(poisson.pmf(row.goals_A, lambda_A)) +
        -np.log(poisson.pmf(row.goals_B, lambda_B))
    )
    match_loss_baseline = (
        -np.log(poisson.pmf(row.goals_A, mean_goals)) +
        -np.log(poisson.pmf(row.goals_B, mean_goals))
    )

    model_match_errors.append(match_loss_model)
    baseline_match_errors.append(match_loss_baseline)

stat, p = wilcoxon(model_match_errors, baseline_match_errors)
print(f'True Match-Level Wilcoxon p-value: {p:.4f}')
print('Len of merged: ', len(merged))
print(merged[merged['team_A'] == merged['team_B']])

dupes = backtest[backtest.duplicated(subset=['team','opponent'], keep=False)]
print(dupes)

print(merged[['team_A','team_B']].drop_duplicates().shape[0])  # check for any remaining exact dupes within merged itself

pd.set_option('display.max_rows', None)
print(merged[['team_A','opponent_A','goals_A','team_B','opponent_B','goals_B']])

