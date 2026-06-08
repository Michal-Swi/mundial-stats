import csv

data = []
with open('../../data/E0.csv', newline='') as file:
    for line in file:
        data.append(line.split(','))

parsed = {}
parsed["home_team"] = []
parsed["away_team"] = []
parsed["goals_home"] = []
parsed["goals_away"] = []



