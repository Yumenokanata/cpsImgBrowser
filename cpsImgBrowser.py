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
import random
import PIL
from PIL import Image
from PIL.ImageTk import *
import tkinter as tk
from tkinter.filedialog import *
from tkinter.simpledialog import *
from tkinter.messagebox import *

_NONE = ""
BACK_IMG = 1
NEXT_IMG = 2
JUMP_IMG = 3
SLIDE_TIME = 3
USE_FILE_MD5 = False
BACK_FILE = -1
NEXT_FILE = 0
CURRENT_FILE = 1
NOCHANGE_FILE = 2
JUMP_FILE = 3
BAD_FILE = "bad_file"
ANTIALIAS_SHOW_IMG = False

class guardTh(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.nextLoadImgPos = 0
        self.nowFilePos = -1
        self.nowFilename = _NONE
        self.nowFile = _NONE
        self.nowShowImgPos = 0
        self.imgCache = []
        self.imgList = []
        self.imgNum = 0
        self.shouldLoadImg = False
        self.shouldRefreshImg = False

    def run(self):
        global mImgLoadQueueLock
        global changeImgLock
        global ChangeFileLock
        global ChangeFileFlag
        global RandomLoadImgFlag
        global willLoadImgQueue
        global FILE_LIST
        global root
        global label
        global mFilePos
        global mImgPos

        global nTime
        nTime = time.time()

        while TRUE:
            ChangeFileLock.acquire()
            if not ChangeFileFlag["direct"] is NOCHANGE_FILE:
                t_direct = ChangeFileFlag["direct"]
                FILE_LIST[self.nowFilePos]["CurrentPos"] = self.nowShowImgPos
                if ChangeFileFlag["direct"] is JUMP_FILE:
                    self.nowFilePos = ChangeFileFlag["nowFilePos"]
                ChangeFileFlag["direct"] = NOCHANGE_FILE
                ChangeFileLock.release()
                root.title("图片浏览器-Loading/%d" % len(FILE_LIST))
                mImgLoadQueueLock.acquire()
                self.openFile(t_direct)
                self.nowShowImgPos = FILE_LIST[self.nowFilePos]["CurrentPos"]

                # print("self.nowShowImgPos: %d" % (self.nowShowImgPos))
                # print("Load File Time: " + str(time.time() - st1))
                self.nowFilename = FILE_LIST[self.nowFilePos]["filename"].encode("utf-8").decode("utf-8")
                self.imgList = self.getImageList(self.nowFile)
                changeImgLock.acquire()
                mImgPos = self.nowShowImgPos
                changeImgLock.release()
                self.imgCache = [_NONE for i in range(len(self.imgList))]
                self.imgNum = len(self.imgList)
                self.nextLoadImgPos = self.nowShowImgPos
                self.shouldLoadImg = TRUE
                self.shouldRefreshImg = TRUE
                t_cps_file = self.nowFile
                willLoadImgQueue = {
                    "CPS_FILE": t_cps_file,
                    "nowFilePos": self.nowFilePos,
                    "imgCache": self.imgCache,
                    "willLoadImgQueue": [{"imgInfo": self.imgList[self.nowShowImgPos],
                                          "imgPos": self.nowShowImgPos}]
                    }
                list_num = len(self.imgList)
                for i in range(min([25, list_num])):
                    t_nextLoadImgPos = (self.nowShowImgPos + i) % list_num
                    willLoadImgQueue["willLoadImgQueue"].append({"imgInfo": self.imgList[t_nextLoadImgPos],
                                                                 "imgPos": t_nextLoadImgPos})
                    t_nextLoadImgPos = (self.nowShowImgPos - i) % list_num
                    willLoadImgQueue["willLoadImgQueue"].append({"imgInfo": self.imgList[t_nextLoadImgPos],
                                                                 "imgPos": t_nextLoadImgPos})
                mImgLoadQueueLock.release()
            else:
                ChangeFileLock.release()
                changeImgLock.acquire()
                if RandomLoadImgFlag:
                    mImgLoadQueueLock.acquire()
                    random.shuffle(self.imgList)
                    mImgPos = 0
                    self.nowShowImgPos = mImgPos
                    self.shouldRefreshImg = TRUE
                    RandomLoadImgFlag = False
                    self.imgCache = [_NONE for i in range(len(self.imgList))]
                    willLoadImgQueue["imgCache"] = self.imgCache
                    willLoadImgQueue["willLoadImgQueue"] = [{"imgInfo": self.imgList[self.nowShowImgPos],
                                                             "imgPos": self.nowShowImgPos}]
                    list_num = len(self.imgList)
                    for i in range(min([25, list_num])):
                        t_nextLoadImgPos = (self.nowShowImgPos + i) % list_num
                        willLoadImgQueue["willLoadImgQueue"].append({"imgInfo": self.imgList[t_nextLoadImgPos],
                                                                     "imgPos": t_nextLoadImgPos})
                        t_nextLoadImgPos = (self.nowShowImgPos - i) % list_num
                        willLoadImgQueue["willLoadImgQueue"].append({"imgInfo": self.imgList[t_nextLoadImgPos],
                                                                     "imgPos": t_nextLoadImgPos})
                    mImgLoadQueueLock.release()
                elif self.nowShowImgPos != mImgPos:
                    mImgPos %= len(self.imgList)
                    self.nowShowImgPos = mImgPos
                    self.shouldRefreshImg = TRUE

                    mImgLoadQueueLock.acquire()
                    willLoadImgQueue["willLoadImgQueue"] = [{"imgInfo": self.imgList[self.nowShowImgPos],
                                                             "imgPos": self.nowShowImgPos}]
                    list_num = len(self.imgList)
                    for i in range(min([25, list_num])):
                        t_nextLoadImgPos = (self.nowShowImgPos + i) % list_num
                        willLoadImgQueue["willLoadImgQueue"].append({"imgInfo": self.imgList[t_nextLoadImgPos],
                                                                     "imgPos": t_nextLoadImgPos})
                        t_nextLoadImgPos = (self.nowShowImgPos - i) % list_num
                        willLoadImgQueue["willLoadImgQueue"].append({"imgInfo": self.imgList[t_nextLoadImgPos],
                                                                     "imgPos": t_nextLoadImgPos})
                    mImgLoadQueueLock.release()
                changeImgLock.release()

            if self.shouldRefreshImg and self.imgCache[self.nowShowImgPos]:
                # print("Change Img Time: %f " % (time.time() - nTime))
                st = time.time()
                self.shouldRefreshImg = False
                imgName = self.imgList[self.nowShowImgPos].filename
                imgName = imgName.replace("/", "\\")
                imgName = imgName.split('\\')[-1]
                try:
                    imgName = imgName.encode('cp437')
                    imgName = imgName.decode("gbk")
                except:
                    pass

                showImg = self.imgCache[self.nowShowImgPos]
                if showImg is BAD_FILE:
                    label.configure(image="")
                    label['text'] = "Bad Image"
                    title = "图片浏览器-%d/%d- %d/%d (0x0) %s --%s " % (self.nowFilePos + 1,
                                                                 len(FILE_LIST),
                                                                 self.nowShowImgPos + 1,
                                                                 self.imgNum,
                                                                 imgName,
                                                                 self.nowFilename)
                    root.title(title)
                    continue
                img_w, img_h = showImg.size
                win_h = root.winfo_height()
                win_w = root.winfo_width()
                if win_h == 1:
                    win_h = 600
                    win_w = 800
                scale = 1.0 * win_h / img_h
                if img_w * scale > win_w:
                    scale = 1.0 * win_w / img_w
                if scale <= 1:
                    box_height = img_h * scale
                    box_width = img_w * scale
                    show_img_resize = self.resizePic(img_w, img_h, box_width, box_height, showImg)
                else:
                    show_img_resize = showImg
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
                label['text']=""
                label.configure(image = tk_img)
                label.image = tk_img
                label.pack(padx=5, pady=5)

                # print("Sum Load Img Time: " + str(time.time() - st))

    def getStringMD5(self, string):
        return hashlib.md5(string.encode("utf-8")).hexdigest()

    def getFileMD5(self, uri):
        if not os.path.exists(uri):
            print("error:fileURI not exists")
            exit()
        md5file = open(uri, 'rb')
        md5 = hashlib.md5(md5file.read()).hexdigest()
        md5file.close()
        return md5

    def resizePic(self, w, h, rw, rh, pil_image):
        f1 = 1.0 * rw / w
        f2 = 1.0 * rh / h
        factor = min([f1, f2])
        width = int(w * factor)
        height = int(h * factor)
        if ANTIALIAS_SHOW_IMG:
            return pil_image.resize((width, height), PIL.Image.ANTIALIAS)
        else:
            return pil_image.resize((width, height))

    def getImageList(self, cps):
        t_img_list = [info for info in cps.infolist()
                   if(info.filename.endswith('jpg')
                      or info.filename.endswith('png')
                      or info.filename.endswith('gif'))]
        return t_img_list

    def nextCanReadFile(self, direct, now_file_pos):
        global FILE_LIST
        if direct is NEXT_FILE:
            now_file_pos += 1
        elif direct is BACK_FILE:
            now_file_pos -= 1
        now_file_pos %= len(FILE_LIST)
        while FILE_LIST[now_file_pos]["CanRead"] is False:
            if direct is BACK_FILE:
                now_file_pos -= 1
            else:
                now_file_pos += 1
            now_file_pos %= len(FILE_LIST)
        return now_file_pos

    def openFile(self, direct):
        global st1
        st1 = time.time()
        global FILE_LIST
        global PWD_JSON

        file_pos = self.nextCanReadFile(direct, self.nowFilePos)
        return_fruit = False
        # print(FILE_LIST[file_pos]["filename"])
        filename = FILE_LIST[file_pos]["filename"]
        file_uri = FILE_LIST[file_pos]["fileUri"]
        if filename.endswith('rar'):
            return_fruit = self.openRarFile(file_pos)
        elif filename.endswith('zip'):
            return_fruit = self.openZipFile(file_pos)

        while not return_fruit:
            if USE_FILE_MD5:
                file_md5 = self.getFileMD5(file_uri + filename)
            else:
                file_md5 = self.getStringMD5(file_uri + filename)
            try:
                PWD_JSON[file_md5]
            except:
                PWD_JSON.update({file_md5:{"password": "", "badfile": True}})
            FILE_LIST[file_pos]["CanRead"] = False
            file_pos = self.nextCanReadFile(direct, file_pos)
            filename = FILE_LIST[file_pos]["filename"]
            file_uri = FILE_LIST[file_pos]["fileUri"]
            if filename.endswith('rar'):
                return_fruit = self.openRarFile(file_pos)
            elif filename.endswith('zip'):
                return_fruit = self.openZipFile(file_pos)

        t_pwd_json = json.dumps(PWD_JSON)
        with open('./Pwd.json', 'w') as f:
            f.write(t_pwd_json)
        self.nowFile = return_fruit
        self.nowFilePos = file_pos

        return return_fruit

    def openZipFile(self, _file_pos):
        global FILE_LIST
        global PWD_JSON

        _filename = FILE_LIST[_file_pos]["filename"]
        _file_uri = FILE_LIST[_file_pos]["fileUri"]

        if not os.path.exists(_file_uri + _filename):
            print("error:fileURI not exists")
            exit()
        # StartTime = time.time()
        if USE_FILE_MD5:
            file_md5 = self.getFileMD5(_file_uri + _filename)
        else:
            file_md5 = self.getStringMD5(_file_uri + _filename)
        # print(time.time() - StartTime)

        try:
            if PWD_JSON[file_md5]["badfile"]:
                return False
        except:
            pass
        try:
            t_cps_file = zipfile.ZipFile(_file_uri + _filename)
        except:
            print(_filename + " open fail")
            return False
        if t_cps_file.infolist():
            t_list = self.getImageList(t_cps_file)
            if not t_list:
                return False
        try:
            t_cps_file.open(t_list[0])
            needs_password = False
        except:
            needs_password = True

        if needs_password:
            try:
                pwd = PWD_JSON[file_md5]["password"]
                if not pwd:
                    raise Exception
                t_cps_file.setpassword(pwd.encode("utf-8"))
                t_cps_file.open(t_list[0])
            except:
                has_pwd = False
                try:
                    pwd_default = PWD_JSON["defaultPassword"]
                except:
                    pwd_default = []
                if pwd_default:
                    for p in pwd_default:
                        try:
                            t_cps_file.setpassword(p.encode("utf-8"))
                            t_cps_file.open(t_list[0])
                            has_pwd = True
                            PWD_JSON.update({file_md5:{"password": p, "badfile": False}})
                            break
                        except:
                            pass
                while not has_pwd:
                    pwd = _NONE
                    while not pwd:
                        pwd = askstring(title='请输入密码', prompt="Zip File: " + _filename + "\n输入\"skip\"跳过此文件")
                    if pwd == "skip":
                        PWD_JSON.update({file_md5:{"password": "", "badfile": False}})
                        return False
                    try:
                        t_cps_file.setpassword(pwd.encode("utf-8"))
                        t_cps_file.open(t_list[0])
                        has_pwd = True
                        PWD_JSON.update({file_md5:{"password": pwd, "badfile": False}})
                    except Exception as ex:
                        print(ex)
                        print("Password is WRONG !")
        return t_cps_file

    def openRarFile(self, _file_pos):
        global FILE_LIST
        global PWD_JSON

        _filename = FILE_LIST[_file_pos]["filename"]
        _file_uri = FILE_LIST[_file_pos]["fileUri"]

        if not os.path.exists(_file_uri + _filename):
            print("error:fileURI not exists")
            exit()
        # st = time.time()
        if USE_FILE_MD5:
            file_md5 = self.getFileMD5(_file_uri + _filename)
        else:
            file_md5 = self.getStringMD5(_file_uri + _filename)
        # print("getFileMD5: %f"%(time.time() - st))

        try:
            if PWD_JSON[file_md5]["badfile"]:
                return False
        except:
            pass
        try:
            t_cps_file = rarfile.RarFile(_file_uri + _filename)
        except:
            print(_filename + " open fail")
            return False
        if t_cps_file.infolist():
            t_list = self.getImageList(t_cps_file)
            if not t_list:
                return False

        if t_cps_file.needs_password():
            pwd = _NONE
            s_reload = True
            try:
                pwd = PWD_JSON[file_md5]["password"]
                if not pwd:
                    raise Exception
                t_cps_file.setpassword(pwd)
                # t_cps_file.read(t_cps_file.infolist()[0])
                # t_cps_file.testrar()
                s_reload = False
            except:
                has_pwd = False
                try:
                    pwd_default = PWD_JSON["defaultPassword"]
                except:
                    pwd_default = []
                if pwd_default:
                    for p in pwd_default:
                        try:
                            t_cps_file.setpassword(p)
                            # t_cps_file.read(t_list[0])
                            t_cps_file.testrar()
                            has_pwd = True
                            pwd = p
                            PWD_JSON.update({file_md5:{"password": p, "badfile": False}})
                            break
                        except:
                            pass
                while not has_pwd:
                    pwd = _NONE
                    while not pwd:
                        pwd = askstring(title='请输入密码', prompt="RaR File: " + _filename + "\n输入\"skip\"跳过此文件")
                    if pwd == "skip":
                        PWD_JSON.update({file_md5:{"password": "", "badfile": False}})
                        return False
                    try:
                        t_cps_file.setpassword(pwd)
                        # t_cps_file.read(t_list[0])
                        t_cps_file.testrar()
                        has_pwd = True
                        PWD_JSON.update({file_md5:{"password": pwd, "badfile": False}})
                    except:
                        print("Password is WRONG !")

            # try:
            #    t_cps_file.testrar()
            # except:
            #    return False
            if s_reload:
                t_cps_file.close()
                t_cps_file = rarfile.RarFile(_file_uri + _filename)
                t_cps_file.setpassword(pwd)
                # CPS_FILE.testrar()
            if not self.getImageList(t_cps_file):
                return False
        return t_cps_file

class loadImgTh(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.mLoadingFilePos = -1
        self.nowLoadImgInfo = {}
        self.cpsFile = _NONE

    def run(self):
        global willLoadImgQueue
        global mImgLoadQueueLock

        while TRUE:
            if not willLoadImgQueue:
                continue
            if self.nowLoadImgInfo:
                # print("loadImgTh: start filename: %s" % (self.nowLoadImgInfo["imgInfo"].filename))
                try:
                    data = self.cpsFile.read(self.nowLoadImgInfo["imgInfo"])
                    try:
                        pil_image = PIL.Image.open(io.BytesIO(data))
                        # print(pil_image.mode)
                    except Exception as ex:
                        print(ex)
                        pil_image = BAD_FILE
                except Exception as ex:
                    print(ex)
                    # PWD_JSON.update({file_md5:{"password": "", "badfile": True}})
                    pil_image = BAD_FILE
                # print("Load Img Num: %d" % (self.nowLoadImgInfo["imgPos"]))
                # print("loadImgTh: over  filename: %s" % (self.nowLoadImgInfo["imgInfo"].filename))

            mImgLoadQueueLock.acquire()
            # if willLoadImgQueue["willLoadImgQueue"]:
            #     print("length of willLoadImgQueue: %d" % (len(willLoadImgQueue["willLoadImgQueue"])))
            if self.mLoadingFilePos == willLoadImgQueue["nowFilePos"]:
                if self.nowLoadImgInfo and (not willLoadImgQueue["imgCache"][self.nowLoadImgInfo["imgPos"]]):
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

def slide():
    # print ("slide")
    global slideLock
    while(True):
        slideLock.acquire()
        checkTmp = SLIDE_START
        slideLock.release()
        if checkTmp:
            ShowPic(NEXT_IMG)
            time.sleep(SLIDE_TIME)
        else:
            break

def ShowPic(value, jump_num=0):
    global changeImgLock
    global mImgPos

    changeImgLock.acquire()
    if value is BACK_IMG:
        mImgPos -= 1
    elif value is NEXT_IMG:
        mImgPos += 1
    elif value is JUMP_IMG:
        mImgPos = jump_num
    changeImgLock.release()

def changeFile(direct, jump_file=0):
    global label
    global ChangeFileFlag
    label.configure(image="")
    label['text'] = "Loading"

    ChangeFileLock.acquire()
    ChangeFileFlag["direct"] = direct
    if direct is JUMP_FILE:
        ChangeFileFlag["nowFilePos"] = jump_file
    ChangeFileLock.release()

def mouseEvent(ev):
    global nTime
    nTime = time.time()
    global slideT
    global SLIDE_START
    if ev.x > root.winfo_width() / 3.0 * 2.0:
        ShowPic(NEXT_IMG)
    elif ev.x < root.winfo_width() / 3.0:
        ShowPic(BACK_IMG)
    elif ev.y > root.winfo_height() / 3.0 * 2.0:
        if slideT.isAlive():
            slideLock.acquire()
            SLIDE_START = False
            slideLock.release()
        changeFile(NEXT_FILE)
    elif ev.y < root.winfo_height() / 3.0:
        if slideT.isAlive():
            slideLock.acquire()
            SLIDE_START = False
            slideLock.release()
        changeFile(BACK_FILE)
    else:
        if slideT.isAlive():
            slideLock.acquire()
            SLIDE_START = False
            slideLock.release()
        else:
            slideLock.acquire()
            SLIDE_START = True
            slideLock.release()
            slideT = threading.Timer(0, slide)
            slideT.start()

def onKeyPress(ev):
    global nTime
    nTime = time.time()
    global slideT
    global SLIDE_START
    print(ev.keycode)
    if ev.keycode == 39:
        if slideT.isAlive():
            slideLock.acquire()
            SLIDE_START = False
            slideLock.release()
        else:
            slideLock.acquire()
            SLIDE_START = True
            slideLock.release()
            slideT = threading.Timer(0, slide)
            slideT.start()
        return

    if slideT.isAlive():
            slideLock.acquire()
            SLIDE_START = False
            slideLock.release()

    if ev.keycode == 113:
        ShowPic(BACK_IMG)
    elif ev.keycode == 114:
        ShowPic(NEXT_IMG)
    elif ev.keycode == 40 or ev.keycode == 116:
        changeFile(NEXT_FILE)
    elif ev.keycode == 38 or ev.keycode == 111:
        changeFile(BACK_FILE)
    elif ev.keycode == 33:
        global SLIDE_TIME
        t_slide_time = askstring(title='设置幻灯片时间', prompt="当前时间: %d" % (SLIDE_TIME))
        try:
            t_slide_time = int(t_slide_time)
            SLIDE_TIME = max([1, t_slide_time])
        except:
            print("输入错误")
            # showerror(title="错误", message="输入错误！")
    elif ev.keycode == 25:
        jump_num = askstring(title='文件跳转', prompt="请输入跳转到的文件序号: ")
        try:
            jump_num = int(jump_num)
            jump_num = max([1, jump_num])
            jump_num = min([len(FILE_LIST), jump_num])
            changeFile(JUMP_FILE, jump_file=jump_num - 1)
        except:
            showerror(title="错误", message="输入错误！")
    elif ev.keycode == 26:
        jump_num = askstring(title='图片跳转', prompt="请输入跳转到的图片序号: ")
        try:
            jump_num = int(jump_num)
            jump_num = max([1, jump_num])
            ShowPic(JUMP_IMG, jump_num=jump_num - 1)
        except:
            print("输入错误")
    elif ev.keycode == 27:
        if askquestion(title="乱序浏览", message="是否打乱图片顺序?") == YES:
            changeImgLock.acquire()
            global RandomLoadImgFlag
            RandomLoadImgFlag = True
            changeImgLock.release()
    elif ev.keycode == 54:
        if askquestion(title="随机跳转", message="是否随机跳转到一个压缩包?") == YES:
            jump_num = random.randint(0, len(FILE_LIST))
            changeFile(JUMP_FILE, jump_file=jump_num)
    elif ev.keycode == 32:
        global ANTIALIAS_SHOW_IMG
        if ANTIALIAS_SHOW_IMG:
            if askquestion(title="抗锯齿", message="是否关闭抗锯齿?") == YES:
                ANTIALIAS_SHOW_IMG = False
        else:
            if askquestion(title="抗锯齿", message="是否开启抗锯齿?") == YES:
                ANTIALIAS_SHOW_IMG = True

def getFileList(file_uri, subfile=False):
    t_file_list = []
    if not file_uri.endswith("/"):
        file_uri += "/"
    fileNameList = os.listdir(file_uri)
    for sub_file_name in fileNameList:
        if (sub_file_name.endswith('rar') or sub_file_name.endswith('zip')):
            t_file_list.append({"filename": sub_file_name, "fileUri": file_uri, "CanRead": TRUE, "CurrentPos": 0})
        elif subfile and os.path.isdir(file_uri + sub_file_name):
            t_file_list += getFileList(file_uri + sub_file_name, subfile=True)
    return t_file_list


'''入口'''
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("800x600+%d+%d" % ((800 - root.winfo_width())/2, (600 - root.winfo_height())/2) )
    root.bind("<Button-1>", mouseEvent)
    root.bind("<Key>", onKeyPress)
    mWinChanged = False
    label = tk.Label(root, image=_NONE, width=600, height=550, font='Helvetica -18 bold')
    label.pack(padx=15, pady=15, expand=1, fill="both")

    if len(sys.argv) < 2:
        fd = LoadFileDialog(root, title="要打开的文件")
        MAIN_FILE_URI = fd.go()
        if MAIN_FILE_URI == _NONE:
            print("URI is wrong")
            exit()
        t_file_uri = MAIN_FILE_URI
    else:
        MAIN_FILE_URI = _NONE
        for uri in sys.argv[1:]:
            MAIN_FILE_URI += (uri + " ")
        MAIN_FILE_URI = MAIN_FILE_URI[:-1]
        t_file_uri = MAIN_FILE_URI
    MAIN_FILE_URI = "./"
    t_file_name = _NONE
    if os.path.isfile(MAIN_FILE_URI):
        t_file_name = MAIN_FILE_URI.split("/")[-1]
        MAIN_FILE_URI = MAIN_FILE_URI.replace(t_file_name, "")

    FILE_LIST = getFileList(MAIN_FILE_URI, subfile=askquestion(title="子文件夹", message="是否扫描子文件夹?") == YES)

    slideT = threading.Timer(0, slide)
    slideLock = threading.Lock()
    mImgLoadQueueLock = threading.Lock()
    changeImgLock = threading.Lock()
    ChangeFileLock = threading.Lock()
    SLIDE_START = False

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

    # 对旧版本保存的密码文件兼容
    if PWD_JSON:
        changed = False
        for key in PWD_JSON:
            if isinstance(PWD_JSON[key], str):
                PWD_JSON[key] = {"password": PWD_JSON[key], "badfile": False}
                changed = True
        if changed:
            t_pwd_json = json.dumps(PWD_JSON)
            with open('./Pwd.json', 'w') as f:
                f.write(t_pwd_json)

    ChangeFileFlag = {"nowFilePos": 0, "direct": CURRENT_FILE}
    RandomLoadImgFlag = False
    willLoadImgQueue = _NONE

    guardTask = guardTh()
    try:
        guardTask.nowFilePos = FILE_LIST.index({"filename": t_file_name, "fileUri": t_file_uri, "CanRead": TRUE})
    except:
        guardTask.nowFilePos = 0
    guardTask.setDaemon(TRUE)
    loadTask = loadImgTh()
    loadTask.setDaemon(TRUE)
    guardTask.start()
    loadTask.start()

    root.mainloop()
