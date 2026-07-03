import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson
from datetime import datetime
import os
import pickle

df = pd.read_csv(
    "./dixon-coles",
    sep=";",
    names=["year", "month", "day", "home_team", "away_team", "home_goals", "away_goals"]
)

prediction_date = datetime(2026, 6, 11)
dates = pd.to_datetime(dict(year=df.year, month=df.month, day=df.day))
days_old = (prediction_date - dates).dt.days

df = df[days_old > 0].copy()
days_old = days_old[days_old > 0]

XI = 0.0018
df["weight"] = np.exp(-XI * days_old)

MIN_MATCHES = 20
home_counts = df["home_team"].value_counts()
away_counts = df["away_team"].value_counts()
total_counts = home_counts.add(away_counts, fill_value=0)
valid_teams = total_counts[total_counts >= MIN_MATCHES].index

df = df[df["home_team"].isin(valid_teams) & df["away_team"].isin(valid_teams)].copy()

teams = sorted(set(df.home_team) | set(df.away_team))
N = len(teams)

if N == 0:
    raise ValueError(f"CRITICAL ERROR: No teams survived the filter! "
                     f"No team played {MIN_MATCHES} or more matches in this dataset.")

team_to_id = {t: i for i, t in enumerate(teams)}
id_to_team = {i: t for t, i in team_to_id.items()}

df["home_id"] = df.home_team.map(team_to_id)
df["away_id"] = df.away_team.map(team_to_id)

home_ids = df["home_id"].values
away_ids = df["away_id"].values
home_goals = df["home_goals"].values
away_goals = df["away_goals"].values
weights = df["weight"].values

NUM_PARAMS = 2 * (N - 1) + 3

def likelihood(params):
    attack_params = params[:N-1]
    defence_params = params[N-1:2*N-2]
    rho = params[-3] 
    home = params[-2]
    intercept = params[-1]
    
    attack = np.append(attack_params, 0.0)
    defence = np.append(defence_params, 0.0)

    home_attack = attack[home_ids]
    away_attack = attack[away_ids]
    home_defence = defence[home_ids]
    away_defence = defence[away_ids]

    lam = np.maximum(np.exp(intercept + home_attack + away_defence + home), 1e-10)
    mu = np.maximum(np.exp(intercept + away_attack + home_defence), 1e-10)

    tau = np.ones_like(home_goals, dtype=float)
    
    mask_00 = (home_goals == 0) & (away_goals == 0)
    tau[mask_00] = 1.0 - (lam[mask_00] * mu[mask_00] * rho)
    
    mask_01 = (home_goals == 0) & (away_goals == 1)
    tau[mask_01] = 1.0 + (lam[mask_01] * rho)
    
    mask_10 = (home_goals == 1) & (away_goals == 0)
    tau[mask_10] = 1.0 + (mu[mask_10] * rho)
    
    mask_11 = (home_goals == 1) & (away_goals == 1)
    tau[mask_11] = 1.0 - rho
    
    tau = np.maximum(tau, 1e-10)

    logL = np.sum(weights * (poisson.logpmf(home_goals, lam) + poisson.logpmf(away_goals, mu) + np.log(tau)))

    return -logL

initial = np.zeros(NUM_PARAMS)
bounds = [(-5.0, 5.0) for _ in range(NUM_PARAMS)]
bounds[-3] = (-0.2, 0.2)

print(f"Igniting optimizer engine (L-BFGS-B) for {N} teams...")
res = minimize(
    likelihood, 
    initial, 
    method='L-BFGS-B', 
    bounds=bounds,
    options={'maxiter': 10000, 'maxfun': 2000000}
)

if res.success:
    print(f"\nOptimization Successful! Iterations: {res.nit}")
else:
    print(f"\nOptimization Failed: {res.message}")

raw_attack = np.append(res.x[:N-1], 0.0)
raw_defence = np.append(res.x[N-1:2*N-2], 0.0)

mean_att = np.mean(raw_attack)
mean_def = np.mean(raw_defence)

final_attack = raw_attack - mean_att
final_defence = raw_defence - mean_def
final_rho = res.x[-3] 
final_home = res.x[-2]
final_intercept = res.x[-1] + mean_att + mean_def

team_ratings = [(teams[i], final_attack[i], final_defence[i]) for i in range(N)]
team_ratings.sort(key=lambda x: x[1], reverse=True)

with open('weights-dixon-coles-2026', 'wb') as f:
    pickle.dump({
        'final_attack': final_attack,
        'final_defence': final_defence,
        'final_intercept': final_intercept,
        'final_home': final_home,
        'final_rho': final_rho,
        'team_to_id': team_to_id 
    }, f)

print(f"\nSaved final parameters! Learned Rho (\u03C1): {final_rho:.4f}")

