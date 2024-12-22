# 3dsMaxLog2Jupyter
A simple Jupyter Kernel for interacting with the Autodesk 3dsMax command line using the Jupyter Notebook and capturing output.

一个简单的 Jupyter Kernel，用于使用 Jupyter Notebook 与 3dsMax 命令行交互并捕获输出。



![max_show1](https://raw.githubusercontent.com/PDE26jjk/misc/main/img/max_show1.gif)

## 用法

下载后，将3dsMaxKernel放到一个目录，将kernel.json里面的3dsMaxLogKernel.py改成这个目录的路径，然后在你使用Jupyter的环境里将其安装为kernel

```cmd
jupyter kernelspec install /path/to/mayaKernel
```

将jupyter_startup.py复制到 /3ds Max 2025/scripts/Startup 目录中。你可以更改INSTANCE_ID的值，以区别不同版本的3dsMax。

接着将3dsMaxKernel里面3dsMax.json里的default_port端口号可以修改，如果被占用，会+1并继续尝试，重复10次。

这样之后，在Jupyter里选择3dsMax内核，打开3dsMax软件，应该能连接到3dsMax了。输入并运行python代码，将同步在3dsMax中运行。

## 其他

为了方便使用，我设置了一些指令，在cell里面可以运行。

- 设置端口，这个指令将设置指令收发的端口，并重新启动监听

```
%setPort 4435
```

- 输入Maxscript代码，这个指令将%mxs 之后的视作Maxscript代码发送到3dsMax。

```
%mxs -- """ 
-- your code
-- """
```

- 设置实例ID，不同的ID对应不同的3dsMax软件实例，应该和Python全局变量INSTANCE_ID保持一致。

```
%setId 2025
```


PyCharm语法提示可以使用这个

- [friedererdmann/pymxs_stubs](https://github.com/friedererdmann/pymxs_stubs)

## 局限

- 只在3dsMax2025版本中测试过。

- 没有debug功能。

  

## 参考

- [制作简单的Python包装器内核](https://daobook.github.io/jupyter_client/wrapperkernels.html)

- [cb109/sublime3dsmax](https://github.com/cb109/sublime3dsmax)

# English：

## Usage

After downloading, place 3dsMaxKernel in a directory, change the path of 3dsMaxLogKernel.py in kernel.json to this directory's path, and then install it as a kernel in your Jupyter environment.

```cmd
jupyter kernelspec install /path/to/mayaKernel
```

Copy jupyter_startup.py to the /3ds Max 2025/scripts/Startup directory. You can change the value of INSTANCE_ID to distinguish between different versions of 3dsMax.

Next, you can modify the default_port number in 3dsMax.json inside 3dsMaxKernel. If the port is occupied, it will increment by 1 and continue trying, repeating this up to 10 times.

After this, select the 3dsMax kernel in Jupyter, open the 3dsMax software, and it should connect to 3dsMax. Input and run Python code, which will be executed in 3dsMax.

## Others

For convenience, I have set up some commands that can be run in the cell.

Set port, this command will set the port for sending and receiving commands and restart the listener.

```
%setPort 4435
```

Input Maxscript code, this command will treat the code after %mxs as Maxscript code to be sent to 3dsMax.

```
%mxs --"""
-- your code
-- """
```

Set instance ID, different IDs correspond to different instances of 3dsMax software and should be consistent with the Python global variable INSTANCE_ID.

```
%setId 2025
```

Grammar hints for PyCharm can use this:

[friedererdmann/pymxs_stubs](https://github.com/friedererdmann/pymxs_stubs)

## Limitations

- Tested only in 3dsMax 2025 version.

- No debug functionality.

## References

[Creating a Simple Python Wrapper Kernel](https://daobook.github.io/jupyter_client/wrapperkernels.html)

[cb109/sublime3dsmax](https://github.com/cb109/sublime3dsmax)