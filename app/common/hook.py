import ctypes
import sys
import time
from ctypes import wintypes
import pygetwindow as gw
import psutil
import win32con
from pyuac import main_requires_admin

# if not ctypes.windll.shell32.IsUserAnAdmin():
#     # 如果当前的 Python 进程不是以管理员权限运行，那么以管理员权限重新启动它
#     ctypes.windll.shell32.ShellExecuteW(win32con.SW_HIDE, "runas", sys.executable, __file__, None, 1)
#     sys.exit()

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
        # print("hook")
        # print(f"0x{wParam:X}")
        if wParam in [0x104, 0x100]:  # WM_KEYDOWN
            print(f"0x{vkCode:X} Down")
            keys_pressed.add(vkCode)
        elif wParam == 0x101:  # WM_KEYUP
            print(f"0x{vkCode:X} Up")
            keys_pressed.discard(vkCode)
        if 0xA4 in keys_pressed and 0x73 in keys_pressed:  # Alt and F4
        # if 0xA4 in keys_pressed and 0x74 in keys_pressed:  # Alt and F5  debug
            print('Alt and F4 keys pressed together')
            keys_pressed.discard(0xA4)
            keys_pressed.discard(0x73)  # F4
            active_window_title = gw.getActiveWindow().title
            print(active_window_title)
            if active_window_title != "League of Legends (TM) Client":
                return user32.CallNextHookEx(None, ctypes.c_int(nCode), wintypes.WPARAM(wParam), wintypes.LPARAM(lParam))

            # 检查进程是否存在并且窗口标题匹配
            print("active hit")
            for proc in psutil.process_iter():
                # print(f"{proc.name()}:::{proc.pid}")
                if proc.name() == "League of Legends.exe":
                    print("proc found")
                    time.sleep(.2)
                    proc.kill()
                    # break
                    return
    return user32.CallNextHookEx(None, ctypes.c_int(nCode), wintypes.WPARAM(wParam), wintypes.LPARAM(lParam))


LowLevelKeyboardProc = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)(
    LowLevelKeyboardProc)


@main_requires_admin
def start_hook():
    hHook = user32.SetWindowsHookExW(idHook, LowLevelKeyboardProc, None, 0)
    if not hHook:
        raise ctypes.WinError(ctypes.get_last_error())
    while user32.GetMessageW(ctypes.byref(MSG), None, 0, 0):
        user32.TranslateMessage(ctypes.byref(MSG))
        user32.DispatchMessageW(ctypes.byref(MSG))
    user32.UnhookWindowsHookEx(hHook)


if __name__ == '__main__':
    start_hook()
