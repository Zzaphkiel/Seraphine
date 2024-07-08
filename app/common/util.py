import json
import os
import re
import winreg
from pathlib import Path

import requests
import base64
import subprocess
import psutil
import win32api

from app.common.config import cfg, VERSION
from app.common.logger import logger


TAG = "Util"


class Github:
    def __init__(self, user="Zzaphkiel", repositories="Seraphine"):
        self.githubApi = "http://api.github.com"
        self.giteeApi = "http://gitee.com/api"

        self.proxyApi = 'https://ghproxy.net'

        self.user = user
        self.repositories = repositories
        self.sess = requests.session()

    def getReleasesInfo(self):
        url = f"{self.githubApi}/repos/{self.user}/{self.repositories}/releases/latest"

        if cfg.get(cfg.enableProxy):
            proxy = {'https': cfg.get(cfg.proxyAddr)}
        else:
            proxy = None

        return self.sess.get(url, proxies=proxy).json()

    def checkUpdate(self):
        """
        检查版本更新
        @return: 有更新 -> info, 无更新 -> None
        """
        info = self.getReleasesInfo()

        ver_info = self.__get_ver_info()
        info["forbidden"] = ver_info.get("forbidden", False)

        if info.get("tag_name")[1:] != VERSION:
            return info
        return None

    def __get_ver_info(self):
        url = f'{self.githubApi}/repos/{self.user}/{self.repositories}/contents/document/ver.json'
        if cfg.get(cfg.enableProxy):
            proxy = {'https': cfg.get(cfg.proxyAddr)}
        else:
            proxy = None

        res = self.sess.get(url, proxies=proxy).json()

        json_data = json.loads(
            str(base64.b64decode(res['content']), encoding='utf-8'))

        return json_data.get(VERSION, {})

    def getNotice(self):
        url = f'{self.githubApi}/repos/{self.user}/{self.repositories}/contents/document/notice.md'

        if cfg.get(cfg.enableProxy):
            proxy = {'https': cfg.get(cfg.proxyAddr)}
        else:
            proxy = None

        res = self.sess.get(url, proxies=proxy).json()

        content = str(base64.b64decode(res['content']), encoding='utf-8')

        return {
            'sha': res['sha'],
            'content': content,
        }


github = Github()


def getLoLPathByRegistry() -> str:
    """
    从注册表获取LOL的安装路径

    ** 只能获取到国服的路径, 外服不支持 **

    无法获取时返回空串
    """
    mainKey = winreg.HKEY_CURRENT_USER
    subKey = "SOFTWARE\Tencent\LOL"
    valueName = "InstallPath"

    try:
        with winreg.OpenKey(mainKey, subKey) as k:
            installPath, _ = winreg.QueryValueEx(k, valueName)
            path = str(Path(f"{installPath}\TCLS").absolute()
                       ).replace("\\", "/")
            return f"{path[:1].upper()}{path[1:]}"
    except FileNotFoundError:
        logger.warning("reg path or val does not exist.", TAG)
    except WindowsError as e:
        logger.warning(f"occurred while reading the registry: {e}", TAG)
    except Exception as e:
        logger.exception("unknown error reading registry", e, TAG)

    return ""


def getTasklistPath():
    for path in ['tasklist',
                 'C:/Windows/System32/tasklist.exe']:
        try:
            cmd = f'{path} /FI "imagename eq LeagueClientUx.exe" /NH'
            _ = subprocess.check_output(cmd, shell=True)
            return path
        except:
            pass

    return None


def getLolClientPidSlowly():
    for process in psutil.process_iter():
        if process.name() in ['LeagueClientUx.exe', 'LeagueClientUx']:
            return process.pid

    return -1


def getLolClientPid(path):
    processes = subprocess.check_output(
        f'{path} /FI "imagename eq LeagueClientUx.exe" /NH', shell=True)

    if b'LeagueClientUx.exe' in processes:
        arr = processes.split()
        try:
            pos = arr.index(b"LeagueClientUx.exe")
            return int(arr[pos + 1])
        except ValueError:
            raise ValueError(f"Subprocess return exception: {processes}")
    else:
        return 0


def getLolClientPids(path):
    processes = subprocess.check_output(
        f'{path} /FI "imagename eq LeagueClientUx.exe" /NH', shell=True)

    pids = []

    if not b'LeagueClientUx.exe' in processes:
        return pids

    arr = processes.split()

    for i, s in enumerate(arr):
        if s == b'LeagueClientUx.exe':
            pids.append(int(arr[i + 1]))

    return pids


def getLolClientPidsSlowly():
    pids = []

    for process in psutil.process_iter():
        if process.name() in ['LeagueClientUx.exe', 'LeagueClientUx']:
            pids.append(process.pid)

    return pids


def isLolGameProcessExist(path):
    processes = subprocess.check_output(
        f'{path} /FI "imagename eq League of Legends.exe" /NH', shell=True)

    return b'League of Legends.exe' in processes


def getPortTokenServerByPidViaPsutil(pid):
    port, token, server = None, None, None

    process = psutil.Process(pid)
    cmdline = process.cmdline()

    for cmd in cmdline:

        p = cmd.find("--app-port=")
        if p != -1:
            port = cmd[11:]

        p = cmd.find("--remoting-auth-token=")
        if p != -1:
            token = cmd[22:]

        p = cmd.find("--rso_platform_id=")
        if p != -1:
            server = cmd[18:]

        if port and token and server:
            break

    return port, token, server


def getPortTokenServerByPidViaWmic():
    '''
    ### 需要管理员权限
    '''
    command = "wmic process WHERE name='LeagueClientUx.exe' GET commandline"
    output = subprocess.check_output(command, shell=True).decode("gbk")

    port = re.findall(r'--app-port=(.+?)"', output)[0]
    token = re.findall(r'--remoting-auth-token=(.+?)"', output)[0]
    server = re.findall(r'--rso_platform_id=(.+?)"', output)[0]

    return port, token, server


def getPortTokenServerByPid(pid):
    '''
    通过进程 id 获得启动命令行参数中的 port、token 以及登录服务器
    '''

    try:
        return getPortTokenServerByPidViaPsutil(pid)
    except:
        return getPortTokenServerByPidViaWmic()


def getFileProperties(fname):
    """
    读取给定文件的所有属性, 返回一个字典.

    returns : {'FixedFileInfo': {'Signature': -17890115, 'StrucVersion': 65536, 'FileVersionMS': 917513, 'FileVersionLS':
    38012988, 'ProductVersionMS': 917513, 'ProductVersionLS': 38012988, 'FileFlagsMask': 23, 'FileFlags': 0,
    'FileOS': 4, 'FileType': 1, 'FileSubtype': 0, 'FileDate': None}, 'StringFileInfo': {'Comments': None,
    'InternalName': 'League of Legends (TM) Client', 'ProductName': 'League of Legends (TM) Client', 'CompanyName':
    'Riot Games, Inc.', 'LegalCopyright': 'Copyright (C) 2009', 'ProductVersion': '14.9.580.2108', 'FileDescription':
    'League of Legends (TM) Client', 'LegalTrademarks': None, 'PrivateBuild': None, 'FileVersion': '14.9.580.2108',
    'OriginalFilename': 'League of Legends.exe', 'SpecialBuild': None}, 'FileVersion': '14.9.580.2108'}

    """

    propNames = ('Comments', 'InternalName', 'ProductName',
                 'CompanyName', 'LegalCopyright', 'ProductVersion',
                 'FileDescription', 'LegalTrademarks', 'PrivateBuild',
                 'FileVersion', 'OriginalFilename', 'SpecialBuild')

    props = {'FixedFileInfo': None,
             'StringFileInfo': None, 'FileVersion': None}

    try:
        fixedInfo = win32api.GetFileVersionInfo(fname, '\\')
        props['FixedFileInfo'] = fixedInfo
        props['FileVersion'] = "%d.%d.%d.%d" % (fixedInfo['FileVersionMS'] / 65536,
                                                fixedInfo['FileVersionMS'] % 65536, fixedInfo['FileVersionLS'] / 65536,
                                                fixedInfo['FileVersionLS'] % 65536)

        # \VarFileInfo\Translation returns list of available (language, codepage)
        # pairs that can be used to retreive string info. We are using only the first pair.
        lang, codepage = win32api.GetFileVersionInfo(
            fname, '\\VarFileInfo\\Translation')[0]

        # any other must be of the form \StringfileInfo\%04X%04X\parm_name, middle
        # two are language/codepage pair returned from above

        strInfo = {}
        for propName in propNames:
            strInfoPath = u'\\StringFileInfo\\%04X%04X\\%s' % (
                lang, codepage, propName)
            strInfo[propName] = win32api.GetFileVersionInfo(fname, strInfoPath)

        props['StringFileInfo'] = strInfo
    except:
        return {}
    else:
        return props


def getLolClientVersion():
    gamePath = cfg.get(cfg.lolFolder)[0]

    assert gamePath  # 必须有, 否则就是调用逻辑有问题 -- By Hpero4

    # 特判一下国服 -- By Hpero4
    gamePath = gamePath.replace("/TCLS", "")

    lolExe = f"{gamePath}/Game/League of Legends.exe"
    # 判断一下, 客户端特殊? 为啥会没有LOL的主程序 -- By Hpero4
    if not os.path.exists(lolExe):
        raise FileNotFoundError(lolExe)

    fileInfo = getFileProperties(lolExe).get("StringFileInfo", {})
    lolVer = fileInfo.get("ProductVersion") or fileInfo.get("FileVersion")

    assert lolVer

    # 缩短至大版本号
    return re.search(r"\d+\.\d+", lolVer).group(0)
