#!/usr/bin/env python3
# coding=utf-8

import io
import urllib
import json
import os
import rarfile
import hashlib
import threading
import time
import zipfile
import PIL
from PIL import Image
from PIL.ImageTk import *
import tkinter as tk
from tkinter.filedialog import *
from tkinter.simpledialog import *

_NONE = ""
BACK_IMG = 1
NEXT_IMG = 2
SLIDE_TIME = 3
USE_FILE_MD5 = FALSE
BACK_FILE = -1
NEXT_FILE = 0
CURRENT_FILE = 1

changePic = FALSE

class guardTh(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.nextLoadImgPos = 0
        self.nowFilePos = -1
        self.nowFilename = _NONE
        self.nowShowImgPos = 0
        self.imgCache = []
        self.imgList = []
        self.imgNum = 0
        self.shouldLoadImg = FALSE
        self.shouldRefreshImg = FALSE

    def run(self):
        global mImgLoadQueueLock
        global changeImgLock
        global CPS_FILELock
        global mFilePos
        global FILE_LIST
        global CPS_FILE
        global root
        global label
        global changePic
        global mImgPos

        global willLoadImgQueue
        global nTime
        nTime = time.time()

        while TRUE:
            CPS_FILELock.acquire()
            if self.nowFilePos != mFilePos:
                self.nowFilePos = mFilePos
                self.nowFilename = FILE_LIST[self.nowFilePos]["filename"].encode("utf-8").decode("utf-8")
                self.imgList = getImageList(CPS_FILE)
                self.imgCache = [_NONE for i in range(len(self.imgList))]
                changeImgLock.acquire()
                mImgPos = 0
                changeImgLock.release()
                self.imgNum = len(self.imgList)
                self.nowShowImgPos = 0
                self.nextLoadImgPos = 0
                self.shouldLoadImg = TRUE
                self.shouldRefreshImg = TRUE
                mImgLoadQueueLock.acquire()
                willLoadImgQueue = {
                    "CPS_FILE": CPS_FILE,
                    "nowFilePos": self.nowFilePos,
                    "imgCache": self.imgCache,
                    "willLoadImgQueue": [{"imgInfo": self.imgList[0],
                                          "imgPos": 0}]
                    }
                mImgLoadQueueLock.release()
            else:
                changeImgLock.acquire()
                if self.nowShowImgPos != mImgPos:
                    mImgPos %= len(self.imgList)
                    self.nowShowImgPos = mImgPos
                    self.shouldRefreshImg = TRUE

                    mImgLoadQueueLock.acquire()
                    if (not willLoadImgQueue["willLoadImgQueue"]) or willLoadImgQueue["willLoadImgQueue"][0]["imgInfo"] != self.imgList[self.nowShowImgPos]:
                        willLoadImgQueue["willLoadImgQueue"].insert(0, {"imgInfo": self.imgList[self.nowShowImgPos],
                                                                        "imgPos": self.nowShowImgPos})
                    mImgLoadQueueLock.release()
                changeImgLock.release()

                self.nextLoadImgPos += 1
                list_num = len(self.imgList)
                self.nextLoadImgPos %= list_num
                n = 0
                while self.imgCache[self.nextLoadImgPos]:
                    n += 1
                    self.nextLoadImgPos += 1
                    self.nextLoadImgPos %= list_num
                    if n >= list_num :
                        self.shouldLoadImg = FALSE
                        break
                if self.shouldLoadImg:
                    mImgLoadQueueLock.acquire()
                    willLoadImgQueue["willLoadImgQueue"].append({"imgInfo": self.imgList[self.nextLoadImgPos],
                                                                 "imgPos": self.nextLoadImgPos})
                    mImgLoadQueueLock.release()
            CPS_FILELock.release()

            if self.shouldRefreshImg and self.imgCache[self.nowShowImgPos]:
                # print("Change Img Time: %f " % (time.time() - nTime))
                st = time.time()
                self.shouldRefreshImg = FALSE
                imgName = self.imgList[self.nowShowImgPos].filename.split('/')[-1]
                try:
                    imgName = imgName.encode('cp437')
                    imgName = imgName.decode("gbk")
                except:
                    pass

                showImg = self.imgCache[self.nowShowImgPos]
                w, h = showImg.size
                if root.winfo_height() != 1:
                    scale = root.winfo_height() / 550.0
                else:
                    scale = 600 / 550.0
                box_width = 600 * scale
                box_height = 550 * scale
                show_img_resize = resizePic(w, h, box_width, box_height, showImg)
                wr, hr = show_img_resize.size
                title = "图片浏览器-%d/%d- %d/%d (%dx%d) %s --%s " % (self.nowFilePos + 1,
                                                                 len(FILE_LIST),
                                                                 self.nowShowImgPos + 1,
                                                                 self.imgNum,
                                                                 wr,
                                                                 hr,
                                                                 imgName,
                                                                 self.nowFilename)
                root.title(title)

                tk_img = PIL.ImageTk.PhotoImage(show_img_resize)
                label.configure(image = tk_img)
                label.image = tk_img
                label.pack(padx=5, pady=5)

                # print("Sum Load Img Time: " + str(time.time() - st))
        print("guardTh is Over!!")

class loadImgTh(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.mLoadingFilePos = -1
        self.nowLoadImgInfo = {}
        self.cpsFile = _NONE

    def run(self):
        global mFilePos
        global willLoadImgQueue
        global mImgLoadQueueLock

        while TRUE:
            if self.nowLoadImgInfo:
                # print("loadImgTh: start filename: %s" % (self.nowLoadImgInfo["imgInfo"].filename))
                data = self.cpsFile.read(self.nowLoadImgInfo["imgInfo"])
                try:
                    pil_image = PIL.Image.open(io.BytesIO(data))
                except Exception as ex:
                    print(ex)
                    pil_image = _NONE
                # print("loadImgTh: over  filename: %s" % (self.nowLoadImgInfo["imgInfo"].filename))

            mImgLoadQueueLock.acquire()
            if self.mLoadingFilePos is willLoadImgQueue["nowFilePos"]:
                if self.nowLoadImgInfo:
                    willLoadImgQueue["imgCache"][self.nowLoadImgInfo["imgPos"]] = pil_image
            else:
                self.cpsFile = willLoadImgQueue["CPS_FILE"]
                self.mLoadingFilePos = willLoadImgQueue["nowFilePos"]

            self.nowLoadImgInfo = _NONE
            while TRUE:
                if not willLoadImgQueue["willLoadImgQueue"]:
                    self.nowLoadImgInfo = _NONE
                    break
                self.nowLoadImgInfo = willLoadImgQueue["willLoadImgQueue"].pop(0)
                if not willLoadImgQueue["imgCache"][self.nowLoadImgInfo["imgPos"]]:
                    break
            mImgLoadQueueLock.release()
        print("loadImgTh is Over!!")

def slide():
    print ("slide")
    global slideLock
    while(True):
        slideLock.acquire()
        checkTmp = SLIDE_START
        slideLock.release()
        if (checkTmp):
            ShowPic(NEXT_IMG)
            time.sleep(SLIDE_TIME)
        else:
            break

def getStringMD5(string):
    return hashlib.md5(string.encode("utf-8")).hexdigest()

def getFileMD5(uri):
    if not os.path.exists(uri):
        print("error:fileURI not exists")
        exit()
    md5file = open(uri, 'rb')
    md5 = hashlib.md5(md5file.read()).hexdigest()
    md5file.close()
    return md5

def resizePic(w, h, w_box, h_box, pil_image):
    f1 = 1.0*w_box/w
    f2 = 1.0*h_box/h
    factor = min([f1, f2])
    width = int(w*factor)
    height = int(h*factor)
    return pil_image.resize((width, height), PIL.Image.ANTIALIAS)

def getImageList(cps):
    tImgList = [info for info in cps.infolist()
               if(info.filename.endswith('jpg')
                  or info.filename.endswith('png')
                  or info.filename.endswith('gif'))]
    return tImgList

def ShowPic(value):
    global changeImgLock
    global mImgPos
    global nTime
    changeImgLock.acquire()
    if value is BACK_IMG:
        mImgPos -= 1
    elif value is NEXT_IMG:
        mImgPos += 1

    nTime = time.time()
    changeImgLock.release()

def mouseEvent(ev):
    global slideT
    global SLIDE_START
    if ev.x > root.winfo_width() / 3.0 * 2.0:
        ShowPic(NEXT_IMG)
    elif ev.x < root.winfo_width() / 3.0:
        ShowPic(BACK_IMG)
    elif ev.y > root.winfo_height() / 3.0 * 2.0:
        if slideT.isAlive():
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()
        openFile(NEXT_FILE)
    elif ev.y < root.winfo_height() / 3.0:
        if slideT.isAlive():
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()
        openFile(BACK_FILE)

def onKeyPress(ev):
    global slideT
    global SLIDE_START
    # print(ev.keycode)
    if ev.keycode == 111 or ev.keycode == 113:
        ShowPic(BACK_IMG)
    elif ev.keycode == 114 or ev.keycode == 116:
        ShowPic(NEXT_IMG)
    elif ev.keycode == 40:
        if slideT.isAlive():
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()
        openFile(NEXT_FILE)
    elif ev.keycode == 38:
        if slideT.isAlive():
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()
        openFile(BACK_FILE)
    elif ev.keycode == 43:
        if slideT.isAlive():
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()
        else:
            slideLock.acquire()
            SLIDE_START = True
            slideLock.release()
            slideT = threading.Timer(0, slide)
            slideT.start()

def nextCanReadFile(direct, now_file_pos):
    global FILE_LIST
    if direct is NEXT_FILE:
        now_file_pos += 1
    elif direct is BACK_FILE:
        now_file_pos -= 1
    now_file_pos %= len(FILE_LIST)
    while FILE_LIST[now_file_pos]["CanRead"] is FALSE:
        if direct is BACK_FILE:
            now_file_pos -= 1
        else:
            now_file_pos += 1
        now_file_pos %= len(FILE_LIST)
    return now_file_pos

def openFile(direct):
    global CPS_FILELock
    global mFilePos
    global CPS_FILE
    global FILE_LIST
    file_pos = nextCanReadFile(direct, mFilePos)
    return_fruit = FALSE
    # print(FILE_LIST[file_pos]["filename"])
    if FILE_LIST[file_pos]["filename"].endswith('rar'):
        return_fruit = openRarFile(file_pos)
    elif FILE_LIST[file_pos]["filename"].endswith('zip'):
        return_fruit = openZipFile(file_pos)

    while not return_fruit:
        FILE_LIST[file_pos]["CanRead"] = FALSE
        file_pos = nextCanReadFile(direct, file_pos)
        if FILE_LIST[file_pos]["filename"].endswith('rar'):
            return_fruit = openRarFile(file_pos)
        elif FILE_LIST[file_pos]["filename"].endswith('zip'):
            return_fruit = openZipFile(file_pos)

    CPS_FILELock.acquire()
    CPS_FILE = return_fruit
    mFilePos = file_pos
    CPS_FILELock.release()

    return return_fruit

def openZipFile(file_pos):
    global FILE_URI
    global FILE_LIST
    global PWD_JSON

    _filename = FILE_LIST[file_pos]["filename"]
    if not os.path.exists(FILE_URI + _filename):
        print("error:fileURI not exists")
        exit()
    # StartTime = time.time()
    if USE_FILE_MD5:
        file_md5 = getFileMD5(FILE_URI + _filename)
    else:
        file_md5 = getStringMD5(FILE_URI + _filename)
    # print(time.time() - StartTime)

    try:
        t_cps_file = zipfile.ZipFile(FILE_URI + _filename)
    except RuntimeError:
        print(_filename + " open fail")
        return FALSE
    if not t_cps_file.infolist():
        t_list = getImageList(t_cps_file)
        if t_list:
            return FALSE
    try:
        t_cps_file.testzip()
        needs_password = FALSE
    except BadZipFile:
        needs_password = True

    if needs_password:
        try:
            pwd = PWD_JSON[file_md5]
            t_cps_file.setpassword(pwd.encode("utf-8"))
            t_cps_file.open(listT[0])
        except:
            has_pwd = FALSE
            try:
                pwd_default = PWD_JSON["defaultPassword"]
            except:
                pwd_default = []
            if not pwd_default:
                for p in pwd_default:
                    try:
                        t_cps_file.setpassword(p.encode("utf-8"))
                        t_cps_file.open(listT[0])
                        has_pwd = True
                        PWD_JSON.update({file_md5: p})
                        t_pwd_json = json.dumps(PWD_JSON)
                        with open('./Pwd.json', 'w') as f:
                            f.write(t_pwd_json)
                        break
                    except RuntimeError:
                        pass
            while not has_pwd:
                pwd = _NONE
                while pwd == _NONE:
                    pwd = askstring(title='请输入密码', prompt="Zip File: " + _filename + "\n输入\"skip\"跳过此文件")
                if pwd == "skip":
                    return FALSE
                try:
                    t_cps_file.setpassword(pwd.encode("utf-8"))
                    t_cps_file.open(listT[0])
                    has_pwd = True
                    PWD_JSON.update({file_md5: pwd})
                    t_pwd_json = json.dumps(PWD_JSON)
                    with open('./Pwd.json', 'w') as f:
                        f.write(t_pwd_json)
                except Exception as ex:
                    print(ex)
                    print("Password is WRONG !")
    return t_cps_file

def openRarFile(file_pos):
    global FILE_URI
    global FILE_LIST
    global PWD_JSON

    _filename = FILE_LIST[file_pos]["filename"]
    if not os.path.exists(FILE_URI + _filename):
        print("error:fileURI not exists")
        exit()
    # st = time.time()
    if USE_FILE_MD5:
        file_md5 = getFileMD5(FILE_URI + _filename)
    else:
        file_md5 = getStringMD5(FILE_URI + _filename)
    # print("getFileMD5: %f"%(time.time() - st))

    try:
        t_cps_file = rarfile.RarFile(FILE_URI + _filename)
    except:
        print(_filename + " open fail")
        return FALSE
    if not t_cps_file.infolist():
        t_list = getImageList(t_cps_file)
        if t_list:
            return FALSE

    if t_cps_file.needs_password():
        pwd = _NONE
        s_reload = True
        try:
            pwd = PWD_JSON[file_md5]
            t_cps_file.setpassword(pwd)
            # t_cps_file.read(t_cps_file.infolist()[0])
            # t_cps_file.testrar()
            s_reload = FALSE
        except:
            has_pwd = FALSE
            try:
                pwd_default = PWD_JSON["defaultPassword"]
            except:
                pwd_default = []
            if not pwd_default:
                for p in pwd_default:
                    try:
                        t_cps_file.setpassword(p)
                        # t_cps_file.read(listT[0])
                        t_cps_file.testrar()
                        has_pwd = True
                        pwd = p
                        PWD_JSON.update({file_md5:p})
                        t_pwd_json = json.dumps(PWD_JSON)
                        with open('./Pwd.json','w') as f:
                            f.write(t_pwd_json)
                        break
                    except:
                        pass
            while not has_pwd:
                pwd = _NONE
                while pwd == _NONE:
                    pwd = askstring(title='请输入密码', prompt="RaR File: " + _filename + "\n输入\"skip\"跳过此文件")
                if pwd == "skip":
                    return FALSE
                try:
                    t_cps_file.setpassword(pwd)
                    # t_cps_file.read(listT[0])
                    t_cps_file.testrar()
                    has_pwd = True
                    PWD_JSON.update({file_md5: pwd})
                    t_pwd_json = json.dumps(PWD_JSON)
                    with open('./Pwd.json','w') as f:
                        f.write(t_pwd_json)
                except:
                    print("Password is WRONG !")
        # try:
        #    t_cps_file.testrar()
        # except:
        #    return FALSE
        if s_reload:
            t_cps_file.close()
            t_cps_file = rarfile.RarFile(FILE_URI + _filename)
            t_cps_file.setpassword(pwd)
            # CPS_FILE.testrar()

    return t_cps_file

'''入口'''
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("800x600+%d+%d" % ((800 - root.winfo_width())/2, (600 - root.winfo_height())/2) )
    root.bind("<Button-1>", mouseEvent)
    root.bind("<Key>", onKeyPress)
    mWinChanged = FALSE
    w_box = 600
    h_box = 550

    if len(sys.argv)<2:
        fd = LoadFileDialog(root, title="要打开的文件")
        FILE_URI = fd.go()
        if FILE_URI == _NONE:
            print("URI is wrong")
            exit()
        t_filename = FILE_URI.split("/")[-1]
        FILE_URI = FILE_URI.replace(t_filename, _NONE)
    else:
        FILE_URI = _NONE
        for uri in sys.argv[1:]:
            FILE_URI += (uri + " ")
        FILE_URI = FILE_URI[:-1]
        t_filename = _NONE
        if not FILE_URI.endswith("/"):
            t_filename = FILE_URI.split("/")[-1]

    fileNameList = os.listdir(FILE_URI)
    fileNameList = [f for f in fileNameList if (f.endswith('rar') or f.endswith('rar'))]
    FILE_LIST = [{"filename": fn, "CanRead": TRUE} for fn in fileNameList]
    try:
        mFilePos = FILE_LIST.index({"filename": t_filename, "CanRead": TRUE})
    except:
        mFilePos = 0

    slideT = threading.Timer(0, slide)
    slideLock = threading.Lock()
    mImgLoadQueueLock = threading.Lock()
    changeImgLock = threading.Lock()
    CPS_FILELock = threading.Lock()
    SLIDE_START = FALSE

    try:
        with open('./Pwd.json', 'r') as f:
            pwdJson = f.read()
    except:
        with open('./Pwd.json', 'w') as f:
            f.write('')
        pwdJson = ''
    try:
        PWD_JSON = json.JSONDecoder().decode(pwdJson)
    except:
        PWD_JSON = {}

    openFile(CURRENT_FILE)

    guardTask = guardTh()
    guardTask.setDaemon(TRUE)
    loadTask = loadImgTh()
    loadTask.setDaemon(TRUE)
    guardTask.start()
    loadTask.start()

    label = tk.Label(root, image=_NONE, width=w_box, height=h_box)
    label.pack(padx=15, pady=15, expand=1, fill="both")
    root.mainloop()
