# Zinio Media Processor - Comprehensive Windows Setup & Compilation Script
$ErrorActionPreference = "Stop"

# Ensure UTF-8 Console Output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Zinio Media Processor Setup & Compilation" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# ---------------------------------------------------------
# 1. Python Check & Installation
# ---------------------------------------------------------
$PythonVersionNeeded = "3.12"
$PythonInstalled = $false

try {
    $pyVersionOut = & python --version 2>&1
    if ($pyVersionOut -like "*Python*") {
        Write-Host "Found existing Python: $pyVersionOut" -ForegroundColor Green
        $PythonInstalled = $true
    }
} catch {
    Write-Host "Python is not currently in the PATH." -ForegroundColor Yellow
}

if (-not $PythonInstalled) {
    # Check if python is installed in local appdata (often not in PATH if installed without prepend option)
    $localPythonPath = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    if (Test-Path $localPythonPath) {
        Write-Host "Detected Python installed at local path: $localPythonPath" -ForegroundColor Green
        $env:PATH = "$env:LOCALAPPDATA\Programs\Python\Python312\;" + "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts\;" + $env:PATH
        $PythonInstalled = $true
    }
}

if (-not $PythonInstalled) {
    Write-Host "Python is not detected. Downloading Python 3.12.4 Installer..." -ForegroundColor Yellow
    $PythonUrl = "https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"
    $InstallerPath = "$env:TEMP\python-3.12.4-amd64.exe"
    
    Write-Host "Downloading from $PythonUrl..."
    Invoke-WebRequest -Uri $PythonUrl -OutFile $InstallerPath
    
    Write-Host "Running Python installation silently (User-only, PrependPath)..." -ForegroundColor Yellow
    # InstallAllUsers=0 (Install for current user only, no admin needed), PrependPath=1 (Add Python to PATH)
    $process = Start-Process -FilePath $InstallerPath -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 AssociateFiles=1 Shortcuts=1" -Wait -PassThru
    
    # Reload path environment variables
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    # Fallback path modification in session if prepend-path was delayed
    $localPythonDir = "$env:LOCALAPPDATA\Programs\Python\Python312"
    if (Test-Path $localPythonDir) {
        $env:PATH = "$localPythonDir\;" + "$localPythonDir\Scripts\;" + $env:PATH
    }
    
    try {
        $pyVersionOut = & python --version 2>&1
        if ($pyVersionOut -like "*Python*") {
            Write-Host "Successfully installed and verified Python: $pyVersionOut" -ForegroundColor Green
        } else {
            throw "Python installation verified check failed."
        }
    } catch {
        Write-Host "Error: Python could not be automatically set up in this session PATH." -ForegroundColor Red
        Write-Host "Please download Python manually from python.org, install it with 'Add python.exe to PATH' checked, and rerun this script." -ForegroundColor Yellow
        exit 1
    }
}

# ---------------------------------------------------------
# 2. FFmpeg Check & Installation
# ---------------------------------------------------------
$FFmpegInstalled = $false
try {
    $ffmpegOut = & ffmpeg -version 2>&1
    if ($ffmpegOut -like "*ffmpeg version*") {
        Write-Host "Found existing FFmpeg install." -ForegroundColor Green
        $FFmpegInstalled = $true
    }
} catch {
    Write-Host "FFmpeg not detected in PATH." -ForegroundColor Yellow
}

if (-not $FFmpegInstalled) {
    # Check common local target directory
    $ffmpegDir = "$env:USERPROFILE\ffmpeg"
    if (Test-Path "$ffmpegDir\bin\ffmpeg.exe") {
        Write-Host "Detected FFmpeg locally at: $ffmpegDir" -ForegroundColor Green
        $env:PATH = "$ffmpegDir\bin;" + $env:PATH
        $FFmpegInstalled = $true
    }
}

if (-not $FFmpegInstalled) {
    Write-Host "Downloading FFmpeg Static Essentials Build..." -ForegroundColor Yellow
    $ffmpegUrl = "https://github.com/GyanD/codexffmpeg/releases/download/7.0.1/ffmpeg-7.0.1-essentials_build.zip"
    $ffmpegZip = "$env:TEMP\ffmpeg.zip"
    
    Write-Host "Downloading from $ffmpegUrl..."
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $ffmpegZip
    
    Write-Host "Extracting FFmpeg..." -ForegroundColor Yellow
    $extractDir = "$env:TEMP\ffmpeg-temp"
    if (Test-Path $extractDir) { Remove-Item -Recurve -Force $extractDir }
    
    Expand-Archive -Path $ffmpegZip -DestinationPath $extractDir
    
    # Locate the inner directory
    $innerDir = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
    
    if ($innerDir) {
        $destinationDir = "$env:USERPROFILE\ffmpeg"
        if (Test-Path $destinationDir) { Remove-Item -Recurve -Force $destinationDir }
        
        Move-Item -Path $innerDir.FullName -Destination $destinationDir
        Write-Host "FFmpeg moved to: $destinationDir" -ForegroundColor Green
        
        # Add to session PATH
        $env:PATH = "$destinationDir\bin;" + $env:PATH
        
        # Permanently add to User PATH
        $currentUserPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
        if ($currentUserPath -notlike "*ffmpeg\bin*") {
            [System.Environment]::SetEnvironmentVariable("Path", $currentUserPath + ";$destinationDir\bin", "User")
            Write-Host "FFmpeg bin added to User Environment PATH." -ForegroundColor Green
        }
        $FFmpegInstalled = $true
    } else {
        Write-Host "Failed to extract/locate FFmpeg build. Please install FFmpeg manually." -ForegroundColor Red
        exit 1
    }
}

# ---------------------------------------------------------
# 3. Virtual Environment Setup
# ---------------------------------------------------------
Write-Host "Setting up Python Virtual Environment..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    & python -m venv .venv
    Write-Host "Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "Virtual environment (.venv) already exists." -ForegroundColor Green
}

Write-Host "Upgrading pip and installing requirements..." -ForegroundColor Cyan
& .venv\Scripts\python.exe -m pip install --upgrade pip
& .venv\Scripts\pip.exe install -r requirements.txt

# ---------------------------------------------------------
# 4. Compilation with PyInstaller
# ---------------------------------------------------------
Write-Host "Compiling Zinio Media Processor executable..." -ForegroundColor Cyan
if (Test-Path "zinio_processor.spec") {
    & .venv\Scripts\pyinstaller.exe --clean zinio_processor.spec
} else {
    Write-Host "Spec file not found, building using manual arguments..." -ForegroundColor Yellow
    & .venv\Scripts\pyinstaller.exe --onefile --windowed --name "ZinioMediaProcessor" --icon "icon_concept1.ico" src/main.py
}

$exePath = "dist\ZinioMediaProcessor.exe"
if (Test-Path $exePath) {
    Write-Host "Compilation completed successfully: $exePath" -ForegroundColor Green
} else {
    Write-Host "Error: Executable failed to generate." -ForegroundColor Red
    exit 1
}

# ---------------------------------------------------------
# 5. Create Desktop Shortcut
# ---------------------------------------------------------
Write-Host "Creating Desktop Shortcut..." -ForegroundColor Cyan
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $DesktopPath = [System.Environment]::GetFolderPath("Desktop")
    $Shortcut = $WshShell.CreateShortcut("$DesktopPath\Zinio Media Processor.lnk")
    
    $fullExePath = Resolve-Path $exePath
    $Shortcut.TargetPath = $fullExePath.Path
    $Shortcut.WorkingDirectory = Split-Path $fullExePath.Path
    
    if (Test-Path "icon_concept1.ico") {
        $iconFullPath = Resolve-Path "icon_concept1.ico"
        $Shortcut.IconLocation = "$($iconFullPath.Path), 0"
    }
    
    $Shortcut.Save()
    Write-Host "Desktop shortcut created successfully!" -ForegroundColor Green
} catch {
    Write-Host "Warning: Could not create desktop shortcut automatically." -ForegroundColor Yellow
}

Write-Host "=============================================" -ForegroundColor Green
Write-Host "  Installation and Compilation complete!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
