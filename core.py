#!/usr/bin/env python3

import redis
import json
from dotenv import load_dotenv
import os

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

def connect_redis():
    load_dotenv(".env")
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
        r.ping()
        print("\033[92mConnexion Redis OK\033[00m")
        return r
    except Exception as e:
        print(f"\033[91mErreur connexion Redis: {e}\033[00m")
        exit(1)

def main():
    """
    Execution de la boucle de logique principale
    """
    check_for_environment()
    ## TODO: add a return int to check_for_environment() to handle in case of error
    connect_redis()

if __name__ == "__main__":
    main()