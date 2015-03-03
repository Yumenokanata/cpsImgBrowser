#!/usr/bin/env python3
#coding=utf-8

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

BACK_IMG = 1
NEXT_IMG = 2
SLIDE_TIME = 3
USE_FILE_MD5 = FALSE
BACK_FILE = -1
NEXT_FILE = 0
CURRENT_FILE = 0

changePic = FALSE

class LoadImgTh(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        #global mPosLock
        global changeImgLock
        global CPS_FILELock
        global mFilePos
        global FILE_LIST
        global CPS_FILE
        global root
        global label
        global changePic
        global mImgPos

        self.nextLoadImgPos = 0
        self.nowFilePos = -1

        while(True):
            CPS_FILELock.acquire()
            if(self.nowFilePos != mFilePos):
                self.nowFilePos = mFilePos
                self.nowFilename = FILE_LIST[self.nowFilePos]["filename"].encode("utf-8").decode("utf-8")
                self.imgList = getImageList(CPS_FILE)
                self.imgCache = ["" for i in range(len(self.imgList))]
                changeImgLock.acquire()
                mImgPos = 0
                self.shouldReflashImg = TRUE
                changeImgLock.release()
                self.imgNum = len(self.imgList)
                self.nowShowImgPos = 0
                self.nextLoadImgPos = 0
                self.shouldLoadImg = TRUE
            else:
                changeImgLock.acquire()
                if(self.nowShowImgPos != mImgPos):
                    mImgPos %= len(self.imgList)
                    self.nowShowImgPos = mImgPos
                    self.shouldReflashImg = TRUE
                changeImgLock.release()

                if(self.imgCache[self.nowShowImgPos] == ""):
                    self.nextLoadImgPos = self.nowShowImgPos
                else:
                    self.nextLoadImgPos += 1
                    list_num = len(self.imgList)
                    self.nextLoadImgPos %= list_num
                    n = 0
                    while(self.imgCache[self.nextLoadImgPos] != ""):
                        n += 1
                        self.nextLoadImgPos += 1
                        self.nextLoadImgPos %= list_num
                        if(n >= list_num):
                            self.shouldLoadImg = FALSE
                            break

            if(self.shouldLoadImg):
                #st = time.time()
                self.nowImgInfo = self.imgList[self.nextLoadImgPos]
                data = CPS_FILE.read(self.nowImgInfo)
                #print("%d LoadImg Time: %f" % (self.nowShowImgPos, (time.time() - st)))
                try:
                    pil_image = PIL.Image.open(io.BytesIO(data))
                    print("Load Img: %d" % (self.nextLoadImgPos))
                    self.imgCache[self.nextLoadImgPos] = pil_image
                except Exception as ex:
                    print(ex)
            CPS_FILELock.release()

            if(self.shouldReflashImg):
                self.shouldReflashImg = FALSE
                imgName = self.imgList[self.nowShowImgPos].filename.split('/')[-1]
                try:
                    imgName = imgName.encode('cp437')
                    imgName = imgName.decode("gbk")
                except:
                    pass

                w, h = pil_image.size
                #print root.winfo_height()
                if(root.winfo_height() != 1):
                    scale = root.winfo_height() / 550.0
                else:
                    scale = 600 / 550.0
                w_box = 600 * scale
                h_box = 550 * scale
                #print h_box
                pil_image_resized = resizePic(w, h, w_box, h_box, pil_image)
                wr, hr = pil_image_resized.size
                titleS = "图片浏览器-%d/%d- %d/%d (%dx%d) %s --%s "%(self.nowFilePos + 1, len(FILE_LIST), self.nextLoadImgPos + 1, self.imgNum, wr, hr, imgName, self.nowFilename)
                root.title(titleS)

                tk_img = PIL.ImageTk.PhotoImage(pil_image_resized)
                label.configure(image = tk_img)
                label.image= tk_img
                label.pack(padx=5, pady=5)

                #print("Sum Load Img Time: " + str(time.time() - StartTime))

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
               if(info.filename.split('.')[-1] == 'jpg'
                  or info.filename.split('.')[-1] == 'png'
                  or info.filename.split('.')[-1] == 'gif')]
    return tImgList

def ShowPic(value):
    global changeImgLock
    global mImgPos
    changeImgLock.acquire()
    if(value == BACK_IMG):
        mImgPos -= 1
    elif(value == NEXT_IMG):
        mImgPos += 1
    changeImgLock.release()

def mouseEvent(ev):
    global slideT
    global SLIDE_START
    if (ev.x > root.winfo_width() / 3.0 * 2.0):
        ShowPic(NEXT_IMG)
    elif(ev.x < root.winfo_width() / 3.0):
        ShowPic(BACK_IMG)
    elif(ev.y > root.winfo_height() / 3.0 * 2.0):
        if (slideT.isAlive()):
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()
        openFile(NEXT_FILE)
    elif(ev.y < root.winfo_height() / 3.0):
        if (slideT.isAlive()):
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()
        openFile(BACK_FILE)

def onKeyPress(ev):
    global slideT
    global SLIDE_START
    #print(ev.keycode)
    if ( ev.keycode == 111 or ev.keycode == 113):
        ShowPic(BACK_IMG)
    elif(ev.keycode == 114 or ev.keycode == 116):
        ShowPic(NEXT_IMG)
    elif(ev.keycode == 40):
        if (slideT.isAlive()):
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()

        openFile(BACK_FILE)
    elif(ev.keycode == 38):
        if (slideT.isAlive()):
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()

        openFile(BACK_FILE)
    elif(ev.keycode == 43):
        if (slideT.isAlive()):
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()
        else:
            slideLock.acquire()
            SLIDE_START = True
            slideLock.release()
            slideT = threading.Timer(0, slide)
            slideT.start()

def nextCanReadFile(direct, nowFilePos):
    global FILE_LIST
    if(direct == NEXT_FILE):
        nowFilePos += 1
    elif(direct == BACK_FILE):
        nowFilePos -= 1
    nowFilePos %= len(FILE_LIST)
    while(FILE_LIST[nowFilePos]["CanRead"] == FALSE):
        if(direct == BACK_FILE):
            nowFilePos -= 1
        else:
            nowFilePos += 1
        nowFilePos %= len(FILE_LIST)
    return nowFilePos

def openFile(direct):
    global CPS_FILELock
    global mFilePos
    global CPS_FILE
    global FILE_LIST
    tFilePos = nextCanReadFile(direct, mFilePos)
    returnFruit = FALSE
    #print(FILE_LIST[tFilePos]["filename"])
    if(FILE_LIST[tFilePos]["filename"].split('.')[-1].lower() == 'rar'):
        returnFruit = openRarFile(tFilePos)
    elif(FILE_LIST[tFilePos]["filename"].split('.')[-1].lower() == 'zip'):
        returnFruit = openZipFile(tFilePos)

    while(not returnFruit):
        FILE_LIST[tFilePos]["CanRead"] = FALSE
        tFilePos = nextCanReadFile(direct, tFilePos)
        if(FILE_LIST[tFilePos]["filename"].split('.')[-1].lower() == 'rar'):
            returnFruit = openRarFile(tFilePos)
        elif(FILE_LIST[tFilePos]["filename"].split('.')[-1].lower() == 'zip'):
            returnFruit = openZipFile(tFilePos)

    CPS_FILELock.acquire()
    CPS_FILE = returnFruit
    mFilePos = tFilePos
    CPS_FILELock.release()

    return returnFruit

def openZipFile(tFilePos):
    global FILE_URI
    global FILE_LIST
    global PWD_JSON

    tFilename = FILE_LIST[tFilePos]["filename"]
    if not os.path.exists(FILE_URI + tFilename):
        print("error:fileURI not exists")
        exit()
    #StartTime = time.time()
    if(USE_FILE_MD5):
        FILE_MD5 = getFileMD5(FILE_URI + tFilename)
    else:
        FILE_MD5 = getStringMD5(FILE_URI + tFilename)
    #print(time.time() - StartTime)

    try:
        tCPS_FILE = zipfile.ZipFile(FILE_URI + tFilename)
    except:
        print(tFilename + " open fail")
        return FALSE
    if(len(tCPS_FILE.infolist()) != 0):
        listT = getImageList(tCPS_FILE)
        if(len(listT) == 0):
            return FALSE
    try:
        tCPS_FILE.testzip()
        needs_password = FALSE
    except:
        needs_password = True

    if(needs_password):
        try:
            PWD = PWD_JSON[FILE_MD5]
            tCPS_FILE.setpassword(PWD.encode("utf-8"))
            tCPS_FILE.open(listT[0])
        except:
            hasPwd = FALSE
            try:
                PWD_DEFAULT = PWD_JSON["defaultPassword"]
            except:
                PWD_DEFAULT = []
            if (not len(PWD_DEFAULT) == 0):
                for p in PWD_DEFAULT:
                    try:
                        tCPS_FILE.setpassword(p.encode("utf-8"))
                        tCPS_FILE.open(listT[0])
                        hasPwd = True
                        PWD_JSON.update({FILE_MD5: p})
                        pwdJson = json.dumps(PWD_JSON)
                        with open('./Pwd.json', 'w') as f:
                            f.write(pwdJson)
                        break
                    except:
                        pass
            while(not hasPwd):
                PWD = ""
                while(PWD == ""):
                    PWD = askstring(title = '请输入密码',prompt = "Zip File: " + tFilename + "\n输入\"skip\"跳过此文件")
                if(PWD == "skip"):
                    return FALSE
                try:
                    tCPS_FILE.setpassword(PWD.encode("utf-8"))
                    tCPS_FILE.open(listT[0])
                    hasPwd = True
                    PWD_JSON.update({FILE_MD5: PWD})
                    pwdJson = json.dumps(PWD_JSON)
                    with open('./Pwd.json', 'w') as f:
                        f.write(pwdJson)
                except Exception as ex:
                    print(ex)
                    print("Password is WRONG !")
    return tCPS_FILE

def openRarFile(tFilePos):
    global FILE_URI
    global FILE_LIST
    global PWD_JSON

    tFilename = FILE_LIST[tFilePos]["filename"]
    if not os.path.exists(FILE_URI + tFilename):
        print("error:fileURI not exists")
        exit()
    #st = time.time()
    if(USE_FILE_MD5):
        FILE_MD5 = getFileMD5(FILE_URI + tFilename)
    else:
        FILE_MD5 = getStringMD5(FILE_URI + tFilename)
    #print("getFileMD5: %f"%(time.time() - st))

    try:
        tCPS_FILE = rarfile.RarFile(FILE_URI + tFilename)
    except:
        print(tFilename + " open fail")
        return FALSE
    if(len(tCPS_FILE.infolist()) != 0):
        listT = getImageList(tCPS_FILE)
        if(len(listT) == 0):
            return FALSE

    if(tCPS_FILE.needs_password()):
        PWD = ""
        sReload = True
        try:
            PWD = PWD_JSON[FILE_MD5]
            tCPS_FILE.setpassword(PWD)
            #tCPS_FILE.read(tCPS_FILE.infolist()[0])
            #tCPS_FILE.testrar()
            sReload = FALSE
        except:
            hasPwd = FALSE
            try:
                PWD_DEFAULT = PWD_JSON["defaultPassword"]
            except:
                PWD_DEFAULT = []
            if (not len(PWD_DEFAULT) == 0):
                for p in PWD_DEFAULT:
                    try:
                        tCPS_FILE.setpassword(p)
                        #tCPS_FILE.read(listT[0])
                        tCPS_FILE.testrar()
                        hasPwd = True
                        PWD = p
                        PWD_JSON.update({FILE_MD5:p})
                        pwdJson = json.dumps(PWD_JSON)
                        with open('./Pwd.json','w') as f:
                            f.write(pwdJson)
                        break
                    except:
                        pass
            while(not hasPwd):
                PWD = ""
                while(PWD == ""):
                    PWD = askstring(title = '请输入密码',prompt = "RaR File: " + tFilename + "\n输入\"skip\"跳过此文件")
                if(PWD == "skip"):
                    return FALSE
                try:
                    tCPS_FILE.setpassword(PWD)
                    #tCPS_FILE.read(listT[0])
                    tCPS_FILE.testrar()
                    hasPwd = True
                    PWD_JSON.update({FILE_MD5:PWD})
                    pwdJson = json.dumps(PWD_JSON)
                    with open('./Pwd.json','w') as f:
                        f.write(pwdJson)
                except:
                    print("Password is WRONG !")
        #try:
        #    tCPS_FILE.testrar()
        #except:
        #    return FALSE
        if(sReload):
            tCPS_FILE.close()
            tCPS_FILE = rarfile.RarFile(FILE_URI + tFilename)
            tCPS_FILE.setpassword(PWD)
            #CPS_FILE.testrar()

    return tCPS_FILE

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
        if(FILE_URI == NONE):
            print("URI is wrong")
            exit()
        tFilename = FILE_URI.split("/")[-1]
        FILE_URI = FILE_URI.replace(tFilename, "")
    else:
        FILE_URI = ""
        for uri in sys.argv[1:]:
            FILE_URI += (uri + " ")
        FILE_URI = FILE_URI[:-1]
        tFilename = ""
        if(not FILE_URI[-1] == "/"):
            tFilename = FILE_URI.split("/")[-1]

    #FILE_URI = input("Please input uri: ")
    #if (FILE_URI == ""):
    #    FILE_URI = "/media/bush/Download/IDM Downloads/Compressed/"
    #mFilePos = 0

    fileNameList = os.listdir(FILE_URI)
    fileNameList = [f for f in fileNameList if (f.split('.')[-1].lower() == 'rar' or f.split('.')[-1].lower() == 'rar')]
    FILE_LIST = [{"filename": fn, "CanRead": TRUE} for fn in fileNameList]
    try:
        mFilePos = FILE_LIST.index({"filename": tFilename, "CanRead": TRUE})
    except:
        mFilePos = 0

    slideT = threading.Timer(0, slide)
    slideLock = threading.Lock()
    #mPosLock = threading.Lock()
    changeImgLock = threading.Lock()
    CPS_FILELock = threading.Lock()
    SLIDE_START = FALSE

    try:
        with open('./Pwd.json','r') as f:
            pwdJson = f.read()
    except:
        with open('./Pwd.json','w') as f:
            f.write('')
        pwdJson = ''
    try:
        PWD_JSON = json.JSONDecoder().decode(pwdJson)
    except:
        PWD_JSON = {}

    openFile(CURRENT_FILE)

    task = LoadImgTh()
    task.start()

    label = tk.Label(root, image="", width=w_box, height=h_box)
    label.pack(padx=15, pady=15, expand = 1, fill = "both")
    root.mainloop()
