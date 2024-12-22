INSTANCE_ID = 2025 # You can change it.

import ctypes
import socket
import time
import pymxs

from ctypes import wintypes

try:
    from PySide6 import QtGui, QtWidgets
    QApplication = QtWidgets.QApplication
except:
    from PySide2 import QtGui, QtWidgets
    QApplication = QtWidgets.QApplication

TARGET_HWND = None
TARGET_PROCESS_ID = wintypes.DWORD()
TARGET_WINDOW_TITLE = [b"Scripting Listener", "脚本侦听器".encode('gbk')]


def _CODE_Run_Script(port, pythonCode=True):
    def getPtr(obj):
        return ctypes.c_uint64(ctypes.cast(obj, ctypes.c_void_p).value)

    user32 = ctypes.WinDLL('user32', use_last_error=True)

    EnumWindows = user32.EnumWindows
    GetWindowTextA = user32.GetWindowTextA
    GetWindowTextLengthA = user32.GetWindowTextLengthA
    GetClassNameA = user32.GetClassNameA

    EnumWindows.restype = wintypes.BOOL

    GetCurrentThreadId = ctypes.windll.kernel32.GetCurrentThreadId
    GetThreadProcessId = user32.GetWindowThreadProcessId

    def getOutputHWND():
        def get_window_title(hwnd):
            length = GetWindowTextLengthA(hwnd)
            title = ctypes.create_string_buffer(length + 1)
            GetWindowTextA(hwnd, title, length + 1)
            return title.value

        def enum_windows_callback(hwnd, _):
            global TARGET_HWND, TARGET_PROCESS_ID
            process_id = wintypes.DWORD()
            GetThreadProcessId(hwnd, ctypes.byref(process_id))
            if process_id.value != TARGET_PROCESS_ID.value:
                return True
            title = get_window_title(hwnd)
            if title in TARGET_WINDOW_TITLE:
                TARGET_HWND = hwnd
                return False
            return True

        top_level_windows = QApplication.topLevelWindows()
        qwindow_handle = top_level_windows[0]

        global TARGET_PROCESS_ID, TARGET_HWND
        TARGET_PROCESS_ID = wintypes.DWORD()
        hwnd = ctypes.cast(qwindow_handle.winId(), ctypes.POINTER(wintypes.HWND))
        GetThreadProcessId(hwnd, ctypes.byref(TARGET_PROCESS_ID))

        EnumWindows(ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(enum_windows_callback), 0)
        hwnd = TARGET_HWND
        hwnd = user32.FindWindowExA(hwnd, None, b"MXS_Scintilla", None)
        TARGET_HWND = hwnd
        if not hwnd:
            print("Output window not found.")
        return hwnd

    def getRangeText(hwnd, start, end):

        class SciCharacterRange(ctypes.Structure):
            _fields_ = [
                ("cpMin", wintypes.LONG),
                ("cpMax", wintypes.LONG)
            ]

        class SciTextRange(ctypes.Structure):
            _fields_ = [
                ("chrg", SciCharacterRange),
                ("lpstrText", ctypes.c_char_p)
            ]

        text_range = SciTextRange()
        text_range.chrg.cpMin = start
        text_range.chrg.cpMax = end

        string_length = 2 * (end - start) + 2

        text_buffer = ctypes.create_string_buffer(string_length * 2)
        text_range.lpstrText = ctypes.cast(text_buffer, ctypes.c_char_p)

        SCI_GETTEXTRANGE = 2162
        EM_GETTEXTRANGE = 0x0400 + 75
        pos = user32.SendMessageW(hwnd, SCI_GETTEXTRANGE, 0, getPtr(ctypes.pointer(text_range)))
        # print("pos{}".format(pos))
        # print("string_length{}".format(string_length))
        # print(text_buffer[:pos])
        # print(text_buffer[:pos].decode('utf-16').encode('utf-8'))
        return text_buffer[:pos]

    def getCurrentPos(hwnd):
        SCI_GETCURRENTPOS = 2008
        current_pos = user32.SendMessageW(hwnd, SCI_GETCURRENTPOS, 0, 0)
        return current_pos

    def getLength(hwnd):
        SCI_GETLENGTH = 2006
        length = user32.SendMessageW(hwnd, SCI_GETLENGTH, 0, 0)
        return length

    def sendEnter(hwnd):
        WM_CHAR = 0x0102
        VK_RETURN = 0x0D
        user32.SendMessageW(hwnd, WM_CHAR, VK_RETURN, 0)

    hwnd = TARGET_HWND
    if hwnd is None:
        hwnd = getOutputHWND()

    if hwnd is None:
        return

    def getCmdAndRun():
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', port)) 

            client.settimeout(1)
            cmd = client.recv(10240).decode('utf-8')
            startPos = getCurrentPos(hwnd)
            try:
                if pythonCode:
                    eval(cmd)
                else:
                    pymxs.runtime.Execute(cmd)

            except Exception as e:
                print(e)
            # sendEnter(hwnd)
            endPos = getCurrentPos(hwnd)
            ufmegvPos = startPos + ((endPos - startPos) - 2) * 2  # ???
            length = getLength(hwnd)
            while ufmegvPos > length:
                s = ufmegvPos - length
                print(' ' * s)
                length = getLength(hwnd)
                if ufmegvPos > length:
                    time.sleep(0.1)
            # print(length)
            # print(startPos, endPos, endPos - startPos, ufmegvPos, length)
            ufmegvPos = max(min(ufmegvPos, length), startPos)
            res = getRangeText(hwnd, startPos, ufmegvPos)
            client.send(res)

        except Exception as e:
            print(e)
        client.close()

    getCmdAndRun()

print(f"INSTANCE_ID = {INSTANCE_ID}")