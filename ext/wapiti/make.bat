@echo off

set CC=gcc
:: if previous does not work
:: set cc=x86_64-w64-mingw32-gcc.exe
set CFLAGS=-std=c99 -W -Wall -Wextra -O3
set LIBS=-lm -lpthread

set SRC=src\*.c
set HDR=src\*.h
set EXEC=wapiti.exe

if [%1] == [] goto end
goto %1

:wapiti
echo "CC: wapiti.c --> %EXEC%"
%CC% -DNDEBUG %CFLAGS% -o %EXEC% %SRC% %LIBS%
goto end

clean:
del %EXEC%
goto end

:end
echo done
