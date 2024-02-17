import subprocess

bat = '''@echo off

:start

@REM 等待 Seraphine.exe 退出
tasklist | find /i "Seraphine.exe" > nul
if NOT errorlevel 1 (
    echo Seraphine is running, waiting...
    timeout /t 1 > nul
    goto start
)

@REM 删除当前目录下所有文件夹
for /d %%i in (*) do (
    rmdir "%%~fi" /s /q
)

@REM 删除当前目录下除了自己的所有文件
for %%i in (*) do (
    if NOT "%%i" equ "updater.bat" (
        del "%%i" /s /q
    )
)

@REM 将解压好的文件和文件夹拷贝到当前文件夹内
set src=%AppData%\\Seraphine\\temp

for /D %%a in (%src%\\*) do (
    move %%a .
)

for %%a in (%src%\\*) do (
    move %%a .
)

@REM 删除原来的那堆东西和自己
rmdir %src% /s /q

@REM 启动一下新版本
start /b .\Seraphine.exe

del %0
'''


def runUpdater():
    with open("updater.bat", 'w', encoding='utf-8') as f:
        f.write(bat)

    subprocess.Popen("updater.bat")
