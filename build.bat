@echo off
echo --- DocuFlow Build Script ---

echo.
echo [1/4] Building Frontend...
cd frontend
call npm install
set VITE_API_URL=/api
call npm run build
cd ..

echo.
echo [2/4] Deploying Frontend to Static...
if not exist static mkdir static
powershell -Command "Remove-Item -Path static\assets -Recurse -Force -ErrorAction SilentlyContinue"
xcopy /E /I /Y frontend\dist static\

echo.
echo [3/4] Packaging with PyInstaller...
set PYTHON_EXE=C:\Users\User\AppData\Local\Programs\Python\Python311\python.exe
"%PYTHON_EXE%" -m pip install pyinstaller
"%PYTHON_EXE%" -m PyInstaller --name DocuFlow ^
            --onedir ^
            --clean ^
            --noconfirm ^
            --paths backend ^
            --add-data "static;static" ^
            --hidden-import "uvicorn.logging" ^
            --hidden-import "uvicorn.loops" ^
            --hidden-import "uvicorn.loops.auto" ^
            --hidden-import "uvicorn.protocols" ^
            --hidden-import "uvicorn.protocols.http" ^
            --hidden-import "uvicorn.protocols.http.auto" ^
            --hidden-import "uvicorn.protocols.websockets" ^
            --hidden-import "uvicorn.protocols.websockets.auto" ^
            --hidden-import "uvicorn.lifespan" ^
            --hidden-import "uvicorn.lifespan.on" ^
            entry_solid.py

echo.
echo [4/4] Finalizing Bundle...
if exist dist\DocuFlow\_internal\static (
    echo Moving static assets to root...
    move dist\DocuFlow\_internal\static dist\DocuFlow\static
)

echo.
echo [Build Complete]
echo The application is available in: dist\DocuFlow

