@echo off

echo ==========================
echo   Demarrage DataViz
echo ==========================


echo.
echo Demarrage Backend Flask...

start cmd /k "cd /d C:\Users\Admin\Documents\projets\dataviz\backend && python run.py"


timeout /t 3 >nul


echo.
echo Demarrage Frontend React...

start cmd /k "cd /d C:\Users\Admin\Documents\projets\dataviz\frontend && npm run dev"


echo.
echo DataViz est en cours de lancement...
pause