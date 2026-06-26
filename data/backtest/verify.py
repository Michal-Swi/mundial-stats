import os
import subprocess

countries = open("./all_countries").read().strip().split('\\n')

for country in countries:
    if ' ' in country:
        country_tab = country.split(' ')
        country = '_'.join(country_tab)

    path = country + '.tsv'
    print(country + '.tsv')

    try:
        file = subprocess.check_output(['cat', path])
        file = str(file)
    except:
        print('exception occured for: ' + country)
        file = ''

    if '<!DOCTYPE html>' in file:
        print('File not downladed correctly for country: ' + country)
