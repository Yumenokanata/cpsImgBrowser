#Linux下浏览压缩文件内图片的小工具
--- 
进度：     
功能实现阶段 **_完成_**     
结构优化 **_进行中_**  


###设计原则：
* 简单的压缩包密码管理，让人感觉不到密码的存在
* 尽量不使用磁盘缓存
* 尽量少使用的第三方包

###测试平台：
Ubuntu 14.04        
CentOS7

###特点：
* 支持zip和rar文件和带图片的文件夹
* **_可保存压缩文件的密码，并支持设置多个默认密码_**
* **_支持双页模式和漫画模式_**
* **_支持收藏夹和书签功能_**
* **_随机切换功能，并且随时可进入随时可退出_**
* 提供两个分支版本：mini版和全功能版
* 文件解压于内存中，减少磁盘使用
* 跳转到随机文件功能
* 支持幻灯片播放
* 多线程预载入，提升图片显示速度
* 独立线程载入图片，提升响应速度    
* 特有排序规则，正确排序文件名常见的"a1"<"a10"<"a2"问题

###缺点：
* 对zip文件的效率较低
* 由于GIL，无法实际发挥多线程优势，读取部分大图片时卡顿严重，待加入多进程

###使用说明：
* 本工具分为两个版本，分别为mini版（mini分支）和全功能版（master分支）。    
**mini版**只有单页浏览文件功能，全为快捷键操作，但轻巧简单   
**全功能版**全GUI交互，提供双页模式、收藏夹、书签、侧边栏等等更多功能，但可能会有一些不稳定（毕竟只有我一个人测试 T_T）
* 因为乱码问题，本工具为 **_python3_** 开发。依赖于两个包：tkinter和pillow        
ubuntu下可依次输入以下命令安装依赖（imagetk包很重要）:    
    $ sudo apt-get install python3-pil      
    $ sudo apt-get install python3-tk   
    **$ sudo apt-get install python3-pil.imagetk**  
    $ sudo apt-get install python3-pip      
    $ sudo pip3 install rarfile  
如果安装过python2环境请注意输入的是"pip3"或"pip3.4"
* **mini版**操作说明：    
    1. 有两种选择路径的方式：
        1. 命令行打开时在后面输入路径作为参数，如：        
        $ python3 ./cpsImgBrowser.py  /home/xxx/图片/
        2. 无参数启动会自动弹出tkinter自带的文件选择界面，即可选择
    2. 快捷键：     
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
* **全功能版**操作说明：
    1. 同mini版一样也支持鼠标点击操作:       
        左三分之一：上一张图      
        右三分之一：下一张图      
        中间的上部：上一个压缩包        
        中间的下部：下一个压缩包        
        中间的中间：开启或关闭幻灯片      
    2. 其他操作全为GUI，应该很简单
    
###小贴士：
    1. 密码管理界面下的默认密码设置为 每行 为一个默认密码
    2. 随机模式为随机跳图片，可回退，同时适用幻灯片和手动切换，可随时关闭返回正常顺序浏览
    3. 双页模式的规则为，宽图(即width大于height)的图仍然使用单页模式
    4. 漫画模式就是左右互换的双页模式，仍然遵从上一条规则
    5. 双页模式下如遇页数没对齐可使用“跳转 -> 下一页”或"上一页"强制只切换一张
    6. “适应高度”和“适应宽度”模式只能用于非双页模式
    7. 对于大于窗口分辨率的图片不作放大（也就是说放大倍数范围在0% ～ 100%）
    8. 首选项中“图像放大方式”对性能有比较大的影响：“抗锯齿”模式最慢，比其他方式慢0.5~4s，其他方式速度差不多（效果也差不多...），如遇图片切换较缓慢（等待时间2s以上），可尝试切换放大模式改善性能
    9. 文件跳转时和图片跳转时输入的数字都不会溢出，但处理方式不同，文件跳转数字溢出则切换到最后一个文件，图片跳转数字溢出则整除后取余
    10. 幻灯片中，按任何键盘的键都会使幻灯片停止，但鼠标切换图片不会（切换文件包还是会中断）