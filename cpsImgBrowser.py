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
try:
    import Tkinter as tk
except:
    import tkinter as tk

BACK_IMG = 1
NEXT_IMG = 2
SLIDE_TIME = 3
USE_FILE_MD5 = False

def slide():
    print ("slide")
    global Lock
    while(True):
        Lock.acquire()
        checkTmp = SLIDE_START
        Lock.release()
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

def resize(w, h, w_box, h_box, pil_image):
    f1 = 1.0*w_box/w
    f2 = 1.0*h_box/h
    factor = min([f1, f2])
    width = int(w*factor)
    height = int(h*factor)
    return pil_image.resize((width, height), Image.ANTIALIAS)

def getImageList():
    tImgList = [info for info in CPS_FILE.infolist()
               if(info.filename.split('.')[-1] == 'jpg'
                  or info.filename.split('.')[-1] == 'png'
                  or info.filename.split('.')[-1] == 'gif')]
    return tImgList

def ShowPic(value):
    global mImgPos
    if(value == BACK_IMG):
        mImgPos -= 1
    elif(value == NEXT_IMG):
        mImgPos += 1
    mImgPos %= len(imgList)
    ShowAjoke(root, label)

def ShowAjoke(root,label):
    global mImgPos
    global mFilePos
    global fileList
    global imgList

    imgInfo = imgList[mImgPos]
    if (imgCache[mImgPos] == ""):
        if(mImgPos == 0):
            badFile = True
            while(badFile):
                try:
                    data = CPS_FILE.read(imgInfo)
                    badFile = False
                except Exception as ex:
                    #print("mFilePos" + str(mFilePos))
                    print("File Name: " + fileList[mFilePos])
                    #print(ex)
                    del fileList[mFilePos]
                    while(not openFile()):
                        del fileList[mFilePos]
                    imgInfo = imgList[mImgPos]
        else:
            data = CPS_FILE.read(imgInfo)
        pil_image = Image.open(io.BytesIO(data))
        imgCache[mImgPos] = pil_image
    else:
        pil_image = imgCache[mImgPos]
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
    pil_image_resized = resize(w, h, w_box, h_box, pil_image)
    wr, hr = pil_image_resized.size
    sf = "图片浏览器-%d/%d- %d/%d (%dx%d) %s --%s "%(mFilePos + 1, len(fileList), mImgPos + 1, IMG_SUM, wr, hr, fileName, fileList[mFilePos].encode("utf-8").decode("utf-8"))
    root.title(sf)

    tk_img = PhotoImage(pil_image_resized)
    label.configure(image = tk_img)
    label.image= tk_img

    label.pack(padx=5, pady=5)

def changePic(ev):
    if (ev.x > root.winfo_width() / 3.0 * 2.0):
        ShowPic(NEXT_IMG)
    elif(ev.x < root.winfo_width() / 3.0):
        ShowPic(BACK_IMG)

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
            Lock.acquire()
            SLIDE_START = False
            Lock.release()

        mFilePos += 1
        while(not openFile()):
            del fileList[mFilePos]
        ShowAjoke(root, label)
    elif(ev.keycode == 38):
        if (slideT.isAlive()):
            Lock.acquire()
            SLIDE_START = False
            Lock.release()

        mFilePos -= 1
        while(not openFile()):
            del fileList[mFilePos]
            mFilePos -= 1
        ShowAjoke(root, label)
    elif(ev.keycode == 43):
        if (slideT.isAlive()):
            Lock.acquire()
            SLIDE_START = False
            Lock.release()
        else:
            Lock.acquire()
            SLIDE_START = True
            Lock.release()
            slideT = threading.Timer(0, slide)
            slideT.start()

def openFile():
    #TODO:用对话框输入密码
    global mFilePos
    mFilePos %= len(fileList)
    #print(fileList[mFilePos])
    if(fileList[mFilePos].split('.')[-1].lower() == 'rar'):
        return openRarFile(mFilePos)
    elif(fileList[mFilePos].split('.')[-1].lower() == 'zip'):
        return openZipFile(mFilePos)

def openZipFile(mFilePos):
    global FILE_URI
    global CPS_FILE
    global imgCache
    global IMG_SUM
    global mImgPos
    global imgList
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
        CPS_FILE = zipfile.ZipFile(FILE_URI + fileList[mFilePos])
    except:
        print(fileList[mFilePos] + " open fail")
        return False
    if(len(CPS_FILE.infolist()) != 0):
        listT = getImageList()
        if(len(listT) == 0):
            return False
    try:
        CPS_FILE.testzip()
        needs_password = False
    except:
        needs_password = True

    if(needs_password):
        try:
            PWD = PWD_JSON[FILE_MD5]
            CPS_FILE.setpassword(PWD.encode("utf-8"))
            CPS_FILE.open(listT[0])
        except:
            hasPwd = False
            try:
                PWD_DEFAULT = PWD_JSON["defaultPassword"]
            except:
                PWD_DEFAULT = []
            if (not len(PWD_DEFAULT) == 0):
                for p in PWD_DEFAULT:
                    try:
                        CPS_FILE.setpassword(p.encode("utf-8"))
                        CPS_FILE.open(listT[0])
                        hasPwd = True
                        PWD_JSON.update({FILE_MD5: p})
                        pwdJson = json.dumps(PWD_JSON)
                        with open('./Pwd.json', 'w') as f:
                            f.write(pwdJson)
                        break
                    except:
                        pass
            while(not hasPwd):
                print("Zip File: " + fileList[mFilePos])
                PWD = input('Please input Password(input "skip" to skip): ')
                if(PWD == "skip"):
                    return False
                try:
                    CPS_FILE.setpassword(PWD.encode("utf-8"))
                    CPS_FILE.open(listT[0])
                    hasPwd = True
                    PWD_JSON.update({FILE_MD5: PWD})
                    pwdJson = json.dumps(PWD_JSON)
                    with open('./Pwd.json', 'w') as f:
                        f.write(pwdJson)
                except:
                    print("Password is WRONG !")
    imgList = getImageList()
    imgCache = ["" for i in range(len(imgList))]
    IMG_SUM = len(imgList)
    mImgPos = 0
    return True

def openRarFile(mFilePos):
    global FILE_URI
    global CPS_FILE
    global imgCache
    global IMG_SUM
    global mImgPos
    global imgList
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
        CPS_FILE = rarfile.RarFile(FILE_URI + fileList[mFilePos])
    except:
        print(fileList[mFilePos] + " open fail")
        return False
    if(len(CPS_FILE.infolist()) != 0):
        listT = getImageList()
        if(len(listT) == 0):
            return False

    if(CPS_FILE.needs_password()):
        PWD = ""
        sReload = True
        try:
            PWD = PWD_JSON[FILE_MD5]
            CPS_FILE.setpassword(PWD)
            #CPS_FILE.read(CPS_FILE.infolist()[0])
            #CPS_FILE.testrar()
            sReload = False
        except:
            hasPwd = False
            try:
                PWD_DEFAULT = PWD_JSON["defaultPassword"]
            except:
                PWD_DEFAULT = []
            if (not len(PWD_DEFAULT) == 0):
                for p in PWD_DEFAULT:
                    try:
                        CPS_FILE.setpassword(p)
                        #CPS_FILE.read(listT[0])
                        CPS_FILE.testrar()
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
                print("RAR File: " + fileList[mFilePos])
                PWD = input('Please input Password(input "skip" to skip): ')
                if(PWD == "skip"):
                    return False
                try:
                    CPS_FILE.setpassword(PWD)
                    #CPS_FILE.read(listT[0])
                    CPS_FILE.testrar()
                    hasPwd = True
                    PWD_JSON.update({FILE_MD5:PWD})
                    pwdJson = json.dumps(PWD_JSON)
                    with open('./Pwd.json','w') as f:
                        f.write(pwdJson)
                except:
                    print("Password is WRONG !")
        #try:
        #    CPS_FILE.testrar()
        #except:
        #    return False
        if(sReload):
            CPS_FILE.close()
            CPS_FILE = rarfile.RarFile(FILE_URI + fileList[mFilePos])
            CPS_FILE.setpassword(PWD)
            #CPS_FILE.testrar()

    imgList = getImageList()
    #while(len(imgList) == 0):
    #    CPS_FILE.close()
    #    CPS_FILE = rarfile.RarFile(FILE_URI + fileList[mFilePos])
    #    CPS_FILE.setpassword(PWD)
    #    CPS_FILE.testrar()
    imgCache = ["" for i in range(len(imgList))]
    IMG_SUM = len(imgList)
    mImgPos = 0
    return True

'''入口'''
if __name__ == '__main__':
    #TODO:用对话框输入路径
    FILE_URI = input("Please input uri: ")
    if (FILE_URI == ""):
        FILE_URI = "/media/bush/Download/IDM Downloads/Compressed/"

    fileList = os.listdir(FILE_URI)
    fileList = [f for f in fileList if (f.split('.')[-1].lower() == 'rar' or f.split('.')[-1].lower() == 'zip')]
    mFilePos = 0

    slideT = threading.Timer(0, slide)
    Lock = threading.Lock()
    SLIDE_START = False

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

    root = tk.Tk()
    root.geometry("800x600")
    root.bind("<Button-1>", changePic)
    root.bind("<Key>", onKeyPress)
    mWinChanged = False
    w_box = 600
    h_box = 550

    while(not openFile()):
        del fileList[mFilePos]

    label = tk.Label(root, image="", width=w_box, height=h_box)
    label.pack(padx=15, pady=15, expand = 1, fill = "both")
    ShowAjoke(root,label)
    root.mainloop()
