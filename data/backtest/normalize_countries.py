import os

countries = open("./all_countries").read().strip().split('\\n')

for country in countries:
    print(country)

