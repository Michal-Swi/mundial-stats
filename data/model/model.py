import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
import numpy as np
import matplotlib.pyplot as plt
from patsy import bs 
from scipy.stats import poisson

df = pd.read_csv('./data.csv', sep=';',
                 names=['team', 'opponent', 'goals', 'elo_diff', 'rest_diff', 'is_home'])

elo = df['elo_diff']
formula = "goals ~ bs(elo_diff, df=3, lower_bound=elo.min(), upper_bound=elo.max()) + is_home"
formula1 = "goals ~ elo_diff + is_home"

model = smf.glm(formula=formula, data=df, family=sm.families.Poisson()).fit()
model1 = smf.glm(formula=formula1, data=df, family=sm.families.Poisson()).fit()

print(model.summary())

elo_diff = -58 
is_home = 0

match_data = pd.DataFrame({
    'elo_diff': [elo_diff],
    'is_home': [is_home]
})

model_lambda = model1.predict(match_data).iloc[0]
print(f"Expected Goals for linear model: (\u03BB): {model_lambda:.2f}\n")

print("Betting Odds, scored goals for linear model:")
for goals in range(5):
    probability = poisson.pmf(goals, model_lambda) * 100
    print(f"Exactly {goals} goals: {probability:.1f}%")


model_lambda1 = model.predict(match_data).iloc[0]
print(f"Expected Goals for spline model: (\u03BB): {model_lambda1:.2f}\n")

print("Betting Odds, scored goals for spline model:")
for goals in range(5):
    probability = poisson.pmf(goals, model_lambda1) * 100
    print(f"Exactly {goals} goals: {probability:.1f}%")

def generate_table(trained_model, team_a, team_b, elo_a, elo_b, is_home_a=0, is_home_b=0, max_goals=5):
    lambda_a = trained_model.predict(pd.DataFrame({
        'elo_diff': [elo_a - elo_b],
        'is_home': [is_home_a]
    })).iloc[0]
    
    lambda_b = trained_model.predict(pd.DataFrame({
        'elo_diff': [elo_b - elo_a],
        'is_home': [is_home_b] 
    })).iloc[0]
    
    prob_matrix = np.zeros((max_goals + 1, max_goals + 1))
    
    for g_a in range(max_goals + 1):
        for g_b in range(max_goals + 1):
            joint_prob = poisson.pmf(g_a, lambda_a) * poisson.pmf(g_b, lambda_b)
            prob_matrix[g_a, g_b] = joint_prob * 100 
            
    row_labels = [f"{team_a} {i}" for i in range(max_goals + 1)]
    col_labels = [f"{team_b} {i}" for i in range(max_goals + 1)]
    
    df_grid = pd.DataFrame(prob_matrix, index=row_labels, columns=col_labels)
    
    venue_text = f"{team_a} Home Venue" if is_home_a == 1 else "Neutral / Away Venue"
    print("\n" + "="*55)
    print(f"GLM PROBABILITY MATRIX: {team_a} vs {team_b}")
    print(f"[{venue_text}] | xG: {lambda_a:.2f} - {lambda_b:.2f}")
    print("="*55)
    
    print(df_grid.round(2).astype(str) + "%")

    df_export = df_grid.round(2).map(lambda x: f"{x:.2f}%".replace(".", ","))

    df_export.to_csv(
        "probability_matrix.csv",
        sep=";",
        decimal=",",
        encoding="utf-8-sig"
    )
    
    return df_grid

generate_table(
    trained_model=model1, 
    team_a="Colombia", 
    team_b="Ghana", 
    elo_a=2004, 
    elo_b=1575, 
)
