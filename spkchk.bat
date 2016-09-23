@echo off
tasklist /FI "IMAGENAME eq espeak.exe" /FO CSV > search.log
FOR /F %%A IN (search.log) DO IF %%~zA EQU 0 GOTO false
echo 0
goto end
:false
echo 1
:end
del search.log