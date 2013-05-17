@echo off

:: This is a hackfest; please look away.

setlocal
SET PATH=C:\Python27;%PATH%
SET PATH=%PATH%;C:\Python33\Scripts

python C:\Software\Dev\asciidoc-8.6.8\asciidoc.py -a numbered -a icons -b html5 manual.asciidoc

