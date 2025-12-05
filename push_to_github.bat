@echo off
echo --- GitHub Push Helper ---
echo.
echo 1. Go to https://github.com/new and create a new EMPTY repository.
echo 2. Copy the HTTPS URL of the new repository (e.g., https://github.com/adriari4/my-repo.git).
echo.
set /p REPO_URL="Paste the Repository URL here: "

if "%REPO_URL%"=="" goto error

echo.
echo Adding remote origin...
git remote add origin %REPO_URL%

echo.
echo Renaming branch to main...
git branch -M main

echo.
echo Pushing to GitHub...
git push -u origin main

echo.
echo Done!
pause
exit /b

:error
echo Error: Repository URL cannot be empty.
pause
