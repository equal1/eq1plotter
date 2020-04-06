@echo off
del *~
git pull
git add -A -f *
git commit -m "update"
git push
echo.
