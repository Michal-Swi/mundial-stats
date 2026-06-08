import os

countries = open("../current_countries.csv").read().strip().split('\n')

for country in countries:
    if ' ' in country: # won't work
        continue
    
    os.system("curl -O https://www.eloratings.net/" + country + '.tsv')    

