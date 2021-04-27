import os


while True:
    user_input = input(f"{os.getcwd()} ")
    print(os.system(user_input).__dict__)