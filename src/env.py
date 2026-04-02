def check_for_environment():
    """
    Verification d'existance d'environement -> Si abscent creation manuelle
    """
    try:
        with open("test", "r") as env:
            print("\033[92mConfiguration presente\033[00m\ninitialisation\n")
            print(env.read())

    except FileNotFoundError:
        print("\033[91mEnvironement non configurée\033[00m")
        with open("test", "w") as env:
            userInput = input("Enter WireGuard IP (10.0.0.1 default):\n>")
            if userInput == "":
                env.write("REDIS_HOST=10.0.0.1\n")
            else:
                env.write(f"REDIS_HOST={userInput}\n")
            userInput = input("Enter Redis Port (6379 default):\n>")
            if userInput == "":
                env.write("REDIS_PORT=6379\n")
            else:
                env.write(f"REDIS_PORT={userInput}\n")
            userInput = input("Enter Redis Password:\n>")
            env.write(f"REDIS_PASSWORD={userInput}\n")
            userInput = input("Enter Redis Key:\n>")
            env.write(f"REDIS_KEY={userInput}\n")
            userInput = input("Enter Redis Client ID:\n>")
            env.write(f"CLIENT_ID={userInput}")

        with open("test", "r") as env:
            print(f"\n{env.read()}")
    ## TODO: create a safety net for each input: eg. ip can't hold letter and such...
