
TARGET_WINDOW_TITLE = [b"Scripting Listener", "脚本侦听器".encode('gbk')]

ShowRedState = True
MXSErrStartText = '-- 匿名 codeblock;'
# MXSErrStartText = "-- Error occurred"

import json
import socket
import threading
import time
import re
import pathlib

from ipykernel.kernelbase import Kernel

def get_temp_file_path(port):
    this_file_path = pathlib.Path(__file__)
    temp_name = this_file_path.parent.joinpath(f"temp_{port}.txt")
    return temp_name


def get_max_config():
    this_file_path = pathlib.Path(__file__)
    json_path = this_file_path.parent.joinpath("3dsMax.json")
    config_dict = None
    with json_path.open("r") as f:
        config_dict = json.load(f)

    print(config_dict)
    return config_dict


def get_port_number(port_str):
    try:
        port_num = int(port_str)

        if 1 <= port_num <= 65535:
            return port_num
        else:
            return None
    except ValueError:
        return None


class MaxCodeSenderServer:

    def __init__(self, port=4439):
        self.lock = threading.Lock()  # 用于线程安全管理
        self.port = port
        self.server_thread = None
        self.server_running = False
        self.server_socket = None
        self.canGetResult = threading.Event()
        self.canGetResult.set()
        self.code = ""
        self.res = ""

    def release(self):
        self.stop_server()

    def __del__(self):
        if self.server_thread is not None and self.server_running:
            self.stop_server()

    def handle_client(self, client_socket):
        try:
            self.canGetResult.clear()
            client_socket.send(f"{self.code}".encode('utf-8'))
            full_request = client_socket.recv(1024 * 100)  # 接收数据
            self.res = full_request.decode('utf-16')
            self.canGetResult.set()

            print(f"Received: {self.res}")
            # print(f"bytes: {full_request}")

        except Exception as e:
            print(f"Error: {e}")
        client_socket.close()

    def get_result(self):
        if not self.canGetResult.is_set():
            self.canGetResult.wait()
        return self.res

    def set_code_to_send(self, code):
        self.code = code

    def start_server(self, num_attempts=10):
        port = self.port
        for attempt in range(num_attempts):
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.server_socket.bind(('0.0.0.0', port))
                self.server_socket.listen(5)
                print(f"[*] Listening on port {port}...")
                self.server_running = True
                self.port = port
                break
            except Exception as e:
                print(f"Port {port} is occupied, error message: {e}")
                port += 1
                self.server_running = False
                self.server_socket = None

        while self.server_running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_handler.start()
            except Exception as e:
                print(f"Server error: {e}")
                break

    def stop_server(self):
        with self.lock:
            if self.server_running:
                self.server_running = False
                if self.server_socket:
                    self.server_socket.close()
                print("Server stopped.")
            else:
                print("Server is not running.")

    def restart_server(self):
        self.stop_server()
        time.sleep(1)
        if self.server_thread is not None:
            self.server_thread.join()
        self.run_in_thread()

    def run_in_thread(self):
        with self.lock:
            if self.server_running:
                print("Server is already running. Please stop it before restarting.")
                return
            self.server_thread = threading.Thread(target=self.start_server)
            self.server_thread.start()


class MaxKernel(Kernel):
    implementation = '3dsMax'
    implementation_version = '1.0'
    language = 'python'
    # language_version = '0.1'
    language_info = {
        'name': '3dsMax Python',
        'mimetype': 'text/x-python',
        'file_extension': '.py',
        'version': '0.1'
    }
    debugger = False,
    banner = "3dsMax kernel"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config_dict = get_max_config()
        self.tamp_file = None
        self.lock = threading.Lock()
        self.max_id = -1
        self.inputHWND = None
        self.max_server: MaxCodeSenderServer = None
        if "default_port" in config_dict:
            self.setPort(int(config_dict['default_port']))
        if "default_id" in config_dict:
            self.max_id = int(config_dict['default_id'])

    def setPort(self, port):
        if port == -1:
            return
        if self.max_server is not None:
            self.max_server.release()
        self.max_server = MaxCodeSenderServer(port)
        self.max_server.run_in_thread()

    def send_err_response(self, text):
        stream_content = {'name': 'stderr', 'text': text}
        self.send_response(self.iopub_socket, 'stream', stream_content)

    def send_response_text(self, text):
        stream_content = {'name': 'stdout', 'text': text}
        self.send_response(self.iopub_socket, 'stream', stream_content)

    def run_script_directly(self, hwnd, code, pythonCode=True):
        with self.lock:
            self.max_server.res = ""
            self.max_server.set_code_to_send(code)
            executePython(hwnd, f'_CODE_Run_Script({self.max_server.port},{str(pythonCode)})')
            result = self.max_server.get_result()
            wait_times = [0.01, 0.1, 0.15]
            i = 0
            while result == "":
                time.sleep(wait_times[i])
                result = self.max_server.get_result()
                if i >= len(wait_times) - 1:
                    break
                i += 1
        return result

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False, *, cell_id=None, ):

        # if len(code.strip()) <= 0:
        #     return {'status': 'ok', 'execution_count': self.execution_count}
        pythonCode = True

        ErrRet = {'status': 'error',
                  'execution_count': self.execution_count,
                  }
        OkRet = {'status': 'ok',
                 'execution_count': self.execution_count,
                 'payload': [],
                 'user_expressions': {},
                 }

        if not code.strip():
            return OkRet  # Empty instruction returns directly

        # % 指令处理
        if code.startswith('%'):
            parts = code.split(maxsplit=1)
            if len(parts) > 1:
                command = parts[0][1:]
                args = parts[1].strip()
            else:
                command = parts[0][1:]
                args = ''

            if command == 'mxs':
                code = args
                pythonCode = False
            elif command == 'setPort':
                port = get_port_number(args.split(maxsplit=1)[0])
                if port is not None:
                    self.setPort(port)
                    return OkRet
                else:
                    self.send_err_response("{} is not a valid port".format(args))
                    return ErrRet
            elif command == 'setId':
                _id = args.split(maxsplit=1)[0]
                if _id is not None:
                    self.max_id = _id
                    self.inputHWND = None
                    return OkRet
                else:
                    self.send_err_response("{} is not a valid id".format(args))
                    return ErrRet
            else:
                self.send_err_response("{} is not a valid command".format(command))
                return ErrRet

        if not silent:

            if not self.max_server.server_running:
                self.max_server.run_in_thread()
                self.send_err_response(f"The server is starting up...")
                return ErrRet

            instance_size = 0
            if self.inputHWND is None or not user32.IsWindow(self.inputHWND):
                hwnds = getScintillaInputList()
                instance_size = len(hwnds)
                for hwnd in hwnds:
                    _id = self.run_script_directly(hwnd, "print(INSTANCE_ID)")
                    if _id.strip() == str(self.max_id):
                        self.inputHWND = hwnd
                        break
            if self.inputHWND is None:
                self.send_err_response(
                    f"No 3dsMax instance set INSTANCE_ID to {self.max_id}, instance size is {instance_size}.")
                return ErrRet

            result = None
            try:
                with self.lock:
                    self.tamp_file = get_temp_file_path(self.max_server.port)
                    with open(self.tamp_file, 'w', encoding='utf-8') as file:
                        file.write(code)
                file_path = self.tamp_file.as_posix()
                if pythonCode:
                    cmd = f'Python.ExecuteFile "{file_path}"'
                else:
                    cmd = f'executeScriptFile  "{file_path}"'
                result = self.run_script_directly(self.inputHWND, cmd, False)

            except KeyboardInterrupt as e:
                self.send_err_response(f"KeyboardInterrupt got, but code in 3dsMax is still running")
                return ErrRet
            except BaseException as e:
                # self.log.debug(e)
                self.send_err_response(e.__str__())
                return ErrRet
            finally:
                pass

            if result is not None and result != "":
                result_splitlines = result.splitlines()
                if ShowRedState:
                    if pythonCode:
                        for i, line in enumerate(result_splitlines):
                            if line == 'MAXScript exception raised.':
                                okText = '\n'.join(result_splitlines[:i])
                                if okText:
                                    self.send_response_text(okText)
                                errText = '\n'.join(result_splitlines[i:])
                                self.send_err_response(errText)
                                return ErrRet
                    else:
                        for i, line in enumerate(result_splitlines):
                            if line.startswith(MXSErrStartText):
                                okText = '\n'.join(result_splitlines[:i])
                                if okText:
                                    self.send_response_text(okText)
                                errText = '\n'.join(result_splitlines[i:])
                                self.send_err_response(errText)
                                return ErrRet

                self.send_response_text(result)

        return OkRet

    def do_shutdown(self, restart):
        if self.max_server is not None:
            self.max_server.release()
        return {"status": "ok", "restart": restart}


import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)


def getPtr(obj):
    return ctypes.c_uint64(ctypes.cast(obj, ctypes.c_void_p).value)


def executePython(inputHWND, cmd):
    WM_SETTEXT = 0x000C
    WM_CHAR = 0x0102
    VK_SEPARATOR = 108
    data = 'python.Execute("{}")\n'.format(cmd).encode("utf-8")
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    VK_RETURN = 0x0D
    user32.SendMessageA(inputHWND, WM_SETTEXT, 0, getPtr(data))
    user32.SendMessageA(inputHWND, WM_CHAR, VK_RETURN, 0)


EnumWindows = user32.EnumWindows
GetWindowTextA = user32.GetWindowTextA
GetWindowTextLengthA = user32.GetWindowTextLengthA
GetClassNameA = user32.GetClassNameA

# 设置调用参数和返回类型
EnumWindows.restype = wintypes.BOOL

GetCurrentThreadId = ctypes.windll.kernel32.GetCurrentThreadId
GetThreadProcessId = user32.GetWindowThreadProcessId


def getScintillaInputList():
    def get_window_title(hwnd):
        length = GetWindowTextLengthA(hwnd)
        title = ctypes.create_string_buffer(length + 1)
        GetWindowTextA(hwnd, title, length + 1)
        return title.value

    def enum_windows_callback(hwnd, _):
        global TARGET_HWND_LIST
        title = get_window_title(hwnd)
        if title in TARGET_WINDOW_TITLE:
            TARGET_HWND_LIST.append(hwnd)
        return True

    hwnd = None
    global TARGET_WINDOW_TITLE
    global TARGET_HWND_LIST
    global TARGET_PROCESS_ID
    TARGET_HWND_LIST = []
    TARGET_PROCESS_ID = wintypes.DWORD()

    GetThreadProcessId(hwnd, ctypes.byref(TARGET_PROCESS_ID))
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

    child_windows = []

    # 回调函数
    def enum_child_proc(hwnd, lParam):
        classname = ctypes.create_string_buffer(256)
        user32.GetClassNameA(hwnd, classname, 256)
        if b'Scintilla' in classname.value:
            child_windows.append(hwnd)
        return True

    res = []
    for hwnd in TARGET_HWND_LIST:
        user32.EnumChildWindows(hwnd, WNDENUMPROC(enum_child_proc), 0)
        if len(child_windows) >= 2:
            inputHWND = child_windows[1]
            # outputHWND = child_windows[0]
            res.append(inputHWND)
    return res


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=MaxKernel)
