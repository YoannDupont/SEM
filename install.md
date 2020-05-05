# Install SEM on Linux

## Python

### Install setuptools

If pip is installed, run: ```pip install setuptools```

Otherwise, run: ```apt install python-setuptools```

### Install Tkinter (optional)

Run: ```apt install python-tk```

## GCC compiler

Run: ```apt install build-essential```

# Install SEM

## Install dependencies

Go to SEM folder and launch the command :

```pip install -r requirements.txt```

If you are not in a virtual environment, use the `--user` flag.

## Install SEM

Go to SEM folder and launch the command :

```python ./setup.py install```

If you are not in a virtual environment, use the `--user` flag.

# Install SEM on Windows

## Python

### Install python

Install python 3.7.5 or later: [python3.7.7](https://www.python.org/downloads/release/python-377/)
- [32 bits installer](https://www.python.org/ftp/python/3.7.7/python-3.7.7-webinstall.exe)
- [64 bits installer (web-based)](https://www.python.org/ftp/python/3.7.7/python-3.7.7-amd64-webinstall.exe) (recommended)

### setup tools

Setup tools should be available with python (or run ```pip install setuptools```)

## GCC compiler: MinGW64

Install MinGW64 x86_64 : https://sourceforge.net/projects/mingw-w64/files/

1. either install with the [MinGW online installer](https://sourceforge.net/projects/mingw-w64/files/Toolchains%20targetting%20Win32/Personal%20Builds/mingw-builds/installer/mingw-w64-install.exe/download) (sélectionner les thread POSIX)
    - install with architecture=x86_64 ; threads=POSIX (for Wapiti) ; exception=SEH.
2. or download [x86_64-posix-seh](https://sourceforge.net/projects/mingw-w64/files/Toolchains%20targetting%20Win64/Personal%20Builds/mingw-builds/8.1.0/threads-posix/seh/x86_64-8.1.0-release-posix-seh-rt_v6-rev0.7z/download)
    - uncompress archive in ```C:\``` to create the folder ```C:\mingw64```
    - add ```C:\mingw64\bin``` to the "Path" environment variable

To install SEM, Wapiti should compile. If compilation fails, replace line 3 of the file ${SEM_folder}/ext/wapiti/make.bat :

```set CC=gcc```

by

```set CC=x86_64-w64-mingw32-gcc.exe```

Note: to compile Wapiti on Windows, either install [POSIX threads for Windows](https://sourceforge.net/p/pthreads4w/wiki/Home/) or disable them as explained in ```ext/src/wapiti.h```

# Install SEM

## Install dependencies

Go to SEM folder and launch the command :

```pip install -r requirements.txt```

If you are not in a virtual environment, use the `--user` flag.

## Install SEM

Go to SEM folder and launch the command :

```python .\setup.py install```

# Using the python-wapiti wrapper in SEM

Simply go to [this link](https://github.com/adsva/python-wapiti) and follow the instructions. SEM will automatically use the wrapper if it is installed. You will not need to modify the configuration files.
