<p align='center'>
  <img src="https://github.com/Zzaphkiel/Seraphine/assets/60383222/78c14456-8f8e-4137-a6bc-20896c382c1a">
</p>

<p align='center'>
  基于 LCU API 实现的英雄联盟战绩查询工具
</p>

<div align="center">

  [![License](https://img.shields.io/github/license/Zzaphkiel/Seraphine?style=flat&label=License)](https://github.com/Zzaphkiel/Seraphine/blob/main/LICENSE)
  [![Forks](https://img.shields.io/github/forks/Zzaphkiel/Seraphine?style=flat&label=Forks)](https://github.com/Zzaphkiel/Seraphine/forks)
  [![Stars](https://img.shields.io/github/stars/Zzaphkiel/Seraphine?style=flat&label=Stars)](https://github.com/Zzaphkiel/Seraphine/stargazers)
  [![Downloads](https://img.shields.io/github/downloads/Zzaphkiel/Seraphine/total?style=flat&label=Downloads)](https://github.com/Zzaphkiel/Seraphine/releases)

</div>

## 快速上手 🤗
### 直接使用打包好的程序
点击[这里](https://github.com/Zzaphkiel/Seraphine/releases/latest)进入发布页面，在下方找到资源中的 `Seraphine.7z`，点击下载并解压至文件夹中，双击运行其中的 `Seraphine.exe` 即可。

### 或通过本地构建
下载项目源码 `zip` 压缩包解压至文件夹或通过 `git`
```shell
git clone https://github.com/Zzaphkiel/Seraphine.git
cd Seraphine
```
创建并激活新的 conda 环境
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
### 卸载 Seraphine 😑
删除 Seraphine 所在文件夹并删除 `%AppData%/Seraphine` 文件夹即可。

## 功能一览 （持续更新中）🥰
- 战绩查询功能（不支持云顶之弈）
  - 同大区召唤师战绩查询 ✅
  - 进入 BP 后自动查队友战绩 ✅
  - 进入游戏后自动查对手战绩 ✅

- 其他辅助功能
  - 自动 B/P 
    - 找到对局后自动接受对局 ✅
    - 进入英雄选择后自动选择英雄 ✅
    - 进入禁用环节时自动禁用英雄 ✅
    - 自动接受来自队友的交换英雄 / 楼层请求 ✅
  
  - 外部数据显示
    - 自动显示大乱斗英雄 Buff 信息 ✅
    - 自动显示 OPGG 英雄排行 ✅
    - 自动显示 OPGG 英雄出装加点，一键设置符文 ✅
      
  - 游戏功能 
    - 创建 5v5 自定义训练模式房间 ✅
    - 观战同大区玩家正在进行的游戏 ✅
    - 锁定游戏内设置 ✅
  
  - 客户端功能
    - 退出后自动重新连接 ✅
    - 修复客户端结算时无限加载和缩成一块 ✅
    - 热重启客户端 ✅

  - 个性化功能
    - 修改个人主页背景 ✅
    - 修改个人在线状态 ✅
    - 修改个人签名 ✅
    - 修改个人状态卡片中的段位显示 ✅
    - 一键卸下勋章 ✅
    - 一键卸下头像框 ✅


## 常见问题 FAQ 🧐
### Q：我会因为使用 Seraphine 而被封号吗 😨？
由于本程序的功能**完全**基于英雄联盟客户端 API 实现，**不含任何**对客户端以及游戏文件本体、代码以及内存的读取或破坏其完整性的行为（详情见下方[套盾环节](https://github.com/Zzaphkiel/Seraphine?tab=readme-ov-file#%E5%A5%97%E7%9B%BE%E7%8E%AF%E8%8A%82-%EF%B8%8F)）。因此仅使用 Seraphine 时极大概率不会被封号，但**并不保证**一定不会封号。

### Q：真的被封号了怎么办？
申诉或等待解封吧 😭

### Q：为什么客户端无法连接 / 功能无法使用 / 生涯界面无限转圈 / 最新战绩更新有延迟？
Seraphine 提供的战绩查询相关功能的数据均是由英雄联盟客户端接口所提供的，程序只是负责将它们显示出来。所以如果遇到功能无法使用或数据更新由延迟的情况，原因基本出在英雄联盟服务器本身，与 Seraphine 大概率没啥关系~

### Q：为什么不提供具体某模式 / 某英雄总场次以及总胜率？
英雄联盟客户端没有提供相关数据接口，我们做不到哇~

### Q：客户端为什么有时候会闪退？
我们怀疑客户端无法承载某些 HTTP 访问（它一碰就碎）。


## 帮助我们改进 Seraphine 😘
在您的使用过程中，如果遇到程序的任何 BUG 或不符合预期的行为，欢迎提出 [issue](https://github.com/Zzaphkiel/Seraphine/issues)。发布 issue 时请按照模板填写。**发布新 issue 前请先善用搜索功能，看看之前是否讨论过相关或类似的问题！**

如果您有功能上的添加或修改建议，也非常欢迎提出 issue 进行讨论！[PR](https://github.com/Zzaphkiel/Seraphine/pulls) 也大欢迎！

## 您也可以自己打包可执行文件 📂
在 `seraphine` 虚拟环境下安装 `Pyinstaller`，并确认环境支持 `7z` 命令
```shell
pip install pyinstaller==5.13
```
执行项目中 `make.ps1` 脚本，通过 `-dest` 参数传入目标文件夹
``` shell
.\make -dest .
```
或直接使用默认值，其为当前目录 `.`
``` shell
.\make
```
命令结束后在目标文件夹获得 `Seraphine.7z`。

## Riot 声明 📢
Seraphine is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc

**参考译文**：Seraphine 未经 Riot Games 认可，也不代表 Riot Games 或任何官方参与制作或管理 Riot Games 产品的人的观点或意见。Riot Games 及其所有相关产物均为 Riot Games，Inc 的商标或注册商标。

## 套盾环节 🛡️
本程序为在 GitHub 仓库 [Zzaphkiel/Seraphine](https://github.com/Zzaphkiel/Seraphine) 开源的代码，以及在 [Release](https://github.com/Zzaphkiel/Seraphine/releases) 或官方 QQ 群组中上传的二进制文件。本环节旨在让用户更加全面详尽地了解本程序以及可能风险，以便用户在使用本程序前及过程中做出充分的风险评估和明智的决策。

1. 本程序的目的是通过为游戏玩家提供**游戏外**辅助功能，从而给玩家提供更好的游戏体验。我们不鼓励不支持任何违反 Riot 以及腾讯规定或任何可能导致游戏环境不公平的行为。
2. 本程序的代码实现遵守 [Riot Policies](https://developer.riotgames.com/policies/general) 的规定，提供的功能符合 [《英雄联盟》游戏插件公约](https://lol.qq.com/webplat/info/news_version3/152/4579/4581/m3106/201509/381618.shtml) 的要求。
3. 本程序是基于 Riot 提供的 League Client Update（LCU）API 开发的工具，其代码与行为均不含任何侵入性的手段，因此在理论上并不会做出任何破坏客户端以及游戏完整性的行为，包括但不限于客户端文件内容的修改或游戏进程内存的读写等。
4. 我们尽力保证本程序软件本体以及使用时游戏客户端的稳定性，但尽管如此，在具体的游戏环境以及 Riot 或腾讯提供的服务更新的过程中（如反作弊系统或其他保护手段的更新），使用本程序可能会对您的游戏体验产生负面影响，如客户端崩溃（[#158](https://github.com/Zzaphkiel/Seraphine/issues/158)）、账号封禁（[#408](https://github.com/Zzaphkiel/Seraphine/issues/408#issuecomment-2185788008)）等。
5. 使用本程序所产生的一切后果将由您自行承担，我们不对因使用本程序而产生的任何直接或间接损失负责，用户在决定使用本程序时，应充分考虑并自行承担由此产生的所有风险和后果。
6. 我们保留随时修改本免责声明的权利，请定期查阅此页面以获取最新信息。

在您使用本程序之前，请确保您已经详细**阅读**、**理解**并**同意**免责声明中的条款；同时，请遵守相关游戏规则，共同维护健康和公平的游戏环境。

## 参考资料 👀
- GUI 基于 [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) 以及 [zhiyiYo/PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) 实现

- LCU API 使用方法以及汇总详见官方文档
  - https://riot-api-libraries.readthedocs.io/en/latest/lcu.html#lcu-explorer
  - https://hextechdocs.dev/tag/lcu/
  - https://developer.riotgames.com/docs/lol
  - https://www.mingweisamuel.com/lcu-schema/tool/#/

  以及其他使用 LCU API 的优秀项目
  - https://github.com/KebsCS/KBotExt
  - https://github.com/XHXIAIEIN/LeagueCustomLobby
  - https://github.com/7rebux/league-tools

- 锁定游戏设置相关请见
  - https://www.bilibili.com/video/BV1s84y1x7ub

  修复客户端无限转圈 / 缩成一块 BUG 请见
  - https://www.bilibili.com/video/BV1Cw41147iS
  - https://github.com/LeagueTavern/fix-lcu-window


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

## 致谢 🥳
- 感谢所有贡献者对 Seraphine 的开发与维护提供的巨大帮助。
  <p align='center'>
    <a href="https://github.com/Zzaphkiel/Seraphine/graphs/contributors">
      <img src="https://contrib.rocks/image?repo=Zzaphkiel/Seraphine">
    </a>
  </p>
- 感谢 [大乱斗之家](jddld.com) 为我们提供大乱斗 Buff 信息服务支持。
- 感谢 [JetBrains](https://www.jetbrains.com.cn/) 为我们提供的免费许可证。
  
  Particularly, thanks to [JetBrains](https://www.jetbrains.com.cn/) for the free [PyCharm](https://www.jetbrains.com.cn/pycharm/) license.
  
  <p align='center'>
    <a href="https://www.jetbrains.com.cn/pycharm/">
      <img src="https://github.com/Zzaphkiel/Seraphine/assets/60383222/cb3abddc-de4d-4198-8eb7-daaf03a6287a">
    </a>
    PyCharm：适用于数据科学和 Web 开发的 Python IDE
  </p>


## 交流群
- Seraphine 交流群（QQ）：[926719775](https://qm.qq.com/cgi-bin/qm/qr?k=ulYfeMNL-GrYzemJyjOq7K1y4YSasBPL&jump_from=webapi&authKey=6Nw8v3gCSswJ6HtoMlqTs2+/nS5llSOgVIs/Hh2Xm0yzNZ0yEIDjvYQqbdjF4wbb)（已满，随缘进群），入群口令：enihpareS
  

## 许可证 ⚖️
- 对于非商用行为，Seraphine 使用 [GPLv3](https://github.com/Zzaphkiel/Seraphine/blob/main/LICENSE) 许可证。
- 禁止一切针对代码以及二进制文件的商用行为。
