### 2025 / 2 / 10

进入大乱斗模式时，如果报错 `getInfoByChampionId KeyError: 'champions'`，可以通过以下步骤式解决：

1. 按 `Win + R` 打开 “开始”，
2. 输入 `%AppData%/Seraphine` 并回车前往，
3. 删除 `AramBuff.json` 文件后重启 Seraphine 。


### 2025 / 2 / 11

从旧版本升级（覆盖安装/自行编译）的用户，如果遇到弹窗报错 
```
Traceback (most recent call last):
  File "main.py", line 60, in <module>
  File "main.py", line 52, in main
  File "app\view\main_window.py", line 82, in __init__
  File "app\view\setting_interface.py", line 57, in __init__
  File "app\components\setting_cards.py", line 680, in __init__
  File "app\components\setting_cards.py", line 689, in __initWidget
KeyError: '480'
```

可以通过以下步骤式解决：

1. 按 `Win + R` 打开 “开始”，
2. 输入 `%AppData%/Seraphine` 并回车前往，
3. 编辑 `config.json` 文件，
   
找到
```
        "QueueFilter": {
            "420": [],
            "430": [],
            "440": [],
            "450": []
        },
```
修改为
```
        "QueueFilter": {
            "420": [],
            "430": [],
            "440": [],
            "450": [],
            "480": []
        },
```

4. 保存 `config.json` 文件，
5. 重启 Seraphine 。
