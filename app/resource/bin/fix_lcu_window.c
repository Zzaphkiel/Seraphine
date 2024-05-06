#include <windows.h>
#include <stdlib.h>

void patchDpiChangedMessage(HWND hWnd) {
    UINT dpi = GetDpiForWindow(hWnd);
    WPARAM wParam = MAKEWPARAM(dpi, dpi);
    RECT lParam;

    lParam.bottom = 0;
    lParam.top = 0;
    lParam.left = 0;
    lParam.right = 0;

    SendMessageW(hWnd, WM_DPICHANGED, wParam, (LPARAM)&lParam);
}

int main(int argc, char *argv[]) {
    if (argc == 1) {
        return 0;
    }

    HWND windowHWnd = FindWindowW(L"RCLIENT", L"League of Legends");
    HWND windowCefHWnd = FindWindowExW(windowHWnd, NULL, L"CefBrowserWindow", NULL);

    if (windowHWnd == 0 || windowCefHWnd == 0) {
        return 0;
    }

    WINDOWPLACEMENT placement;
    GetWindowPlacement(windowHWnd, &placement);

    if (placement.flags == SW_SHOWMINIMIZED) {
        return 0;
    }

    double zoom = atof(argv[1]);

    int screenWidth = GetSystemMetrics(SM_CXSCREEN);
    int screenHeight = GetSystemMetrics(SM_CYSCREEN);

    int targetWindowWidth = (int)(1280 * zoom);
    int targetWindowHeight = (int)(720 * zoom);

    patchDpiChangedMessage(windowHWnd);
    patchDpiChangedMessage(windowCefHWnd);

    SetWindowPos(windowHWnd, 0, (screenWidth - targetWindowWidth) / 2,
                 (screenHeight - targetWindowHeight) / 2, targetWindowWidth, targetWindowHeight,
                 SWP_SHOWWINDOW);
    SetWindowPos(windowCefHWnd, 0, 0, 0, targetWindowWidth, targetWindowHeight, SWP_SHOWWINDOW);

    return 0;
}
