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

class LoadImgTh(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global mPosLock
        global imgCacheLock
        global CPS_FILELock
        global mImgPos
        global mFilePos
        global imC
        global fileList
        global imgList
        global CPS_FILE
        global imgCache

        self.nowImgPos = 0
        self.nowFilename = ""

        while(True):
            mPosLock.acquire()
            if(self.nowFilename != fileList[mFilePos]):
                self.nowFilename = fileList[mFilePos]
                self.nowImgPos = mImgPos
                imgCacheLock.acquire()
                imgCache = ["" for i in range(len(imgList))]
                imgCacheLock.release()
            else:
                if(mImgPos != self.nowImgPos):
                    self.nowImgPos = mImgPos
                else:
                    self.nowImgPos += 1
            mPosLock.release()

            #imgCacheLock.acquire()
            list_num = len(imgList)
            self.nowImgPos %= list_num
            n = 0
            while(imgCache[self.nowImgPos] != ""):
                n += 1
                self.nowImgPos += 1
                self.nowImgPos %= list_num
                if(n >= list_num):
                    break
            #imgCacheLock.release()

            CPS_FILELock.acquire()
            #st = time.time()
            data = CPS_FILE.read(imgList[self.nowImgPos])
            #print("%d LoadImg Time: %f" % (mImgPos, (time.time() - st)))
            pil_image = PIL.Image.open(io.BytesIO(data))
            CPS_FILELock.release()

            imgCacheLock.acquire()
            imgCache[self.nowImgPos] = pil_image
            imgCacheLock.release()

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
    global mImgPos
    global mPosLock
    mPosLock.acquire()
    if(value == BACK_IMG):
        mImgPos -= 1
    elif(value == NEXT_IMG):
        mImgPos += 1
    mImgPos %= len(imgList)
    mPosLock.release()
    ShowAjoke(root, label)

def ShowAjoke(root,label):
    StartTime = time.time()
    global imgCacheLock
    global mImgPos
    global mFilePos
    global fileList
    global imgList
    global imgCache

    imgInfo = imgList[mImgPos]

    imgCacheLock.acquire()
    pil_image = imgCache[mImgPos]
    imgCacheLock.release()
    while(pil_image == ""):
        time.sleep(1)
        imgCacheLock.acquire()
        pil_image = imgCache[mImgPos]
        imgCacheLock.release()

    fileName = imgInfo.filename.split('/')[-1]
    try:
        fileName = fileName.encode('cp437')
        fileName = fileName.decode("gbk")
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
    sf = "图片浏览器-%d/%d- %d/%d (%dx%d) %s --%s "%(mFilePos + 1, len(fileList), mImgPos + 1, IMG_SUM, wr, hr, fileName, fileList[mFilePos].encode("utf-8").decode("utf-8"))
    root.title(sf)

    tk_img = PIL.ImageTk.PhotoImage(pil_image_resized)
    label.configure(image = tk_img)
    label.image= tk_img
    label.pack(padx=5, pady=5)

    print("Sum Load Img Time: " + str(time.time() - StartTime))

def changePic(ev):
    global slideT
    global SLIDE_START
    global mFilePos
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
        ShowAjoke(root, label)
    elif(ev.y < root.winfo_height() / 3.0):
        if (slideT.isAlive()):
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()

        openFile(BACK_FILE)
        ShowAjoke(root, label)

def onKeyPress(ev):
    global slideT
    global SLIDE_START
    global mFilePos
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
        ShowAjoke(root, label)
    elif(ev.keycode == 38):
        if (slideT.isAlive()):
            slideLock.acquire()
            SLIDE_START = FALSE
            slideLock.release()

        openFile(BACK_FILE)
        ShowAjoke(root, label)
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

def openFile(direct):
    global mPosLock
    global CPS_FILELock
    global mFilePos
    global CPS_FILE
    global imgCache
    global IMG_SUM
    global imgList
    global mImgPos
    mPosLock.acquire()
    if(direct == NEXT_FILE):
        mFilePos += 1
    elif(direct == BACK_FILE):
        mFilePos -= 1
    mFilePos %= len(fileList)
    mPosLock.release()
    returnFruit = FALSE
    #print(fileList[mFilePos])
    if(fileList[mFilePos].split('.')[-1].lower() == 'rar'):
        returnFruit = openRarFile(mFilePos)
    elif(fileList[mFilePos].split('.')[-1].lower() == 'zip'):
        returnFruit = openZipFile(mFilePos)

    while(not returnFruit):
        mPosLock.acquire()
        del fileList[mFilePos]
        mFilePos += direct
        mFilePos %= len(fileList)
        mPosLock.release()
        if(fileList[mFilePos].split('.')[-1].lower() == 'rar'):
            returnFruit = openRarFile(mFilePos)
        elif(fileList[mFilePos].split('.')[-1].lower() == 'zip'):
            returnFruit = openZipFile(mFilePos)

    CPS_FILELock.acquire()
    CPS_FILE = returnFruit
    imgList = getImageList(CPS_FILE)
    CPS_FILELock.release()

    mPosLock.acquire()
    mImgPos = 0
    IMG_SUM = len(imgList)
    mPosLock.release()
    return returnFruit

def openZipFile(mFilePos):
    global FILE_URI
    global fileList
    global PWD_JSON

    if not os.path.exists(FILE_URI + fileList[mFilePos]):
        print("error:fileURI not exists")
        exit()
    #StartTime = time.time()
    if(USE_FILE_MD5):
        FILE_MD5 = getFileMD5(FILE_URI + fileList[mFilePos])
    else:
        FILE_MD5 = getStringMD5(FILE_URI + fileList[mFilePos])
    #print(time.time() - StartTime)

    try:
        tCPS_FILE = zipfile.ZipFile(FILE_URI + fileList[mFilePos])
    except:
        print(fileList[mFilePos] + " open fail")
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
                    PWD = askstring(title = '请输入密码',prompt = "Zip File: " + fileList[mFilePos] + "\n输入\"skip\"跳过此文件")
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

def openRarFile(mFilePos):
    global FILE_URI
    global fileList
    global PWD_JSON

    if not os.path.exists(FILE_URI + fileList[mFilePos]):
        print("error:fileURI not exists")
        exit()
    #st = time.time()
    if(USE_FILE_MD5):
        FILE_MD5 = getFileMD5(FILE_URI + fileList[mFilePos])
    else:
        FILE_MD5 = getStringMD5(FILE_URI + fileList[mFilePos])
    #print("getFileMD5: %f"%(time.time() - st))

    try:
        tCPS_FILE = rarfile.RarFile(FILE_URI + fileList[mFilePos])
    except:
        print(fileList[mFilePos] + " open fail")
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
                    PWD = askstring(title = '请输入密码',prompt = "RaR File: " + fileList[mFilePos] + "\n输入\"skip\"跳过此文件")
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
            tCPS_FILE = rarfile.RarFile(FILE_URI + fileList[mFilePos])
            tCPS_FILE.setpassword(PWD)
            #CPS_FILE.testrar()

    #while(len(imgList) == 0):
    #    tCPS_FILE.close()
    #    tCPS_FILE = rarfile.RarFile(FILE_URI + fileList[mFilePos])
    #    tCPS_FILE.setpassword(PWD)
    #    tCPS_FILE.testrar()
    return tCPS_FILE

'''入口'''
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("800x600+%d+%d" % ((800 - root.winfo_width())/2, (600 - root.winfo_height())/2) )
    root.bind("<Button-1>", changePic)
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

    fileList = os.listdir(FILE_URI)
    fileList = [f for f in fileList if (f.split('.')[-1].lower() == 'rar' or f.split('.')[-1].lower() == 'rar')]
    mFilePos = 0
    if(tFilename in fileList):
        mFilePos = fileList.index(tFilename)

    slideT = threading.Timer(0, slide)
    slideLock = threading.Lock()
    mPosLock = threading.Lock()
    imgCacheLock = threading.Lock()
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
    ShowAjoke(root,label)
    root.mainloop()
