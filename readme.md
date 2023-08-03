<h1 align='center'>
    Seraphine
</h1>
<p align='center'>
    基于 LCU API 实现的英雄联盟战绩查询工具
</p>

<p align='center'><img src="https://github.com/Zzaphkiel/Seraphine/assets/60383222/d3deb827-385d-4ef4-a56b-36b944f97276" align="center" /></p>

## 快速上手 🤗
下载项目 `zip` 文件解压至文件夹或通过 `git`
```shell
git clone https://github.com/Zzaphkiel/Seraphine.git
cd Seraphine
```
创建新的 Anaconda 环境
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

## 功能介绍 🥰（还在更新中）
- 战绩查询功能
  - 战绩查询，包括隐藏战绩 ✅
  - 进入 BP 后自动查队友战绩 ✅
  - 进入游戏后自动查对手战绩 ❌（快写好了）
- 其他辅助功能
  - 找到对局后自动接收对局 ✅
  - 修改个人主页背景，可改为未拥有的皮肤 ✅
  - 修改个人在线状态 ✅
  - 修改个人签名 ✅
  - 创建 5v5 自定义训练模式房间 ✅
  - 卸下勋章 ✅
- 通用功能（还没想好要不要写）
  - 开机自动启动 Seraphine ❌
  - 自动 Seraphine 自动启动客户端   ❌

## 使用它我会被封号吗 😨？
由于本程序的功能**完全**基于英雄联盟客户端 API 实现，**不含任何**对客户端以及游戏文件、代码或内存的读取或破坏其完整性的行为。

因此仅使用 Seraphine 时极大概率（99.99%）不会被封号，**不保证**一定不会封号。

## 参考 👀
- GUI 基于 [PyQt-Fluent-Widget](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) 实现
- 部分与 LCU 的通信使用 [Willump](https://github.com/elliejs/Willump) 实现
- LCU API 使用方法以及汇总详见官方文档
  - https://riot-api-libraries.readthedocs.io/en/latest/lcu.html#lcu-explorer
  - https://www.mingweisamuel.com/lcu-schema/tool/#/

  以及其他基于 LCU API 的项目
  - https://github.com/KebsCS/KBotExt
  - https://github.com/XHXIAIEIN/LeagueCustomLobby
  - https://github.com/7rebux/league-tools
- 游戏资源获取详见
  - https://raw.communitydragon.org/latest/
  - https://github.com/CommunityDragon/Docs/blob/master/assets.md


## 许可证
Seraphine 使用 [GPLv3](https://github.com/Zzaphkiel/Seraphine/blob/main/LICENSE) 许可证，代码不经允许**不可商用**。
