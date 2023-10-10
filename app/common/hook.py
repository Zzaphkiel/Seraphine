import ctypes
import json
import os
import threading
import time
from ctypes import wintypes
import pygetwindow as gw
import psutil
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-p", "--pid", help="master process PID")

args = parser.parse_args()

user32 = ctypes.WinDLL('user32', use_last_error=True)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD),
                ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]


if not hasattr(wintypes, 'LPDWORD'):  # PY2
    wintypes.LPDWORD = ctypes.POINTER(wintypes.DWORD)

idHook = wintypes.DWORD(13)  # WH_KEYBOARD_LL
MSG = ctypes.wintypes.MSG()

keys_pressed = set()


def LowLevelKeyboardProc(nCode, wParam, lParam):
    if nCode == 0:  # HC_ACTION
        KBDLLHOOKSTRUCT_p = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT))
        vkCode = KBDLLHOOKSTRUCT_p.contents.vkCode
        if wParam in [0x104, 0x100]:  # WM_KEYDOWN
            keys_pressed.add(vkCode)
        elif wParam == 0x101:  # WM_KEYUP
            keys_pressed.discard(vkCode)
        if 0xA4 in keys_pressed and 0x73 in keys_pressed:  # Alt and F4
            keys_pressed.discard(0xA4)
            keys_pressed.discard(0x73)  # F4
            active_window_title = gw.getActiveWindow().title
            if active_window_title != "League of Legends (TM) Client":
                return user32.CallNextHookEx(None, ctypes.c_int(nCode), wintypes.WPARAM(wParam), wintypes.LPARAM(lParam))

            # 检查进程是否存在并且窗口标题匹配
            for proc in psutil.process_iter():
                if proc.name() == "League of Legends.exe":
                    proc.kill()
                    return -1
    return user32.CallNextHookEx(None, ctypes.c_int(nCode), wintypes.WPARAM(wParam), wintypes.LPARAM(lParam))


LowLevelKeyboardProc = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)(
    LowLevelKeyboardProc)


def start_hook():
    hHook = user32.SetWindowsHookExW(idHook, LowLevelKeyboardProc, None, 0)
    if not hHook:
        raise ctypes.WinError(ctypes.get_last_error())
    while user32.GetMessageW(ctypes.byref(MSG), None, 0, 0):
        user32.TranslateMessage(ctypes.byref(MSG))
        user32.DispatchMessageW(ctypes.byref(MSG))
    user32.UnhookWindowsHookEx(hHook)


if __name__ == '__main__':
    def _():
        while True:
            with open(fr"{os.getcwd()}\app\config\config.json", "r", encoding="utf-8") as f:
                js = json.loads(f.read())
                if not js.get("Functions", {}).get("ForceDisconnection"):  # 关闭了设置
                    os._exit(0)

            for proc in psutil.process_iter():
                if proc.pid == int(args.pid):
                    break
            else:
                os._exit(0)  # 随主进程退出
            time.sleep(.5)

    threading.Thread(target=_, daemon=True).start()

    start_hook()

