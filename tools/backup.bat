@echo off

REM Change to the parent of the script directory
cd /d %~dp0..

REM Check if rclone is installed
where rclone >nul 2>&1
if %errorlevel% equ 0 goto installed

echo Rclone is not installed. Should it be automatically installed now?
set /p choice="y/n> "
if /i "%choice%"=="y" goto install

echo Please install rclone manually and run this script again.
exit /b 0

:install
echo Installing rclone ...
winget install --id Rclone.Rclone 
echo Installation complete, please restart your shell and run this script again.
exit /b 0

:installed

REM Check IP address
echo Enter the Raspi IP address or proceed with '192.168.25.4' by pressing Enter
set /p ip_address="> "
if "%ip_address%" neq "" goto custom_ip

set ip_address=192.168.25.4

:custom_ip

REM Check SSH username
echo Enter the SSH username or proceed with 'maker' by pressing Enter
set /p ssh_username="> "
if "%ssh_username%" neq "" goto custom_username

set ssh_username=maker

:custom_username

REM Get ssh password
echo Enter your ssh password:
set /p ssh_password="> "

REM Obscure password
rclone obscure %ssh_password%
for /f "tokens=*" %%A in ('rclone obscure %ssh_password%') do set obscured_password=%%A

REM Make dir for backup
mkdir data

REM Backup sensor data
echo Copy %ssh_username%@%ip_address%:/home/maker/SpaceBalloon/data/sensor to ./data/sensor
rclone -P copy :sftp:home/maker/SpaceBalloon/data/sensor ./data/sensor --sftp-host %ip_address% --sftp-user %ssh_username% --sftp-pass %obscured_password% --contimeout 15s

REM Backup photo data
echo Copy %ssh_username%@%ip_address%:/home/maker/SpaceBalloon/data/video to ./data/video (photo only)
rclone -P --ignore-existing copy :sftp:home/maker/SpaceBalloon/data/video ./data/video --sftp-host %ip_address% --sftp-user %ssh_username% --sftp-pass %obscured_password% --include "*.jpg" --contimeout 15s

REM Backup video data
echo Copy %ssh_username%@%ip_address%:/home/maker/SpaceBalloon/data/video to ./data/video (video only)
rclone -P --ignore-existing copy :sftp:home/maker/SpaceBalloon/data/video ./data/video --sftp-host %ip_address% --sftp-user %ssh_username% --sftp-pass %obscured_password% --include "*.mp4" --contimeout 15s
