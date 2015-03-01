#Linux下浏览压缩文件内图片的小工具

###特点：
* 支持zip和rar文件
* 可保存压缩文件的密码，并支持设置多个默认密码
* 支持幻灯片播放
* 以文件夹为源，快速切换压缩文件
* 文件解压于内存中，减少磁盘使用

###缺点：
* 未完全使用tkinter，输入界面使用命令行
* 没有文件列表浏览界面
* 未加入预缓存功能，切换时略卡
* 使用文件的MD5值区别并保存压缩文件密码，计算MD5略耗时(0.02~0.6s不等)

###注意：
* 由于python2.7中zipfile对中、日文支持太差，故使用python3
* 需要安装python3的PIL、tkinter和rarfile库，ubuntu下可依次输入以下命令：  
        $ sudo apt-get install python3-pil  
        $ sudo apt-get install python3-tk  
        $ sudo apt-get install python3-pip  
        $ sudo pip install rarfile  

###使用说明：
* ubuntu下使用  
        $ python3 ./cpsImgBrowser.py  
打开
* 进入后首先需输入指定需要浏览的压缩包们所在的<u>**文件夹地址**</u>
*开始浏览图片后的操作：  
        左： 上一张  
        右： 下一张  
        a： 上一个压缩包  
        d： 下一个压缩包  
        h： 幻灯片播放（默认3s）  