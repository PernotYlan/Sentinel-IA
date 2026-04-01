#!/usr/bin/env python3

def main():
    env = open(".env", "r")
    print(env.read())


if __name__ == "__main__":
    main()