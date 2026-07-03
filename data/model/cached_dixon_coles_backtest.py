import numpy as np
import pandas as pd
import pickle
from scipy.stats import wilcoxon
from scipy.stats import poisson

def calculate_xg(home_team, away_team, is_neutral=True):
    if home_team not in team_to_id or away_team not in team_to_id:
        raise ValueError(f"Cannot predict: '{home_team}' or '{away_team}' was not in the training data.")

    h_id = team_to_id[home_team]
    a_id = team_to_id[away_team]

    alpha_h = final_attack[h_id]
    beta_h = final_defence[h_id]

    alpha_a = final_attack[a_id]
    beta_a = final_defence[a_id]

    gamma = 0.0 if is_neutral else final_home

    home_xg = np.exp(final_intercept + alpha_h + beta_a + gamma)
    away_xg = np.exp(final_intercept + alpha_a + beta_h)

    return home_xg, away_xg

"""
id_to_team = {v: k for k, v in team_to_id.items()}
def get_team_from_id(team_id):
    if team_id not in id_to_team:
        raise ValueError(f"Invalid team ID: {team_id}")
    return id_to_team[team_id]
"""

with open('./weights-dixon-coles-2026', 'rb') as f:
    cached_data = pickle.load(f)
    final_attack = cached_data['final_attack']
    final_defence = cached_data['final_defence']
    final_intercept = cached_data['final_intercept']
    final_home = cached_data['final_home']
    team_to_id = cached_data['team_to_id']

data = pd.read_csv('./backtest_dixon_coles.csv', sep='\t',
                       names=['date', 'us', 'opp', 'goals', 'opp_goals', 'torunament', 'city', 'country', 'neutral'])

mae = 0
ll = 0
correct = 0
l = 0 
i = 0
for row in data.itertuples(index=False):
    try:
        xus, xopp = calculate_xg(row.us, row.opp, row.us == row.country)
        l += 1
        print('us: ', row.us, ' opp: ', row.opp, 
              ' predicted sum of xg: ', xus + xopp)

        prob_us = [poisson.pmf(g, xus) for g in range(10)]
        most_probable_us = prob_us.index(max(prob_us))

        prob_opp = [poisson.pmf(g, xopp) for g in range(10)]
        most_probable_opp = prob_opp.index(max(prob_opp))
        
        mae += abs(most_probable_us - row.goals)
        mae += abs(most_probable_opp - row.opp_goals)

        ll -= np.log(poisson.pmf(row.goals, xus) * poisson.pmf(row.opp_goals, xopp))

        if most_probable_us == row.goals:
            correct += 1
    except:
        print('No team: ', row.us, ' or: ', row.opp)

print('===')
print('Model guessed correctly ', correct, ' out of ', l)
print('Mean absolute error: ', mae / (l * 2))
print('Log loss: ', ll / (l * 2))
print('correct: ', correct)
print('len', l)

mean_goals = data['goals'].mean() 
baseline_match_errors = [] 
model_match_errors = []
for row in data.itertuples(index=False):
    lambda_A, lambda_B = calculate_xg(row.us, row.opp, row.us == row.country)

    match_loss_model = (
        -np.log(poisson.pmf(row.goals, lambda_A)) +
        -np.log(poisson.pmf(row.opp_goals, lambda_B))
    )
    match_loss_baseline = (
        -np.log(poisson.pmf(row.goals, mean_goals)) +
        -np.log(poisson.pmf(row.opp_goals, mean_goals))
    )

    model_match_errors.append(match_loss_model)
    baseline_match_errors.append(match_loss_baseline)

stat, p = wilcoxon(model_match_errors, baseline_match_errors)
print(f'True Match-Level Wilcoxon p-value: {p:.4f}')

