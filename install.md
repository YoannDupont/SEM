# Install SEM on Linux

## Python

### Install setuptools (should not be required anymore)

If pip is installed, run: ```pip install setuptools```

Otherwise, run: ```apt install python-setuptools```

### Install Tkinter (optional)

Run: ```apt install python3-tk```

## GCC compiler

Run: ```apt install build-essential```

# Install SEM (4.0.0 and later)

New way of installing SEM is with pip. This installation method will give you an
"empty" SEM installation, with no resources, which you will need to install.

It is recommended to use a virtual environment to install SEM, you (of course)
use an existing one. If you want, you can create a new one with the following
command:

```python3 -m venv ~/envs/semtest```

`semtest` is only used as an example, you can name it however you want. This
environment will be used in the installation procedure to keep names consistant.

Then, you need to activate it:

```source ~/envs/semtest/bin/activate```

You can then install SEM with pip:

```pip install semtagger```

You now have an empty SEM installation! To make it functional, you will need to
download some resources. For the basic french worflows, you can launch the two
following commands to have a fully functional SEM installation:

```
sem download fr/base -k resource-pack
sem download gui -k resource-pack
```

This will install two resource packs required for SEM to work on french data:

- `fr/base` will download lexica, models and worflows for french.
- `gui` will download some images used in GUI. This might get removed as they only have aesthetic purpose.

# Install SEM (before 4.0.0)

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
