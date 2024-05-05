import subprocess

bat = '''
# 等待 Seraphine.exe 退出
while ((Get-Process Seraphine -ErrorAction SilentlyContinue) -ne $null) {
    Write-Host "Seraphine is running, waiting..."
    Start-Sleep -Seconds 1
}

$fileList = Get-Content -Path "filelist.txt"

# 遍历文件列表
foreach ($file in $fileList) {
    # 检查文件或目录是否存在
    if (Test-Path -Path $file) {
        # 删除文件或目录
        Remove-Item -Path $file -Recurse -Force
        Write-Output "Removed: $file"
    } else {
        Write-Output "NotFound: $file"
    }
}

# 设置源路径
$src = "$env:AppData\\Seraphine\\temp"

# 移动目录
Get-ChildItem -Path $src -Directory | ForEach-Object {
    Move-Item -Path $_.FullName -Destination '.' -Force
}

# 移动文件
Get-ChildItem -Path $src -File | ForEach-Object {
    Move-Item -Path $_.FullName -Destination '.' -Force
}

# 删除更新解压的临时文件夹
Remove-Item -Path $src -Recurse -Force

# 启动新版本的 Seraphine.exe
Start-Process -FilePath ".\Seraphine.exe" -NoNewWindow

# 删除自身脚本文件
Remove-Item -Path $MyInvocation.MyCommand.Definition -Force

'''


def runUpdater():
    with open("updater.ps1", 'w', encoding='utf-8') as f:
        f.write(bat)

    subprocess.Popen("PowerShell.exe -ExecutionPolicy Bypass -File updater.ps1")
