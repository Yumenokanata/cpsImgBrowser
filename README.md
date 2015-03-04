#Linux下浏览压缩文件内图片的小工具

###特点：
* 支持zip和rar文件
* 对zip中的中日文有良好支持
* 可保存压缩文件的密码，并支持设置多个默认密码
* 支持幻灯片播放
* 以文件夹为源，快速切换压缩文件
* 文件解压于内存中，减少磁盘使用
* 多线程预载入，提升图片显示速度
* 独立线程载入图片，提升响应速度

###缺点：
* 没有文件列表浏览界面
* 尚未加入文件预载入，在跳转文件时对无图片文件、大文件载入和进行默认密码测试会耗去较多时间(检测过一次的文件会被标记，二次加载会跳过检测)

###注意：
* 由于python2.7中zipfile对中、日文支持太差，故使用python3
* 需要安装python3的PIL、tkinter和rarfile库，ubuntu下可依次输入以下命令：  
        $ sudo apt-get install python3-pil  
        $ sudo apt-get install python3-tk  
        $ sudo apt-get install python3-pip  
        $ sudo pip install rarfile  
* 现大部分的卡顿在于图片文件的载入和重绘，也就是zipfile的read函数和tk界面绘制：   
点击到响应点击(0.0001s ~ 0.0002s)->载入图片(0.5s ~ 12s)->显示(0.4s ~ 1.0s)

###使用说明：
* ubuntu下使用  
        $ python3 ./cpsImgBrowser.py  
打开
* 进入后首先需输入指定需要浏览的压缩包们所在的<u>**文件夹地址**</u>
* 开始浏览图片后的操作：  
        左： 上一张  
        右： 下一张  
        a 或者 上： 上一个压缩包  
        d 或者 下： 下一个压缩包  
        h： 幻灯片播放（默认3s）  
        p：设置幻灯片时间
        w：压缩包跳转
        e：图片跳转
