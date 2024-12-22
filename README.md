# 3dsMaxLog2Jupyter
A simple Jupyter Kernel for interacting with the Autodesk 3dsMax command line using the Jupyter Notebook and capturing output.

一个简单的 Jupyter Kernel，用于使用 Jupyter Notebook 与 3dsMax 命令行交互并捕获输出。

只在3dsMax2025版本中测试过。

没有debug功能。

![max_show1](https://raw.githubusercontent.com/PDE26jjk/misc/main/img/max_show1.gif)

## 用法

下载后，将3dsMaxKernel放到一个目录，将kernel.json里面的3dsMaxLogKernel.py改成这个目录的路径，然后在你使用Jupyter的环境里将其安装为kernel

```cmd
jupyter kernelspec install /path/to/mayaKernel
```

将jupyter_startup复制到 /3ds Max 2025/scripts/Startup 目录中。你可以更改INSTANCE_ID的值，以区别不同版本的3dsMax。

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


语法提示可以使用这个

- [friedererdmann/pymxs_stubs](https://github.com/friedererdmann/pymxs_stubs)

  

  ## 参考

- [制作简单的Python包装器内核](https://daobook.github.io/jupyter_client/wrapperkernels.html)
- [cb109/sublime3dsmax](https://github.com/cb109/sublime3dsmax)