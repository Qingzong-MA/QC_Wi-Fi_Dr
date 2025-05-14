from colorama import init, Fore
init(autoreset=True)

def print_warning(msg):
    print(Fore.YELLOW + "WARNING: {}".format(msg))