# Install SEM on Linux

# Python

### Install setuptools

If pip is installed, run: ```pip install setuptools```

Otherwise, run: ```apt install python-setuptools```

### Install Tkinter (optional)

Run: ```apt install python-tk```

## GCC compiler

Run: ```apt install build-essential```

# launch SEM installer

Go to SEM folder and launch the command :

```python .\setup.py install --user```

# Install SEM on Windows

## Python

### install python

Install the most recent python 2.7 possible : [python2.7.15](https://www.python.org/downloads/release/python-2715/)
- [32 bits installer](https://www.python.org/ftp/python/2.7.15/python-2.7.15.msi)
- [64 bits installer](https://www.python.org/ftp/python/2.7.15/python-2.7.15.amd64.msi) (recommended)

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

## launch SEM installer

Go to SEM folder and launch the command :

```python .\setup.py install```
