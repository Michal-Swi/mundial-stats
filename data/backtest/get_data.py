import os

countries = open("./all_countries").read().strip().split('\\n')

for country in countries:
    if ' ' in country:
        country_tab = country.split(' ')
        country = '_'.join(country_tab)

    os.system('curl -O https://www.eloratings.net/' + country + '.tsv')

