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

def calculate_tau(g_us, g_opp, xus, xopp, rho):
    if g_us == 0 and g_opp == 0:
        return max(1.0 - (xus * xopp * rho), 1e-10)
    elif g_us == 0 and g_opp == 1:
        return max(1.0 + (xus * rho), 1e-10)
    elif g_us == 1 and g_opp == 0:
        return max(1.0 + (xopp * rho), 1e-10)
    elif g_us == 1 and g_opp == 1:
        return max(1.0 - rho, 1e-10)
    return 1.0


with open('./weights-dixon-coles-2026', 'rb') as f:
    cached_data = pickle.load(f)
    final_attack = cached_data['final_attack']
    final_defence = cached_data['final_defence']
    final_intercept = cached_data['final_intercept']
    final_home = cached_data['final_home']
    final_rho = cached_data.get('final_rho', 0.0) 
    team_to_id = cached_data['team_to_id']

data = pd.read_csv('./backtest_dixon_coles.csv', sep='\t',
                   names=['date', 'us', 'opp', 'goals', 'opp_goals', 'tournament', 'city', 'country', 'neutral'])

def generate_table(team_a, team_b, xg_a, xg_b, rho, is_neutral=False, max_goals=5):
    prob_matrix = np.zeros((max_goals + 1, max_goals + 1))
    
    for g_a in range(max_goals + 1):
        for g_b in range(max_goals + 1):
            joint_prob = poisson.pmf(g_a, xg_a) * poisson.pmf(g_b, xg_b)
            tau = calculate_tau(g_a, g_b, xg_a, xg_b, rho)
            prob_matrix[g_a, g_b] = (joint_prob * tau) * 100 
            
    row_labels = [f"{team_a} {i}" for i in range(max_goals + 1)]
    col_labels = [f"{team_b} {i}" for i in range(max_goals + 1)]
    
    df_grid = pd.DataFrame(prob_matrix, index=row_labels, columns=col_labels)
    
    venue_text = "Neutral Venue" if is_neutral else f"{team_a} Home Venue"
    print("\n" + "="*50)
    print(f"MATCH PROBABILITY MATRIX: {team_a} vs {team_b}")
    print(f"[{venue_text}] | xG: {xg_a:.2f} - {xg_b:.2f}")
    print("="*50)
    
    print(df_grid.round(2).astype(str) + "%")
    
    return df_grid

xga, xgb = calculate_xg("Morocco", "Netherlands")
generate_table("Morocco", "Netherlands", xga, xgb, final_rho, is_neutral=True)


"""
mae_expected = 0
mae_integer = 0
ll = 0
correct = 0
l = 0 

mean_goals = data['goals'].mean()
baseline_match_errors = []
model_match_errors = []

for row in data.itertuples(index=False):
    try:
        is_neutral = row.us == row.country 
        xus, xopp = calculate_xg(row.us, row.opp, is_neutral)
        l += 1
        
        best_prob = 0.0
        pred_us_goals = 0
        pred_opp_goals = 0
        
        for g_us in range(10):
            for g_opp in range(10):
                joint_prob = poisson.pmf(g_us, xus) * poisson.pmf(g_opp, xopp)
                joint_prob *= calculate_tau(g_us, g_opp, xus, xopp, final_rho)
                
                if joint_prob > best_prob:
                    best_prob = joint_prob
                    pred_us_goals = g_us
                    pred_opp_goals = g_opp
        
        if pred_us_goals == row.goals and pred_opp_goals == row.opp_goals:
            correct += 1
            
        mae_expected += abs(xus - row.goals) + abs(xopp - row.opp_goals)
        mae_integer += abs(pred_us_goals - row.goals) + abs(pred_opp_goals - row.opp_goals)

        actual_prob = poisson.pmf(row.goals, xus) * poisson.pmf(row.opp_goals, xopp)
        actual_prob *= calculate_tau(row.goals, row.opp_goals, xus, xopp, final_rho)

        model_match_errors.append(-np.log(max(actual_prob, 1e-10)))
        match_loss_baseline = (
            -np.log(poisson.pmf(row.goals, mean_goals)) +
            -np.log(poisson.pmf(row.opp_goals, mean_goals))
        )
        baseline_match_errors.append(match_loss_baseline)

        ll -= np.log(max(actual_prob, 1e-10))

    except:
        pass

print('====================================')
print(f'Matches Evaluated:                 {l}')
print(f'Exact Scorelines Correct:          {correct} out of {l} ({(correct/l)*100:.1f}%)')
print(f'MAE (per team) using xG (Float):   {(mae_expected / (2 * l)):.4f}')
print(f'MAE (per team) using Mode (Int):   {(mae_integer / (2 * l)):.4f}')
print(f'Match Log Loss:                    {(ll / l):.4f}')

stat, p = wilcoxon(model_match_errors, baseline_match_errors)
print(f'True Match-Level Wilcoxon p-value: {p:.4f}')
"""

