#Linux下浏览压缩文件内图片的小工具

###特点：
* 支持zip和rar文件
* 可将带图片的文件夹作为压缩包浏览 **_NEW_**
* 对zip中的中日文有良好支持
* 可保存压缩文件的密码，并支持设置多个默认密码
* 支持幻灯片播放
* 可随机打乱图片顺序、跳转到随机文件 **_NEW_**
* 以文件夹为源，快速切换压缩文件
* 文件解压于内存中，减少磁盘使用
* 多线程预载入，提升图片显示速度
* 独立线程载入图片，提升响应速度    
* 特有排序规则，正确排序文件名常见的"a1"<"a10"<"a2"问题 **_NEW_**

###缺点：
* 对zip文件的效率较低
* 没有文件列表浏览界面
* 尚未加入文件预载入，在跳转文件时对无图片文件、大文件载入和进行默认密码测试会耗去较多时间(检测过一次的文件会被标记，二次加载会跳过检测)

###注意：
* 由于python2.7中zipfile对中、日文支持太差，故使用python3
* 本工具主要是针对Linux开发，虽然也做过一点兼容性使其可以在win下运行，但毕竟win下比这个好的工具太多了，除了简单兼容之外是不会做太多的Bug测试优化的。但如果还是想在win下尝试一下的话可以按以下步骤安装python环境：   
    1. 在[Python官网](https://www.python.org/downloads/windows/)下载安装最新的python3.4并安装，一切按默认，其会自动安装tk和pip   
    2. win+R键输入“cmd”启动命令行，输入：   
        $ pip install rarfile   
        $ pip install pillow   
    3. 然后就可以双击py文件运行了
* 需要安装python3的pillow、tkinter和rarfile库(tkinter自带)，ubuntu下可依次输入以下命令:    
    $ sudo apt-get install python3-pil      
    $ sudo apt-get install python3-tk   
    **$ sudo apt-get install python3-pil.imagetk**  
    $ sudo apt-get install python3-pip      
    $ sudo pip install rarfile  
* **_NEW_** 非ubuntu系统也只需要通过pip安装pillow和rarfile模块即可
* 现大部分的卡顿在于图片文件的载入和重绘，也就是zipfile的read函数和tk界面绘制：   
按键事件->轮询响应事件(0.0001s ~ 0.0002s)->载入图片(0.5s ~ 12s)->显示(0.4s ~ 1.0s)    
**现已加入抗锯齿手动设置，默认为无抗锯齿，开启和关闭抗锯齿载入时间相差0.7s ~ 10s**
* 任何按键都会终止幻灯片，但鼠标**点击切换图片**不会使幻灯片终止

###使用说明：
* Linux下使用  
        $ python3 ./cpsImgBrowser.py  
打开，win下直接双击
* 进入后首先需输入指定需要浏览的压缩包们所在的<u>**文件夹地址**</u>
* 开始浏览图片后的操作：  
        左： 上一张  
        右： 下一张  
        a 或者 上： 上一个压缩包  
        d 或者 下： 下一个压缩包  
        s： 幻灯片播放（默认3s）  
        p：设置幻灯片时间    
        w：压缩包跳转    
        e：图片跳转    
        r：打乱图片顺序    
        c：跳转到随机压缩包   
        o：设置是否开启抗锯齿(切换图片后可见差别)   
        m：添加默认密码
