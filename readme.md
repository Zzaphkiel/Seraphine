<h1 align='center'>
  Seraphine
</h1>

<p align='center'>
  基于 LCU API 实现的英雄联盟战绩查询工具
</p>

<p align='center'>
  <a href="https://github.com/Zzaphkiel/Seraphine/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Zzaphkiel/Seraphine?style=flat&label=License">
  </a>
  <a href="https://github.com/Zzaphkiel/Seraphine/forks">
    <img src="https://img.shields.io/github/forks/Zzaphkiel/Seraphine?style=flat&label=Forks">
  </a>
  <a href="https://github.com/Zzaphkiel/Seraphine/stargazers">
    <img src="https://img.shields.io/github/stars/Zzaphkiel/Seraphine?style=flat&label=Stars">
  </a>
  <a href="https://github.com/Zzaphkiel/Seraphine/releases">
    <img src="https://img.shields.io/github/downloads/Zzaphkiel/Seraphine/total?style=flat&label=Downloads">
  </a>
</p>

<p align='center'>
  <img src="https://github.com/Zzaphkiel/Seraphine/assets/60383222/2c053134-25e1-4a1b-aa9c-4f77cf9522f2">
</p>

## 快速上手 🤗
### 直接使用打包好的程序
在 [release](https://github.com/Zzaphkiel/Seraphine/releases/latest) 中下载最新版本的压缩包后解压，运行文件夹内 `Seraphine.exe` 开始使用。

**请您暂时关闭 “在游戏进行时最小化 Seraphine 窗口” 功能，该功能可能会引起程序崩溃，针对其的修复随下版本上线**

### 或通过本地构建
下载项目 `zip` 压缩包解压至文件夹或通过 `git`
```shell
cd Seraphine
git clone https://github.com/Zzaphkiel/Seraphine.git
```
创建并激活新的 Anaconda 环境
```shell
conda create -n seraphine python=3.8
conda activate seraphine
```
安装依赖
```shell
pip install -r requirements.txt
```
运行 `main.py` 开始使用
```shell
python main.py
```

## 功能一览 （持续更新中）🥰
- 战绩查询功能（不支持云顶之弈）
  - 同大区召唤师战绩查询 ✅
  - 进入 BP 后自动查队友战绩 ✅
  - 进入游戏后自动查对手战绩 ✅

- 其他辅助功能
  - 游戏功能 
    - 找到对局后自动接受对局 ✅
    - 进入英雄选择后自动选择英雄 ✅
    - 创建 5v5 自定义训练模式房间 ✅
    - 观战同大区玩家正在进行的游戏 ✅
    - 锁定游戏内设置 ✅

  - 个性化功能
    - 修改个人主页背景 ✅
    - 修改个人在线状态 ✅
    - 修改个人签名 ✅
    - 伪造个人状态卡片中的段位显示 ✅
    - 一键卸下勋章 ✅


## 常见问题 FAQ 🧐
### Q：我会因为使用 Seraphine 而被封号吗 😨？
由于本程序的功能**完全**基于英雄联盟客户端 API 实现，**不含任何**对客户端以及游戏文件本体、代码以及内存的读取或破坏其完整性的行为。因此仅使用 Seraphine 时极大概率（99.99%）不会被封号，但**并不保证**一定不会封号。

### Q：为什么客户端无法连接 / 功能无法使用 / 生涯界面无限转圈 / 最新战绩更新有延迟？
Seraphine 提供的战绩查询相关功能的数据均是由英雄联盟客户端接口所提供的，程序只是负责将它们显示出来。所以如果遇到功能无法使用或数据更新由延迟的情况，原因基本出在英雄联盟服务器本身，与 Seraphine 大概率没啥关系~

### Q：从本地直接运行代码报错怎么办？
换 Python `3.8` 试试。

### Q：为什么不提供具体某模式 / 某英雄总场次以及总胜率？
英雄联盟客户端没有提供相关数据接口，我们做不到哇~


## 帮助我们改进 Seraphine 😘
在您的使用过程中，如果遇到程序的任何 BUG 或不符合预期的行为，欢迎提出 [issue](https://github.com/Zzaphkiel/Seraphine/issues)。发布 issue 时请务必带上**环境信息**（如 Python、Seraphine 版本等），以及问题的**复现过程**；若程序报错请带上**错误信息**。

如果您有功能上的添加或修改建议，也非常欢迎提出 issue 进行讨论！[PR](https://github.com/Zzaphkiel/Seraphine/pulls) 也大欢迎！

**发布新 issue 前先善用搜索功能，请看看之前是否讨论过相关或类似的问题！** _因开学太忙，后续的功能更新、BUG 修复以及 issue 回复的速度将显著变慢，还请谅解。_

## 您也可以自己打包可执行文件 📂
在 `seraphine` 虚拟环境下安装 `Pyinstaller`
```shell
pip install pyinstaller
```
执行项目中 `make.ps1` 脚本，通过 `-dest` 参数传入目标文件夹
``` shell
.\make -dest .
```
或直接使用默认值，其为当前目录 `.`
``` shell
.\make
```
命令结束后在目标文件夹获得 `Seraphine.zip`。


## 引用以及参考资料 👀
- GUI 基于 [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) 以及 [zhiyiYo/PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) 实现
- 部分与 LOL 客户端的通信使用 [Willump](https://github.com/elliejs/Willump) 实现
- LCU API 使用方法以及汇总详见官方文档
  - https://riot-api-libraries.readthedocs.io/en/latest/lcu.html#lcu-explorer
  - https://developer.riotgames.com/docs/lol
  - https://www.mingweisamuel.com/lcu-schema/tool/#/

  以及其他使用 LCU API 的项目
  - https://github.com/KebsCS/KBotExt
  - https://github.com/XHXIAIEIN/LeagueCustomLobby
  - https://github.com/7rebux/league-tools

- 游戏资源获取请见
  - https://raw.communitydragon.org/latest/
  - https://github.com/CommunityDragon/Docs/blob/master/assets.md

- Fluent Icons 资源获取请见
  - https://fluenticons.co/outlined
  - https://github.com/microsoft/fluentui-system-icons/blob/main/icons_regular.md



## 点个 Star 支持我们 ⭐
<p align='center'>
  <a href="https://github.com/Zzaphkiel/Seraphine/stargazers">
    <img src="https://api.star-history.com/svg?repos=Zzaphkiel/Seraphine&type=Date">
  </a>
</p>

## 感谢所有贡献者 🥳！
<p align='center'>
  <a href="https://github.com/Zzaphkiel/Seraphine/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=Zzaphkiel/Seraphine">
  </a>
</p>

## 免责声明
Seraphine is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc

## 许可证 ⚖️
Seraphine 使用 [GPLv3](https://github.com/Zzaphkiel/Seraphine/blob/main/LICENSE) 许可证，**源代码**以及二**进制文件不可商用**。宣传或转载时请带上[本页链接](https://github.com/Zzaphkiel/Seraphine)。
