

import os

def dd(value):
    """
    Only for debugging purposes
    :param value:
    :return:
    """
    os.system('cls' if os.name == 'nt' else 'clear')

    print("\n" + "=" * 60)
    print("DEBUG DUMP - START".center(60))
    print("=" * 60 + "\n")

    # Yellow color
    print(f"\033[93m{value}\033[0m")

    print("\n" + "=" * 60)
    print("DEBUG DUMP - END".center(60))
    print("=" * 60 + "\n")



