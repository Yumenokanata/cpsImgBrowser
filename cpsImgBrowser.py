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
            time.sleep(0.08)
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
                self.nowFileInfo.Filename = FILE_LIST[self.nowFileInfo.FilePos]["filename"]
                try:
                    self.nowFileInfo.Filename = self.nowFileInfo.Filename.encode("cp437").decode("gbk")
                except:
                    pass
                    # self.nowFileInfo.Filename = self.nowFileInfo.Filename.encode("utf-8").decode("utf-8")
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
                imgName = imgName.replace("\\", "/")
                # imgName = imgName.split('/')[-1]
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
                    show_img_resize = self.resizePic(img_w, img_h, box_width, box_height, showImg)
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
        # t_test_list = ['aaa']
        divide_list = self.divideByFile(t_img_list, key=lambda x: x.filename)
        divide_list.sort(key=lambda x: x[0])
        t_img_list = []
        for t_l in divide_list:
            t_img_list += self.sortFileName(t_l[1], key=lambda x: x.filename)
        # print("Sort Time: %f / %d" % (time.time() - st4, len(t_img_list)))
        return t_img_list

    def divideByFile(self, t_list, key=lambda x: x):
        if not callable(key):
            return []
        uri_list = []
        files_dict = {' ':[]}
        for t_l in t_list:
            value = key(t_l)
            value = value.replace("\\", "/")
            uri = value.replace(value.split('/')[-1], '')
            if not uri:
                files_dict[' '].append(t_l)
            elif uri in uri_list:
                files_dict[uri].append(t_l)
            else:
                uri_list.append(uri)
                files_dict[uri] = [t_l]

        r_list = []
        for d in files_dict.items():
            r_list.append([d[0], d[1]])
        return r_list

    def printList(self, t_list):
        str1 = ""
        for n in t_list:
            str1 = str1 + str(n) + ","
        print(str1)

    def getEditDistance(self, a, b):
        len_a = len(a)
        len_b = len(b)
        d = [[0 for i in range(len_b)] for j in range(len_a)]
        for i in range(len_a):
            d[i][0] = i
        for j in range(len_b):
            d[0][j] = j

        for i in range(1, len_a):
            for j in range(1, len_b):
                if a[i] == b[j]:
                    d[i][j] = d[i - 1][j - 1]
                else:
                    d[i][j] = min( d[i - 1][j - 1] + 1,
                                   d[i - 1][j] + 1,
                                   d[i][j - 1] + 1)
        return d[len_a - 1][len_b - 1]

    def sortStringBySimilarity2(self, t_list, key=lambda x:x):
        if not callable(key):
            return []
        if not t_list:
            return []
        minString = key(t_list[0])
        minIndex = 0
        for i,l in enumerate(t_list):
            value = key(l)
            if value < minString:
                minString = value
                minIndex = i
        self.swap(t_list, 0, minIndex)

        l_len = len(t_list)
        for i in range(l_len - 1):
            minValue = key(t_list[i])
            minDistance = len(minValue)
            minIndex = i
            for j in range(i + 1, l_len):
                d = self.getEditDistance(minValue, key(t_list[j]))
                if d < minDistance:
                    d = minDistance
                    minIndex = j
            self.swap(t_list, i, minIndex)
        return t_list

    def sortStringBySimilarity(self, t_list, key=lambda x:x):
        print('self.n', self.n)
        self.n += 1
        if not callable(key):
            return []
        if (not t_list) or len(t_list) == 1:
            return t_list
        elif len(t_list) == 2:
            if key(t_list[0]) < key(t_list[1]):
                return [t_list[1], t_list[0]]
            else:
                return t_list
        minString = key(t_list[0])
        maxLen = 0
        for l in t_list:
            value = key(l)
            if value < minString:
                minString = value
            t_len = len(value)
            if maxLen < t_len:
                maxLen = t_len

        d_dict = {}.fromkeys(range(maxLen))
        for l in t_list:
            d = self.getEditDistance(minString, key(l))
            if d_dict[d]:
                d_dict[d].append(l)
            else:
                d_dict[d] = [l]

        # sorted(d_dict.items(), key=lambda x: x[0])
        sorted_list = []
        for t_d in d_dict.items():
            if not t_d[1]:
                continue

            t_d_len = len(t_d[1])
            if t_d_len == 1:
                sorted_list.append(t_d[1][0])
            elif t_d_len < 4:
                t_d_list = t_d[1]
                self.quickSort(t_d_list, 0, len(t_d_list) - 1, key=key)
                sorted_list += t_d_list
            else:
                sorted_list += self.sortStringBySimilarity(t_d[1], key)
                # t_d[1].sort(key=key)
                # sorted_list += t_d[1]
        return sorted_list

    def sortFileName(self, t_list, key=lambda x: x.filename):
        # self.n = 0
        # return self.sortStringBySimilarity(t_list, key)
        self.quickSort(t_list, 0, len(t_list) - 1, key=key)
        return t_list

    def quickSort(self, t_list, left, right, key=lambda x: x):
        if left < right:
            pivot = int((right + left) / 2)
            pivot = self.partition(t_list, left, right, pivot, key=key)
            self.quickSort(t_list, left, pivot - 1, key=key)
            self.quickSort(t_list, pivot + 1, right, key=key)

    def partition(self, t_list, left, right, pivot, key=lambda x: x):
        # print("partition:  left: %d right: %d pivot: %d" % (left, right, pivot))
        pivot_value = key(t_list[pivot])
        self.swap(t_list, pivot, right)
        pivot = left

        for i in range(left, right):
            if self.cmpString(pivot_value, key(t_list[i])):
                self.swap(t_list, i, pivot)
                pivot += 1
        self.swap(t_list, pivot, right)
        return pivot

    def cmpString(self, s1, s2):
        # Return one bigger than two
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
                    while pwd == '':
                        t_root = tk.Tk()
                        t_root.withdraw()
                        pwd = askstring(parent=t_root, title='请输入密码', prompt="Zip File: " + _filename + "\n输入\"skip\"跳过此文件")
                        t_root.destroy()
                    label['text'] = "Loading"
                    if pwd == "skip" or pwd == None:
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
                            # t_cps_file.open(t_cps_file.infolist()[0])
                            t_cps_file.testrar()
                            has_pwd = True
                            pwd = p
                            PWD_JSON.update({file_md5:{"password": p, "badfile": False}})
                            break
                        except:
                            pass
                while not has_pwd:
                    pwd = _NONE
                    while pwd == '':
                        t_root = tk.Tk()
                        t_root.withdraw()
                        pwd = askstring(parent=t_root, title='请输入密码', prompt="Rar File: " + _filename + "\n输入\"skip\"跳过此文件")
                        t_root.destroy()
                    label['text'] = "Loading"
                    if pwd == "skip" or pwd == None:
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

    def run(self):
        global willLoadImgQueue
        global mImgLoadQueueLock

        while TRUE:
            time.sleep(0.05)
            if not willLoadImgQueue:
                continue
            if self.nowLoadImgInfo:
                # print("loadImgTh: start filename: %s" % (self.nowLoadImgInfo["imgInfo"].filename))
                if self.fileClass is FILE_CLASS:
                    try:
                        pil_image = PIL.Image.open(self.nowLoadImgInfo["imgInfo"].uri)
                    except Exception as ex:
                        print(ex)
                        pil_image = BAD_FILE
                else:
                    try:
                        data = self.cpsFile.read(self.nowLoadImgInfo["imgInfo"])
                        pil_image = PIL.Image.open(io.BytesIO(data))
                    except Exception as ex:
                        print(ex)
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
    root.geometry("800x600+%d+%d" % ((800 - root.winfo_width()) / 2, (600 - root.winfo_height()) / 2) )
    root.bind("<Button-1>", mouseEvent)
    root.bind("<Key>", onKeyPress)
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
