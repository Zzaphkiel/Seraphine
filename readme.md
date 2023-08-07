<h1 align='center'>
    Seraphine
</h1>
<p align='center'>
    基于 LCU API 实现的英雄联盟战绩查询工具
</p>

<p align='center'><img src="https://github.com/Zzaphkiel/Seraphine/assets/60383222/aea50a9d-09a6-46a9-9385-377019f2d071" align="center" /></p>

## 快速上手 🤗
### 直接使用发布版本
在 [release](https://github.com/Zzaphkiel/Seraphine/releases) 中下载最新版本的压缩包后解压至本地，以管理员身份运行 `Seraphine.exe` 开始使用。
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
**以管理员身份**运行 `main.py` 开始使用
```shell
python main.py
```
## 功能一览 🥰（还在更新中）
- 战绩查询功能
  - 战绩查询，包括隐藏战绩 ✅
  - 进入 BP 后自动查队友战绩 ✅
  - 进入游戏后自动查对手战绩 ✅（暂不支持斗魂竞技场）

- 其他辅助功能
  - 找到对局后自动接收对局 ✅
  - 开局秒选英雄 ❌（还没想好要不要写）
  - 修改个人主页背景✅（可改为未拥有的皮肤）
  - 修改个人在线状态 ✅
  - 修改个人签名 ✅
  - 伪造个人状态卡片中的段位显示 ✅
  - 创建 5v5 自定义训练模式房间 ✅
  - 一键卸下勋章 ✅

- 通用功能
  - 开机自动启动 Seraphine ❌（还没想好要不要写）
  - 启动 Seraphine 时自动启动 LOL 客户端 ❌（还没想好要不要写）

## 常见问题 Q&A 🤨
### Q：为什么要必须要使用管理员身份运行 😡？

A：管理员身份**仅用于**获取 `LeagueClientUx.exe` 进程的命令行参数以调用 LCU API。

### Q：我会因为使用 Seraphine 而被封号吗 😨？

A：由于本程序的功能**完全符合**[英雄联盟游戏插件公约](https://lol.qq.com/webplat/info/news_version3/152/4579/4581/m3106/201509/381618.shtml)中对于 “**绿色功能**” 的定义，并且**完全**基于英雄联盟客户端 API 实现，**不含任何**对客户端以及游戏文件本体、代码以及内存的读取或破坏其完整性的行为。因此仅使用 Seraphine 时极大概率（99.99%）不会被封号，**并不保证**一定不会封号。

### Q：关闭程序时终端提示 `QThread` 的错误信息怎么办 🤔？

A：忽视它，它并不影响什么。~~我也不知道为什么会这样，我不会修~~😥

## 帮助我们改进 Seraphine 😘
在使用过程中，遇到程序发生任何不符合预期的行为或任何 BUG，请提出 [issue](https://github.com/Zzaphkiel/Seraphine/issues)。发布 issue 时请务必带上**环境信息**以及**复现过程**；程序报错请带上**错误信息**。

有功能上的添加 / 改进建议也欢迎提出 issue 进行讨论。


## 引用以及参考资料 👀
- GUI 基于 [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) 以及 [zhiyiYo/PyQt-Fluent-Widget](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) 实现
- 部分与 LOL 客户端的通信使用 [Willump](https://github.com/elliejs/Willump) 实现
- LCU API 使用方法以及汇总详见官方文档
  - https://riot-api-libraries.readthedocs.io/en/latest/lcu.html#lcu-explorer
  - https://www.mingweisamuel.com/lcu-schema/tool/#/

  以及其他使用 LCU API 的项目
  - https://github.com/KebsCS/KBotExt
  - https://github.com/XHXIAIEIN/LeagueCustomLobby
  - https://github.com/7rebux/league-tools

- 游戏资源获取请见
  - https://raw.communitydragon.org/latest/
  - https://github.com/CommunityDragon/Docs/blob/master/assets.md


## 许可证 ⚖️
Seraphine 使用 [GPLv3](https://github.com/Zzaphkiel/Seraphine/blob/main/LICENSE) 许可证，代码不经允许**不可商用**。
