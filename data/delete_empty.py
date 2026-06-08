file = open("current_countries").read().split('\n')

for line in file:
    if len(line) == 0:
        continue
    else:
        print(line)

