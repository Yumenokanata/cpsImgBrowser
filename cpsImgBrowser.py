#!/usr/bin/env python3
# coding=utf-8

import io
import json
import os
import rarfile
import hashlib
import threading
import time
import zipfile
import random
import getpass
import platform
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
CPS_CLASS = 0
FILE_CLASS = 1
PLATFORM = platform.system()

class _KeyCode():
    def __init__(self, _platform):
        if platform.system() == 'Linux':
            self.codeA = 38
            self.codeS = 39
            self.codeD = 40
            self.codeW = 25
            self.codeE = 26
            self.codeR = 27
            self.codeC = 54
            self.codeLeft = 113
            self.codeRight = 114
            self.codeUp = 111
            self.codeDown = 116
            self.codeO = 32
            self.codeP = 33
            self.codeM = 58
        elif platform.system() == 'Windows':
            self.codeA = 65
            self.codeS = 83
            self.codeD = 68
            self.codeW = 87
            self.codeE = 69
            self.codeR = 82
            self.codeC = 67
            self.codeLeft = 37
            self.codeRight = 39
            self.codeUp = 38
            self.codeDown = 40
            self.codeO = 79
            self.codeP = 80
            self.codeM = 77

class _fileImgInfo():
    def __init__(self, filename=_NONE, uri=_NONE):
            self.filename = filename
            self.uri = uri

class guardTh(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.nextLoadImgPos = 0
        self.nowFileInfo = self._now_file_info()
        self.nowShowImgPos = 0
        self.imgCache = []
        self.imgList = []
        self.imgNum = 0
        self.shouldLoadImg = False
        self.shouldRefreshImg = False

    class _now_file_info():
        def __init__(self, pos=-1, filename=_NONE, file=_NONE, _class=CPS_CLASS):
            self.FilePos = pos
            self.Filename = filename
            self.File = file
            self.FileClass = _class

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
                FILE_LIST[self.nowFileInfo.FilePos]["CurrentPos"] = self.nowShowImgPos
                if ChangeFileFlag["direct"] is JUMP_FILE:
                    self.nowFileInfo.FilePos = ChangeFileFlag["nowFilePos"]
                ChangeFileFlag["direct"] = NOCHANGE_FILE
                ChangeFileLock.release()
                root.title("图片浏览器-Loading/%d" % len(FILE_LIST))
                mImgLoadQueueLock.acquire()
                if self.openFile(t_direct) is FILE_CLASS:
                    t_file_class = FILE_CLASS
                    self.imgList = self.getImageList(self.nowFileInfo.File, isfile=True)
                else:
                    t_file_class = CPS_CLASS
                    self.imgList = self.getImageList(self.nowFileInfo.File)
                self.nowShowImgPos = FILE_LIST[self.nowFileInfo.FilePos]["CurrentPos"]

                # print("self.nowShowImgPos: %d" % (self.nowShowImgPos))
                # print("Load File Time: " + str(time.time() - st1))
                self.nowFileInfo.Filename = FILE_LIST[self.nowFileInfo.FilePos]["filename"].encode("utf-8").decode("utf-8")
                changeImgLock.acquire()
                mImgPos = self.nowShowImgPos
                changeImgLock.release()
                self.imgCache = [_NONE for i in range(len(self.imgList))]
                self.imgNum = len(self.imgList)
                self.nextLoadImgPos = self.nowShowImgPos
                self.shouldLoadImg = TRUE
                self.shouldRefreshImg = TRUE
                willLoadImgQueue = {
                    "CPS_FILE": self.nowFileInfo.File,
                    "fileClass": t_file_class,
                    "nowFilePos": self.nowFileInfo.FilePos,
                    "imgCache": self.imgCache,
                    "willLoadImgQueue": []
                    }
                self.addQueue(self.nowShowImgPos)
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
                    self.addQueue(self.nowShowImgPos)
                    mImgLoadQueueLock.release()
                elif self.nowShowImgPos != mImgPos:
                    mImgPos %= len(self.imgList)
                    self.nowShowImgPos = mImgPos
                    self.shouldRefreshImg = TRUE

                    mImgLoadQueueLock.acquire()
                    self.addQueue(self.nowShowImgPos)
                    mImgLoadQueueLock.release()
                changeImgLock.release()

            if self.shouldRefreshImg and self.imgCache[self.nowShowImgPos]:
                # print("Change Img Time: %f " % (time.time() - nTime))
                mImgLoadQueueLock.acquire()
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
                    title = "图片浏览器-%d/%d- %d/%d (0x0) %s --%s " % (self.nowFileInfo.FilePos + 1,
                                                                 len(FILE_LIST),
                                                                 self.nowShowImgPos + 1,
                                                                 self.imgNum,
                                                                 imgName,
                                                                 self.nowFileInfo.Filename)
                    root.title(title)
                    mImgLoadQueueLock.release()
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
                    st5 = time.time()
                    show_img_resize = self.resizePic(img_w, img_h, box_width, box_height, showImg)
                    print("Load Resize Time: %f" % (time.time() - st5))
                else:
                    show_img_resize = showImg
                try:
                    tk_img = PIL.ImageTk.PhotoImage(show_img_resize)
                except:
                    show_img_resize = BAD_FILE

                if show_img_resize is BAD_FILE:
                    label.configure(image="")
                    label['text'] = "Bad Image"
                    title = "图片浏览器-%d/%d- %d/%d (0x0) %s --%s " % (self.nowFileInfo.FilePos + 1,
                                                                 len(FILE_LIST),
                                                                 self.nowShowImgPos + 1,
                                                                 self.imgNum,
                                                                 imgName,
                                                                 self.nowFileInfo.Filename)
                    root.title(title)
                    mImgLoadQueueLock.release()
                    continue

                wr, hr = show_img_resize.size
                title = "图片浏览器-%d/%d- %d/%d (%dx%d) %s --%s " % (self.nowFileInfo.FilePos + 1,
                                                                 len(FILE_LIST),
                                                                 self.nowShowImgPos + 1,
                                                                 self.imgNum,
                                                                 wr,
                                                                 hr,
                                                                 imgName,
                                                                 self.nowFileInfo.Filename)
                root.title(title)

                label['text']=""
                label.configure(image = tk_img)
                label.image = tk_img
                label.pack(padx=5, pady=5)

                # print("Sum Load Img Time: " + str(time.time() - st))
                mImgLoadQueueLock.release()

    def addQueue(self, start_pos):
        willLoadImgQueue["willLoadImgQueue"] = [{"imgInfo": self.imgList[start_pos],
                                                 "imgPos": start_pos}]
        list_num = len(self.imgList)
        for i in range(min([30, list_num])):
            t_nextLoadImgPos = (start_pos + i) % list_num
            willLoadImgQueue["willLoadImgQueue"].append({"imgInfo": self.imgList[t_nextLoadImgPos],
                                                         "imgPos": t_nextLoadImgPos})
            t_nextLoadImgPos = (start_pos - i) % list_num
            willLoadImgQueue["willLoadImgQueue"].append({"imgInfo": self.imgList[t_nextLoadImgPos],
                                                         "imgPos": t_nextLoadImgPos})

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
        try:
            if ANTIALIAS_SHOW_IMG:
                return pil_image.resize((width, height), PIL.Image.ANTIALIAS)
            else:
                return pil_image.resize((width, height))
        except:
            return BAD_FILE

    def getImageList(self, cps, isfile=False):
        if isfile:
            if not cps.endswith(FILE_SIGN):
                cps += FILE_SIGN
            file_name_list = os.listdir(cps)
            t_img_list = [_fileImgInfo(filename=fn, uri=cps + fn) for fn in file_name_list
                          if (fn[-3:].lower() == 'jpg'
                              or fn[-3:].lower() == 'png'
                              or fn[-3:].lower() == 'gif')]
            # TODO use uri to key
        else:
            t_img_list = [info for info in cps.infolist()
                       if(info.filename[-3:].lower() == 'jpg'
                          or info.filename[-3:].lower() == 'png'
                          or info.filename[-3:].lower() == 'gif')]
        # st4 = time.time()
        self.sortFileName(t_img_list)
        # print("Sort Time: %f / %d" % (time.time() - st4, len(t_img_list)))
        return t_img_list

    def printList(self, t_list):
        str1 = ""
        for n in t_list:
            str1 = str1 + str(n) + ","
        print(str1)

    def sortFileName(self, t_list):
        self.quickSort(t_list, 0, len(t_list) - 1)

    def quickSort(self, t_list, left, right):
        if left < right:
            pivot = int((right + left) / 2)
            pivot = self.partition(t_list, left, right, pivot)
            self.quickSort(t_list, left, pivot - 1)
            self.quickSort(t_list, pivot + 1, right)

    def partition(self, t_list, left, right, pivot):
        # print("partition:  left: %d right: %d pivot: %d" % (left, right, pivot))
        pivot_value = t_list[pivot].filename
        self.swap(t_list, pivot, right)
        pivot = left

        for i in range(left, right):
            if self.cmpString(pivot_value, t_list[i].filename):
                self.swap(t_list, i, pivot)
                pivot += 1
        self.swap(t_list, pivot, right)
        return pivot

    def cmpString(self, s1, s2):
        # Return one bigger than two
        # TODO File sort
        if s1.count(FILE_SIGN) != s1.count(FILE_SIGN):
            return s1.count(FILE_SIGN) > s1.count(FILE_SIGN)
        if s1.count(FILE_SIGN) > 0:
            for i,a in enumerate(s1.split(FILE_SIGN)):
                if a != s2.split(FILE_SIGN)[i]:
                    return a > s2.split(FILE_SIGN)[i]
        for i,a in enumerate(s1):
            try:
                if a != s2[i]:
                    isNum = 0
                    try:
                        n1 = int(a)
                        isNum += 1
                    except:
                        pass
                    try:
                        n2 = int(s2[i])
                        isNum += 1
                    except:
                        pass
                    if isNum > 0:
                        if len(s1) == len(s2):
                            return s1 > s2
                        else:
                            return len(s1) > len(s2)
                    else:
                        return s1 > s2
            except:
                if len(s1) == len(s2):
                    return s1 > s2
                else:
                    return len(s1) > len(s2)
        return True

    def swap(self, t_list, x, y):
        if x == y:
            return
        temp_value = t_list[x]
        t_list[x] = t_list[y]
        t_list[y] = temp_value

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

        file_pos = self.nextCanReadFile(direct, self.nowFileInfo.FilePos)

        if FILE_LIST[file_pos]["fileClass"] is FILE_CLASS:
            self.nowFileInfo.File = FILE_LIST[file_pos]["fileUri"]
            self.nowFileInfo.FilePos = file_pos
            self.nowFileInfo.FileClass = FILE_CLASS
            return FILE_CLASS
        return_fruit = False
        # print(FILE_LIST[file_pos]["filename"])
        filename = FILE_LIST[file_pos]["filename"]
        file_uri = FILE_LIST[file_pos]["fileUri"]
        if filename[-3:].lower() == 'rar':
            return_fruit = self.openRarFile(file_pos)
        elif filename[-3:].lower() == 'zip':
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
            if filename[-3:].lower() == 'rar':
                return_fruit = self.openRarFile(file_pos)
            elif filename[-3:].lower() == 'zip':
                return_fruit = self.openZipFile(file_pos)

        t_pwd_json = json.dumps(PWD_JSON)
        with open('.' + FILE_SIGN + 'Pwd.json', 'w') as f:
            f.write(t_pwd_json)
        self.nowFileInfo.File = return_fruit
        self.nowFileInfo.FilePos = file_pos

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
                        if PLATFORM == 'Windows':
                            label.configure(image="")
                            label['text'] = "正在打开加密压缩文件：" + _filename + "\n请在命令行中按提示输入密码\n输入\"skip\"跳过此文件"
                            print("Zip File: " + _filename + "\n输入\"skip\"跳过此文件")
                            pwd = input('请输入密码: ')
                            sys.stdout.flush()
                        else:
                            pwd = askstring(title='请输入密码', prompt="Zip File: " + _filename + "\n输入\"skip\"跳过此文件")
                    label['text'] = "Loading"
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
                            t_cps_file.open(t_cps_file.infolist()[0])
                            #t_cps_file.testrar()
                            has_pwd = True
                            pwd = p
                            PWD_JSON.update({file_md5:{"password": p, "badfile": False}})
                            break
                        except:
                            pass
                while not has_pwd:
                    pwd = _NONE
                    while not pwd:
                        if PLATFORM == 'Windows':
                            label.configure(image="")
                            label['text'] = "正在打开加密压缩文件：" + _filename + "\n请在命令行中按提示输入密码\n输入\"skip\"跳过此文件"
                            print("Rar File: " + _filename + "\n输入\"skip\"跳过此文件")
                            pwd = input('请输入密码: ')
                            sys.stdout.flush()
                        else:
                            pwd = askstring(title='请输入密码', prompt="Rar File: " + _filename + "\n输入\"skip\"跳过此文件")
                    label['text'] = "Loading"
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
        self.fileClass = CPS_CLASS

    def LoadImg(self,t_imgInfo, t_fileClass, t_cpsFile):
        # TODO 大图优化
        # TODO gif
        # print("loadImgTh: start filename: %s" % (self.nowLoadImgInfo["imgInfo"].filename))
        if t_fileClass is FILE_CLASS:
            try:
                pil_image = PIL.Image.open(t_imgInfo["imgInfo"].uri)
            except Exception as ex:
                print(ex)
                pil_image = BAD_FILE
        else:
            try:
                data = t_cpsFile.read(t_imgInfo["imgInfo"])
                pil_image = PIL.Image.open(io.BytesIO(data))
            except Exception as ex:
                print(ex)
                pil_image = BAD_FILE
        # print("Load Img Num: %d" % (self.nowLoadImgInfo["imgPos"]))
        # print("loadImgTh: over  filename: %s" % (self.nowLoadImgInfo["imgInfo"].filename))
        return pil_image

    def run(self):
        global willLoadImgQueue
        global mImgLoadQueueLock

        while TRUE:
            if not willLoadImgQueue:
                continue
            if self.nowLoadImgInfo:
                pil_image = self.LoadImg(self.nowLoadImgInfo, self.fileClass, self.cpsFile)

            mImgLoadQueueLock.acquire()
            # if willLoadImgQueue["willLoadImgQueue"]:
            #     print("length of willLoadImgQueue: %d" % (len(willLoadImgQueue["willLoadImgQueue"])))
            if self.mLoadingFilePos == willLoadImgQueue["nowFilePos"]:
                if self.nowLoadImgInfo and (not willLoadImgQueue["imgCache"][self.nowLoadImgInfo["imgPos"]]):
                    willLoadImgQueue["imgCache"][self.nowLoadImgInfo["imgPos"]] = pil_image
            else:
                self.cpsFile = willLoadImgQueue["CPS_FILE"]
                self.mLoadingFilePos = willLoadImgQueue["nowFilePos"]
                self.fileClass = willLoadImgQueue["fileClass"]

            self.nowLoadImgInfo = _NONE
            while TRUE:
                if not willLoadImgQueue["willLoadImgQueue"]:
                    self.nowLoadImgInfo = _NONE
                    break
                self.nowLoadImgInfo = willLoadImgQueue["willLoadImgQueue"].pop(0)
                if not willLoadImgQueue["imgCache"][self.nowLoadImgInfo["imgPos"]]:
                    break
            mImgLoadQueueLock.release()


OPEN_FILE = 1
OPEN_URI = 0
USER_NAME = getpass.getuser()

class mountInfo():
    def __init__(self):
        pass

class fileInfo():
    def __init__(self, path):
        # print(type(path))
        if os.path.isdir(path):
            if not path.endswith('/'):
                path += '/'
            self.path = path
            self.filename = path.split('/')[-2]
            self.ctime = os.path.getctime(path)
            self.atime = os.path.getatime(path)
            self.size = 0
        elif os.path.isfile(path):
            self.path = path
            self.filename = path.split('/')[-1]
            self.ctime = os.path.getctime(path)
            self.atime = os.path.getatime(path)
            self.size = os.path.getsize(path)
        else:
            raise

class myTable(Canvas):

    def __init__(self, master=None, rowWidth=170, rowHeight=25, titleHeight=25, column=0, row=0, data=[], ):
        Canvas.__init__(self, master=master)
        self.column = column
        self.row = row
        self.tableData = data
        self.tableRect = []
        self.rowWidth = rowWidth
        self.rowHeight = rowHeight
        self.titleHeight = titleHeight
        self.select_row = -1
        self.bind('<Double-Button-1>', self.onDoubleClick)
        self.bind('<Button-4>', self.mouseWheel, add='+')
        self.bind('<Button-5>', self.mouseWheel, add='+')
        self.bind('<Button-1>', self.onClick)
        self.scrollY = 0
        self.minScrollY = 0
        self.TableLines = []
        self.x_list = []
        self.columnWidthList = []
        self.titleCommand = None
        self.titlesRect = []
        self.titles = []
        self.tableCommand = None
        h = self.winfo_height()
        if h != 1:
            self.height = h
        else:
            self.height = None

        self.SELECT_COLOR = '#FF7F50'
        self.BLACK_COLOR = '#F5F5F5'
        self.WHITE_COLOR = 'white'
        self.TITLE_COLOR = '#D3D3D3'

    def draw(self):
        if self.tableRect:
            for row in self.tableRect:
                self.delete(row[0])
                for col in row[1]:
                    self.delete(col)
        if self.TableLines:
            for t_line in self.TableLines:
                self.delete(t_line)
        self.tableRect = []
        self.TableLines = []
        if self.height:
            h = self.height
        else:
            h = 600
        self.tableRect = []
        for row in range(self.row):
            t_rowList = []
            if row % 2 == 1:
                bg = self.WHITE_COLOR
            else:
                bg = self.BLACK_COLOR
            tag = 'r' + str(row)
            t_x = 2
            t_y = self.scrollY + self.titleHeight + row * self.rowHeight
            t_width = 2 + self.x_list[-1] + self.columnWidthList[-1]
            t_height = self.rowHeight
            if t_y > 0:
                if t_y > h:
                    break
                t_rect = self.create_rectangle(t_x,
                                               t_y,
                                               t_x + t_width,
                                               t_y + t_height,
                                               width=1,
                                               tags=tag,
                                               fill=bg)
                # self.tag_bind(tag, '<Button-1>', self.onClick)
                for col in range(self.column):
                    t_text = self.create_text(10 + self.x_list[col],
                                              3 + t_y,
                                              anchor='nw',
                                              text=self.tableData[row][col])
                    t_rowList.append(t_text)
                self.tableRect.append([t_rect, t_rowList, t_x, t_y, row])
        for col in range(1, self.column):
            self.TableLines.append(self.create_line((1 + self.x_list[col], self.titleHeight, 1 + self.x_list[col], self.titleHeight + self.row * self.rowHeight)))

    def resetColumnSize(self, columnWidthList):
        # self.rowHeight = rowHeight
        # self.titleHeight = titleHeight
        x_list = []
        t_x_offset = 1
        if columnWidthList == []:
            for col_w in range(self.column):
                columnWidthList.append(self.rowWidth)
                x_list.append(t_x_offset)
                t_x_offset += self.rowWidth
        else:
            if self.column != len(columnWidthList):
                raise
            for col_w in columnWidthList:
                x_list.append(t_x_offset)
                t_x_offset += col_w
        self.columnWidthList = columnWidthList
        self.x_list = x_list

    def refreshTitle(self, titles=[]):
        if self.titlesRect:
            for t in self.titlesRect:
                self.delete(t[0])
                self.delete(t[1])
        if titles:
            self.titles = titles
        self.titlesRect = []
        for col in range(self.column):
            tag = 'bt' + str(col)
            t_rect = self.create_rectangle(1 + self.x_list[col],
                                           1,
                                           3 + self.x_list[col] + self.columnWidthList[col],
                                           self.titleHeight,
                                           width=2,
                                           tags=tag,
                                           outline=self.WHITE_COLOR,
                                           fill=self.TITLE_COLOR)
            t_text = self.create_text(10 + self.x_list[col] + self.columnWidthList[col] / 2,
                             self.titleHeight / 2,
                             anchor=CENTER,
                             text=self.titles[col])
            self.titlesRect.append([t_rect, t_text])

    def cleanData(self):
        if self.tableRect:
            for row in self.tableRect:
                self.delete(row[0])
                for col in row[1]:
                    self.delete(col)
        if self.TableLines:
            for t_line in self.TableLines:
                self.delete(t_line)
        self.tableRect = []
        self.TableLines = []
        self.row = 0
        self.tableData = []
        self.select_row = -1
        self.minScrollY = 0

    def setData(self, data, titles, columnWidthList=[], command=None):
        self.cleanData()

        self.scrollY = 0
        self.tableData = data
        self.row = len(data)
        self.column = len(titles)
        self.titleCommand = command
        self.titles = titles

        self.resetColumnSize(columnWidthList)
        if not data:
            return
        if len(data[0]) != len(titles):
            return

        h = self.winfo_height()
        if h != 1:
            self.height = h
            self.minScrollY = h - self.row * self.rowHeight - 2
        else:
            self.minScrollY = None

        # TODO
        self.draw()

        self.refreshTitle(titles)

    def addData(self, add_data):
        if not add_data:
            return
        if len(add_data[0]) != self.column:
            raise
        self.tableData += add_data
        if self.TableLines:
            for t_line in self.TableLines:
                self.delete(t_line)

        self.row += len(add_data)
        self.draw()

        for col in range(1, self.column):
            self.TableLines.append(self.create_line((1 + self.x_list[col],
                                                     self.scrollY + self.titleHeight,
                                                     1 + self.x_list[col],
                                                     self.scrollY + self.titleHeight + self.row * self.rowHeight)))

        self.refreshTitle()

        h = self.winfo_height()
        if h != 1:
            self.minScrollY = h - self.row * self.rowHeight - 2
        else:
            self.minScrollY = None

    def setDoubleButtonCallback(self, command):
        if callable(command):
            self.tableCommand = command

    def mouseWheel(self, event):
        if self.minScrollY == None:
            h = self.winfo_height()
            if h != 1:
                self.minScrollY = h - self.row * self.rowHeight - 2
            else:
                self.minScrollY = None
                return
        if self.minScrollY >= 0:
            return
        if event.num == 4:
            direct = 20
            if self.scrollY == 0:
                return
            elif self.scrollY + direct >= 0:
                direct = -self.scrollY
        elif event.num == 5:
            direct = -20
            if self.scrollY == self.minScrollY:
                return
            elif self.scrollY + direct <= self.minScrollY:
                direct = self.minScrollY - self.scrollY
        self.scrollY += direct

        self.draw()
        self.refreshTitle()
        # for row in range(len(self.tableRect)):
        #     t_rect = self.tableRect[row][0]
        #     t_rowList = self.tableRect[row][1]
        #     self.move(t_rect, 0, direct)
        #     for col in range(self.column):
        #         self.move(t_rowList[col], 0, direct)
        pass

    def onClick(self, event):
        self.clickEvent(event)

    def onDoubleClick(self, event):
        self.clickEvent(event, 1)

    def clickEvent(self, event, Mode=0):
        if event.y < self.titleHeight:
            n = 0
            while event.x > self.x_list[n] + self.columnWidthList[n]:
                n += 1
            if callable(self.titleCommand):
                self.titleCommand(n)
            return

        index = -1
        n = 0
        for i,t in enumerate(self.tableRect):
            if t[3] > event.y - self.titleHeight:
                index = n
                break
            n += 1
        if index == -1:
            return
        # row = int((event.y - self.scrollY - self.titleHeight) / self.rowHeight)
        if self.select_row != -1:
            if self.select_row % 2 == 1:
                bg = self.WHITE_COLOR
            else:
                bg = self.BLACK_COLOR
            for t_col in range(self.column):
                rt = self.tableRect[self.select_row][0]
                self.itemconfigure(rt, fill=bg)
        self.select_row = index

        rt = self.tableRect[index][0]
        self.itemconfigure(rt, fill=self.SELECT_COLOR)

        if Mode and callable(self.tableCommand):
            row = self.tableRect[index][4]
            data = [row, self.tableData[row]]
            self.tableCommand(data)

class openFileDialog():
    def printProtocol(self):
        print('WM_DELETE_WINDOW')
        self.openfileRoot.destroy()
        mImgLoadQueueLock.release()

    def __init__(self, master):
        mImgLoadQueueLock.acquire()
        self.REVERSE_FILE_TABLE = False
        self.nowFileList = None
        self.nowFilePath = None
        self.openFile(master)
        self.openfileRoot.protocol('WM_DELETE_WINDOW', self.printProtocol)

    def onDoubleClickFileTable(self, data):
        new_path = data[1][0]
        if new_path == '..':
            backUri()
            return
        if os.path.isdir(self.nowFilePath + new_path + '/'):
            self.nowFilePath = self.nowFilePath + new_path + '/'
            self.refreshFileListBox(self.nowFilePath)

    def refreshFileListBox(self, Path):
        self.nowFileList = self.getFileInfoList(Path)
        self.openfileRoot.mountFrame.fileTable.setData(self.getFileListTable(self.nowFileList[0]), columnWidthList=[250, 100, 150], titles=['文件名', '大小', '修改日期'], command=self.reSortFileList)
        self.openfileRoot.mountFrame.fileTable.addData(self.getFileListTable(self.nowFileList[1]))

    def reSortFileList(self, num):
        global REVERSE_FILE_TABLE
        global nowFileList
        if num == 0:
            nowFileList[0].sort(key=lambda x: x.filename, reverse=REVERSE_FILE_TABLE)
            nowFileList[1].sort(key=lambda x: x.filename, reverse=REVERSE_FILE_TABLE)
        if num == 1:
            nowFileList[1].sort(key=lambda x: x.size, reverse=REVERSE_FILE_TABLE)
        if num == 2:
            nowFileList[0].sort(key=lambda x: x.atime, reverse=REVERSE_FILE_TABLE)
            nowFileList[1].sort(key=lambda x: x.atime, reverse=REVERSE_FILE_TABLE)
        print('reSortFileList ',num)

        self.openfileRoot.mountFrame.fileTable.cleanData()
        if REVERSE_FILE_TABLE:
            t = [0, 1]
            REVERSE_FILE_TABLE = False
        else:
            t = [0, 1]
            REVERSE_FILE_TABLE = True
        for i in t:
            self.openfileRoot.mountFrame.fileTable.addData(self.getFileListTable(nowFileList[i]))

    def backUri(self):
        t_mlist = self.nowFilePath.split('/')[:-2]
        self.nowFilePath = '/'
        for m in t_mlist:
            if m != '':
                self.nowFilePath += (m + '/')

        self.refreshFileListBox(self.nowFilePath)

    def changeMount(self, event):
        t = self.openfileRoot.mountList.curselection()
        now_mount = self.openfileRoot.mountList.get(t)
        self.nowFilePath = '/media/' + USER_NAME + '/' + now_mount + '/'
        self.refreshFileListBox(self.nowFilePath)

    def changeFile(self, new_path):
        if new_path == '..':
            backUri()
            return
        self.nowFilePath = self.nowFilePath + new_path + '/'
        self.refreshFileListBox(self.nowFilePath)

    def getFileInfoList(self, path):
        if not os.path.isdir(path):
            raise
        if not path.endswith('/'):
            path += '/'
        mlist = os.listdir(path)
        pathList = []
        fileList = []
        for fn in mlist:
            if os.path.isdir(path + fn):
                pathList.append(fileInfo(path + fn))
            else:
                fileList.append(fileInfo(path + fn))
        pathList.sort(key=lambda x: x.filename)
        fileList.sort(key=lambda x: x.filename)
        nowFileInfoList = [pathList, fileList]
        return nowFileInfoList

    def getFileListTable(self, nowFileInfoList):
        # fileInfoTable = [['..', '', '']]
        fileInfoTable = []
        for fi in nowFileInfoList:
            if len(fi.filename) > 27:
                t_filename = fi.filename[:10] + '...' + fi.filename[-10:]
            else:
                t_filename = fi.filename

            l = ['字节', 'KB', 'MB', 'GB']
            t_size = fi.size
            if t_size:
                n = 0
                while n < 3 and t_size / 1024.0 > 1:
                    t_size /= 1024.0
                    n += 1
                t_size = ("%.1f"%(t_size)) + l[n]
            else:
                t_size = ''

            t_tome = time.strftime("%Y年%2m月%2d日", time.localtime(fi.atime))
            # print(t_filename)
            #fileInfoString = "%-25s| %-10s| %-13s|" % (t_filename, t_size, t_tome)
            # filenameList.append(t_filename)
            # fileSizeList.append(t_size)
            # fileATimeList.append(t_tome)
            fileInfoTable.append([t_filename, t_size, t_tome])
        # fileV.set(tuple(filenameList))
        # sizeV.set(tuple(fileSizeList))
        # atimeV.set(tuple(fileATimeList))
        return fileInfoTable

    def openFile(self, master):
        # TODO
        print('openFile')
        self.openfileRoot = Toplevel(master)
        self.openfileRoot.wm_attributes('-topmost',1)
        t_screen_width, t_screen_height = root.maxsize()
        self.openfileRoot.geometry("800x600+%d+%d" % ((t_screen_width - 800) / 2, (t_screen_height - 600) / 2))

        self.openfileRoot.uirFrame = Frame(self.openfileRoot)
        # openfileRoot.uirFrame.place(in_=openfileRoot, x=10, y=10, relwidth=0.9, anchor=NW)
        self.openfileRoot.uirFrame.pack(fill=X, expand=0, padx=5, pady=5)
        self.openfileRoot.uirFrame.backButton = Button(self.openfileRoot.uirFrame, text="后退", relief=FLAT, command=self.backUri, height=1)
        self.openfileRoot.uirFrame.backButton.pack(side=LEFT,padx=5)
        self.uriV = StringVar()
        self.openfileRoot.mUriEntry = Entry(self.openfileRoot.uirFrame, textvariable=self.uriV)
        self.openfileRoot.mUriEntry.bind('<Return>', )
        self.uriV.set(os.getcwd())
        self.openfileRoot.mUriEntry.pack(side=RIGHT, fill=X, expand=1)

        mountV = StringVar()
        self.openfileRoot.mountList = Listbox(self.openfileRoot, listvariable=mountV, selectmode=SINGLE)
        mList = os.listdir('/media/' + USER_NAME)
        for m in mList:
            self.openfileRoot.mountList.insert(END, m)
        self.openfileRoot.mountList.bind('<Double-Button-1>', self.changeMount)
        self.openfileRoot.m_scrollbar = Scrollbar(self.openfileRoot, orient=VERTICAL)
        self.openfileRoot.mountList['yscrollcommand'] = self.openfileRoot.m_scrollbar.set
        self.openfileRoot.m_scrollbar['command'] = self.openfileRoot.mountList.yview
        self.openfileRoot.mountList.pack(fill=Y, expand=0, side=LEFT)
        self.openfileRoot.m_scrollbar.pack(fill=Y, expand=0, side=LEFT)

        self.openfileRoot.mountFrame = Frame(self.openfileRoot,bg='red')
        self.openfileRoot.mountFrame.pack(fill=BOTH, expand=1, padx=5, pady=5, side=RIGHT)
        self.openfileRoot.mountFrame.fileTable = myTable(self.openfileRoot.mountFrame)
        self.openfileRoot.mountFrame.fileTable.pack(fill=BOTH, expand=1, side=LEFT)
        self.openfileRoot.mountFrame.fileTable.setDoubleButtonCallback(self.onDoubleClickFileTable)
        self.nowFilePath = os.getcwd()
        self.refreshFileListBox(self.nowFilePath)

def openFile(master, MODE):
    openFileDialog(master)

def rotateImg(MODE):
    print(MODE)

def mainUI(master):
    global mTwoViewMode
    master.menu = Menu(master)

    master.menu.filemenu = Menu(master)
    master.menu.filemenu.s_submenu = Menu(master)
    master.menu.add_cascade(label='文件',menu=master.menu.filemenu)
    master.menu.filemenu.add_command(label="打开文件...", command=lambda: openFile(master, OPEN_FILE))
    master.menu.filemenu.add_command(label="打开文件夹...", command=lambda: openFile(master, OPEN_URI))
    master.menu.filemenu.add_command(label="管理收藏库...", command=openFile)
    master.menu.filemenu.add_separator()
    master.menu.filemenu.add_command(label="文件属性...", command=openFile)
    master.menu.filemenu.add_command(label="密码管理...", command=openFile)
    master.menu.filemenu.add_command(label="首选项...", command=openFile)
    master.menu.filemenu.add_separator()
    master.menu.filemenu.add_cascade(label='打开最近', menu=master.menu.filemenu.s_submenu)
    master.menu.filemenu.s_submenu.add_command(label="清空最近")
    master.menu.filemenu.s_submenu.add_separator()
    master.menu.filemenu.add_separator()
    master.menu.filemenu.add_command(label="退出", command=openFile)

    master.menu.viewmenu = Menu(master)
    master.menu.add_cascade(label='查看',menu=master.menu.viewmenu)
    mTwoViewMode = IntVar()
    master.menu.viewmenu.add_checkbutton(variable=mTwoViewMode, label="双页模式",command=openFile)
    master.menu.viewmenu.add_separator()
    mViewMode = StringVar()
    master.menu.viewmenu.add_radiobutton(variable=mViewMode, label="最佳适应模式", command=openFile)
    master.menu.viewmenu.add_radiobutton(variable=mViewMode, label="适应宽度模式", command=openFile)
    master.menu.viewmenu.add_radiobutton(variable=mViewMode, label="适应高度模式", command=openFile)
    mViewMode.set('最佳适应模式')
    master.menu.viewmenu.add_separator()
    master.menu.viewmenu.add_command(label="顺时针旋转 90度", command=lambda: rotateImg(1))
    master.menu.viewmenu.add_command(label="逆时针旋转 90度", command=lambda: rotateImg(2))
    master.menu.viewmenu.add_command(label="旋转 180度", command=lambda: rotateImg(3))

    master.menu.jumpmenu = Menu(master)
    master.menu.add_cascade(label='跳转',menu=master.menu.jumpmenu)
    master.menu.jumpmenu.add_command(label="文件跳转...", command=openFile)
    master.menu.jumpmenu.add_command(label="文件随机跳转", command=openFile)
    master.menu.jumpmenu.add_separator()
    master.menu.jumpmenu.add_command(label="图片跳转...", command=openFile)
    master.menu.jumpmenu.add_command(label="图片随机跳转", command=openFile)
    master.menu.jumpmenu.add_separator()
    master.menu.jumpmenu.add_command(label="下一页", command=openFile)
    master.menu.jumpmenu.add_command(label="上一页", command=openFile)
    master.menu.jumpmenu.add_command(label="下一文件包", command=openFile)
    master.menu.jumpmenu.add_command(label="上一文件包", command=openFile)
    master.menu.jumpmenu.add_separator()
    mSlide = IntVar()
    master.menu.jumpmenu.add_checkbutton(variable=mSlide, label="放映幻灯片",command=openFile)
    mRandomSlide = IntVar()
    master.menu.jumpmenu.add_checkbutton(variable=mRandomSlide, label="随机播放模式", command=openFile)

    master.menu.bookmarkmenu = Menu(master)
    master.menu.add_cascade(label='书签',menu=master.menu.bookmarkmenu)
    master.menu.bookmarkmenu.add_command(label="添加书签", command=openFile)
    master.menu.bookmarkmenu.add_command(label="管理书签...", command=openFile)
    master.menu.bookmarkmenu.add_separator()

    master['menu'] = master.menu

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
    # TODO about和help
    # TODO 重开文件
    global nTime
    nTime = time.time()
    global slideT
    global SLIDE_START
    # print(ev.keycode)
    if ev.keycode == KEY_CODE.codeS:
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

    if ev.keycode == KEY_CODE.codeLeft:
        ShowPic(BACK_IMG)
    elif ev.keycode == KEY_CODE.codeRight:
        ShowPic(NEXT_IMG)
    elif ev.keycode == KEY_CODE.codeD or ev.keycode == KEY_CODE.codeDown:
        changeFile(NEXT_FILE)
    elif ev.keycode == KEY_CODE.codeA or ev.keycode == KEY_CODE.codeUp:
        changeFile(BACK_FILE)
    elif ev.keycode == KEY_CODE.codeP:
        global SLIDE_TIME
        t_slide_time = askstring(title='设置幻灯片时间', prompt="当前时间: %ds" % (SLIDE_TIME))
        try:
            t_slide_time = int(t_slide_time)
            SLIDE_TIME = max([1, t_slide_time])
        except:
            print("输入错误")
            # showerror(title="错误", message="输入错误！")
    elif ev.keycode == KEY_CODE.codeW:
        jump_num = askstring(title='文件跳转', prompt="请输入跳转到的文件序号: ")
        try:
            jump_num = int(jump_num)
            jump_num = max([1, jump_num])
            jump_num = min([len(FILE_LIST), jump_num])
            changeFile(JUMP_FILE, jump_file=jump_num - 1)
        except:
            showerror(title="错误", message="输入错误！")
    elif ev.keycode == KEY_CODE.codeE:
        jump_num = askstring(title='图片跳转', prompt="请输入跳转到的图片序号: ")
        try:
            jump_num = int(jump_num)
            jump_num = max([1, jump_num])
            ShowPic(JUMP_IMG, jump_num=jump_num - 1)
        except:
            print("输入错误")
    elif ev.keycode == KEY_CODE.codeR:
        if askquestion(title="乱序浏览", message="是否打乱图片顺序?") == YES:
            changeImgLock.acquire()
            global RandomLoadImgFlag
            RandomLoadImgFlag = True
            changeImgLock.release()
    elif ev.keycode == KEY_CODE.codeC:
        if askquestion(title="随机跳转", message="是否随机跳转到一个压缩包?") == YES:
            jump_num = random.randint(0, len(FILE_LIST))
            changeFile(JUMP_FILE, jump_file=jump_num)
    elif ev.keycode == KEY_CODE.codeO:
        global ANTIALIAS_SHOW_IMG
        if ANTIALIAS_SHOW_IMG:
            if askquestion(title="抗锯齿", message="是否关闭抗锯齿?") == YES:
                ANTIALIAS_SHOW_IMG = False
        else:
            if askquestion(title="抗锯齿", message="是否开启抗锯齿?") == YES:
                ANTIALIAS_SHOW_IMG = True
    elif ev.keycode == KEY_CODE.codeM:
        if PWD_JSON["defaultPassword"]:
            dpw = PWD_JSON["defaultPassword"][0]
            for pw in PWD_JSON["defaultPassword"][1:]:
                dpw = dpw + ";" + pw
        add_password = askstring(title='默认密码', prompt="请输入欲添加的可待测试默认密码: \n  1.以\";\"分隔多个\n  2.多余的空格也会被视为密码", initialvalue=dpw)
        try:
            add_password = add_password.split(";")
        except:
            return
        for ap in add_password:
            try:
                PWD_JSON["defaultPassword"].index(ap)
            except:
                PWD_JSON["defaultPassword"].append(ap)
        t_pwd_json = json.dumps(PWD_JSON)
        with open('.' + FILE_SIGN + 'Pwd.json', 'w') as f:
            f.write(t_pwd_json)

def getFileList(file_uri, subfile=False):
    t_file_list = []
    if not file_uri.endswith(FILE_SIGN):
        file_uri += FILE_SIGN
    fileNameList = os.listdir(file_uri)
    has_pic = False
    for sub_file_name in fileNameList:
        if sub_file_name[-3:].lower() == 'rar' or sub_file_name[-3:].lower() == 'zip':
            t_file_list.append({"filename": sub_file_name, "fileUri": file_uri, "fileClass": CPS_CLASS, "CanRead": TRUE, "CurrentPos": 0})
        elif sub_file_name[-3:].lower() == 'jpg' or sub_file_name[-3:].lower() == 'png' or sub_file_name[-3:].lower() == 'gif':
            has_pic = True
        elif subfile and os.path.isdir(file_uri + sub_file_name):
            t_file_list += getFileList(file_uri + sub_file_name, subfile=True)
    if has_pic:
        t_file_list.append({"filename": file_uri.split(FILE_SIGN)[-2], "fileUri": file_uri, "fileClass": FILE_CLASS, "CanRead": TRUE, "CurrentPos": 0})
    return t_file_list

'''入口'''
if __name__ == '__main__':
    if PLATFORM == 'Linux':
        FILE_SIGN = "/"
        KEY_CODE = _KeyCode('Linux')
    elif PLATFORM == 'Windows':
        FILE_SIGN = "\\"
        KEY_CODE = _KeyCode('Windows')

    root = tk.Tk()
    t_screen_width, t_screen_height = root.maxsize()
    root.geometry("800x600+%d+%d" % ((t_screen_width - 800) / 2, (t_screen_height - 600) / 2))
    root.bind("<Button-1>", mouseEvent)
    root.bind("<Key>", onKeyPress)
    mainUI(root)
    mWinChanged = False
    label = tk.Label(root, image=_NONE, width=600, height=550, font='Helvetica -18 bold')
    label.pack(padx=15, pady=15, expand=1, fill="both")

    if len(sys.argv) < 2:
        fd = FileDialog(root, title="要打开的文件")
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

    t_file_name = _NONE
    if os.path.isfile(MAIN_FILE_URI):
        t_file_name = MAIN_FILE_URI.split(FILE_SIGN)[-1]
        MAIN_FILE_URI = MAIN_FILE_URI.replace(t_file_name, "")

    FILE_LIST = getFileList(MAIN_FILE_URI, subfile=askquestion(title="子文件夹", message="是否扫描子文件夹?") == YES)

    slideT = threading.Timer(0, slide)
    slideLock = threading.Lock()
    mImgLoadQueueLock = threading.Lock()
    changeImgLock = threading.Lock()
    ChangeFileLock = threading.Lock()
    SLIDE_START = False

    try:
        with open('.' + FILE_SIGN + 'Pwd.json', 'r') as f:
            pwdJson = f.read()
    except:
        with open('.' + FILE_SIGN + 'Pwd.json', 'w') as f:
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
            with open('.' + FILE_SIGN + 'Pwd.json', 'w') as f:
                f.write(t_pwd_json)

    ChangeFileFlag = {"nowFilePos": 0, "direct": CURRENT_FILE}
    RandomLoadImgFlag = False
    willLoadImgQueue = _NONE

    guardTask = guardTh()
    try:
        guardTask.nowFilePos = FILE_LIST.index({"filename": t_file_name, "fileUri": t_file_uri, "fileClass":CPS_CLASS, "CanRead": TRUE})
    except:
        guardTask.nowFilePos = 0
    guardTask.setDaemon(TRUE)
    loadTask = loadImgTh()
    loadTask.setDaemon(TRUE)
    guardTask.start()
    loadTask.start()

    root.mainloop()
