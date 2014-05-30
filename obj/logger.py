import sys

def log(message):
    sys.stdout.write(message)
    sys.stdout.flush()

def flog(message, file):
    file.write(message)
    file.flush()
