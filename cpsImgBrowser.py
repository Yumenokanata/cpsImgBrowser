#!/usr/bin/env python3
#coding=utf-8

import io
import urllib
from PIL import Image
import PIL
from PIL.ImageTk import *
import json
try:
    import Tkinter as tk
except:
    import tkinter as tk
import os
import rarfile
import hashlib
import threading
import time
import zipfile

BACK_IMG = 1
NEXT_IMG = 2
SLIDE_TIME = 3

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
    return hashlib.md5(string).hexdigest()

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
    imgList = [info for info in CPS_FILE.infolist()
               if(info.filename.split('.')[-1] == 'jpg'
                  or info.filename.split('.')[-1] == 'png'
                  or info.filename.split('.')[-1] == 'gif')]
    #with open("img.txt",'r') as f:
    #    imglist = f.readlines()
    return imgList

def ShowPic(value):
    global postion
    if(value == BACK_IMG):
        postion -= 1
    elif(value == NEXT_IMG):
        postion += 1
    postion %= len(list)
    ShowAjoke(root,label,list[postion])

def ShowAjoke(root,label,imgInfo):
    global postion
    flieName = imgInfo.filename.split('\\')[-1].encode('utf-8')
    if (imgCache[postion] == ""):
        data = CPS_FILE.read(imgInfo)
        pil_image = Image.open(io.BytesIO(data))
        imgCache[postion] = pil_image
    else:
        pil_image = imgCache[postion]

    # get the size of the image
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
    sf = "图片浏览器-%d/%d- %d/%d (%dx%d) %s --%s "%(mFilePos, len(fileList), postion + 1, IMG_SUM, wr, hr, flieName, fileList[mFilePos])
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
        while(not openFile(mFilePos)):
            del fileList[mFilePos]
        ShowAjoke(root,label,list[postion])
    elif(ev.keycode == 38):
        if (slideT.isAlive()):
            Lock.acquire()
            SLIDE_START = False
            Lock.release()

        mFilePos -= 1
        while(not openFile(mFilePos)):
            del fileList[mFilePos]
            mFilePos -= 1
        ShowAjoke(root,label,list[postion])
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

def openFile(mFilePos):
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
    global postion
    global list
    global fileList

    if not os.path.exists(FILE_URI + fileList[mFilePos]):
        print("error:fileURI not exists")
        exit()
    #StartTime = time.time()
    FILE_MD5 = getFileMD5(FILE_URI + fileList[mFilePos])
    #print(time.time() - StartTime)

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

    CPS_FILE = zipfile.ZipFile(FILE_URI + fileList[mFilePos])
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
            CPS_FILE.setpassword(PWD)
            CPS_FILE.testzip()
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
                        CPS_FILE.testzip()
                        hasPwd = True
                        PWD_JSON.update({FILE_MD5: p})
                        pwdJson = json.dumps(PWD_JSON, ensure_ascii=False)
                        with open('./Pwd.json', 'w') as f:
                            f.write(pwdJson.encode('utf-8'))
                        break
                    except:
                        pass
            while(not hasPwd):
                print("Zip File: " + fileList[mFilePos])
                PWD = input('Please input Password(input "skip" to skip): ')
                if(PWD == "skip"):
                    return False
                try:
                    CPS_FILE.setpassword(PWD)
                    CPS_FILE.testzip()
                    hasPwd = True
                    PWD_JSON.update({FILE_MD5: PWD})
                    pwdJson = json.dumps(PWD_JSON,ensure_ascii=False)
                    with open('./Pwd.json', 'w') as f:
                        f.write(pwdJson.encode('utf-8'))
                except:
                    print("Password is WRONG !")
    list=getImageList()
    imgCache = ["" for i in range(len(list))]
    IMG_SUM = len(list)
    postion = 0
    return True

def openRarFile(mFilePos):
    global FILE_URI
    global CPS_FILE
    global imgCache
    global IMG_SUM
    global postion
    global list
    global fileList

    if not os.path.exists(FILE_URI + fileList[mFilePos]):
        print("error:fileURI not exists")
        exit()
    #StartTime = time.time()
    FILE_MD5 = getFileMD5(FILE_URI + fileList[mFilePos])
    #print(time.time() - StartTime)

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

    CPS_FILE = rarfile.RarFile(FILE_URI + fileList[mFilePos])
    if(len(CPS_FILE.infolist()) != 0):
        listT = getImageList()
        if(len(listT) == 0):
            return False

    if(CPS_FILE.needs_password()):
        PWD = ""
        try:
            PWD = PWD_JSON[FILE_MD5]
            CPS_FILE.setpassword(PWD)
            CPS_FILE.testrar()
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
                        CPS_FILE.testrar()
                        hasPwd = True
                        PWD_JSON.update({FILE_MD5:p})
                        pwdJson = json.dumps(PWD_JSON,ensure_ascii=False)
                        with open('./Pwd.json','w') as f:
                            f.write(pwdJson.encode('utf-8'))
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
                    CPS_FILE.testrar()
                    hasPwd = True
                    PWD_JSON.update({FILE_MD5:PWD})
                    pwdJson = json.dumps(PWD_JSON,ensure_ascii=False)
                    with open('./Pwd.json','w') as f:
                        f.write(pwdJson.encode('utf-8'))
                except:
                    print("Password is WRONG !")
        #try:
        #    CPS_FILE.testrar()
        #except:
        #    return False
        CPS_FILE.close()
        CPS_FILE = rarfile.RarFile(FILE_URI + fileList[mFilePos])
        CPS_FILE.setpassword(PWD)

    list=getImageList()
    imgCache = ["" for i in range(len(list))]
    IMG_SUM = len(list)
    postion = 0
    return True

'''入口'''
if __name__ == '__main__':
    FILE_URI = input("Please input uri: ")
    if (FILE_URI == ""):
        FILE_URI = "/media/bush/Download/IDM Downloads/Compressed/"

    fileList = os.listdir(FILE_URI)
    fileList = [f for f in fileList if (f.split('.')[-1].lower() == 'rar' or f.split('.')[-1].lower() == 'zip')]
    mFilePos = 0

    slideT = threading.Timer(0, slide)
    Lock = threading.Lock()
    SLIDE_START = False

    root = tk.Tk()
    root.geometry("800x600")
    root.bind("<Button-1>", changePic)
    root.bind("<Key>", onKeyPress)
    mWinChanged = False
    w_box = 600
    h_box = 550

    while(not openFile(mFilePos)):
        del fileList[mFilePos]

    label = tk.Label(root, image="", width=w_box, height=h_box)
    label.pack(padx=15, pady=15, expand = 1, fill = "both")
    ShowAjoke(root,label,list[postion])
    root.mainloop()
