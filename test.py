balance = 0
diamonds = 100
cours = 1
for i in range(diamonds):
    cours += cours / 100 * 0.01
cours = round(cours, 2)
print(cours)