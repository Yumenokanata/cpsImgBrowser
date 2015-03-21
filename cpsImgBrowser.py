#!/usr/bin/env python3
# coding=utf-8

from widget import *
import io
import urllib
import json
import os
import rarfile
import hashlib
import threading
import copy
import time
import zipfile
import random
import platform
import PIL
from PIL import Image
from PIL import ImageTk
import multiprocessing
# import imageTk
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

SUB_FILE_DEPTH = -1

BACK_FILE = -1
NEXT_FILE = 0
CURRENT_FILE = 1
NOCHANGE_FILE = 2
JUMP_FILE = 3
CHANGE_FILE = 4

BAD_FILE = "bad_file"

RANDOM_JUMP_IMG = False
RANDOM_LIST = [n for n in range(99999)]
random.shuffle(RANDOM_LIST)
RANDOM_LIST_LENGTH = 99999
RANDOM_LIST_INDEX = 0

CPS_CLASS = 0
FILE_CLASS = 1

IMG_NAME_MESSAGE = 0
IMG_NUM_MESSAGE = 1
FILE_NUM_MESSAGE = 2
FILE_NAME_MESSAGE = 3

MESSAGE_BAR_HEIGHT = 20
MESSAGE_BAR_IMG_NAME_WIDTH = 0.4
MESSAGE_BAR_IMG_NUM_WIDTH = 0.1
MESSAGE_BAR_FILE_NUM_WIDTH = 0.1
MESSAGE_BAR_FILE_NAME_WIDTH = 0.4

MANAGE_BAR_BUTTON_WIDTH = 20
MANAGE_BAR_LIST_WIDTH = 200

USE_FAVORITE_LIST = 1
USE_FILE_LIST = 2
USE_BOOKMARK_LIST = 3

NONE = 0
NEAREST = 0
ANTIALIAS = 1
LINEAR = 2
CUBIC = 3

SCALE_FIT_MODE_BOTH = 0
SCALE_FIT_MODE_WIDTH = 1
SCALE_FIT_MODE_HEIGHT = 2

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_SIZE_CHANGE = False

RIGHT_MENU_VISIBLE = False

CPU_COUNT = multiprocessing.cpu_count()

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


class _configData():
    def __init__(self, background='#d3d3d3',
                 customBackground='#d3d3d3',
                 restore=True,
                 restoreData={'filename':'', 'uri':'', 'imgPos': 0},
                 saveLatelyFileInfo=True,
                 latelyFileInfo=[],
                 scanSubFile=True,
                 scanSubFileDepth=-1,
                 defaultPassword=[],
                 useCache=True,
                 slideTime=3,
                 saveFilePassword=True,
                 useCustomSort=True,
                 scaleMode=NEAREST,
                 twoPageMode=False,
                 scaleFitMode=0,
                 mangaMode=False):
        self.background = background
        self.customBackground = customBackground
        self.restore = restore
        self.restoreData = restoreData
        self.saveLatelyFileInfo = saveLatelyFileInfo
        self.latelyFileInfo = latelyFileInfo
        self.scanSubFile = scanSubFile
        self.scanSubFileDepth = scanSubFileDepth
        self.defaultPassword = defaultPassword
        self.useCache = useCache
        self.slideTime = slideTime
        self.saveFilePassword = saveFilePassword
        self.useCustomSort = useCustomSort
        self.scaleMode = scaleMode
        self.twoPageMode = twoPageMode
        self.scaleFitMode = scaleFitMode
        self.mangaMode = mangaMode

    def getDataDict(self):
        return {'background': self.background,
                'customBackground': self.customBackground,
                'restore': self.restore,
                'restoreData': self.restoreData,
                'saveLatelyFileInfo': self.saveLatelyFileInfo,
                'latelyFileInfo': self.latelyFileInfo,
                'scanSubFile': self.scanSubFile,
                'scanSubFileDepth': self.scanSubFileDepth,
                'defaultPassword': self.defaultPassword,
                'useCache': self.useCache,
                'slideTime': self.slideTime,
                'saveFilePassword': self.saveFilePassword,
                'useCustomSort': self.useCustomSort,
                'scaleMode': self.scaleMode,
                'twoPageMode': self.twoPageMode,
                'scaleFitMode': self.scaleFitMode,
                'mangaMode': self.mangaMode}

    def setDataFromDict(self, dict):
        self.background = dict['background']
        self.customBackground = dict['customBackground']
        self.restore = dict['restore']
        self.restoreData = dict['restoreData']
        self.saveLatelyFileInfo = dict['saveLatelyFileInfo']
        self.latelyFileInfo = dict['latelyFileInfo']
        self.scanSubFile = dict['scanSubFile']
        self.scanSubFileDepth = dict['scanSubFileDepth']
        self.defaultPassword = dict['defaultPassword']
        self.useCache = dict['useCache']
        self.slideTime = dict['slideTime']
        self.saveFilePassword = dict['saveFilePassword']
        self.useCustomSort = dict['useCustomSort']
        self.scaleMode = dict['scaleMode']
        self.twoPageMode = dict['twoPageMode']
        self.scaleFitMode = dict['scaleFitMode']
        self.mangaMode = dict['mangaMode']

class _fileImgInfo():
    def __init__(self, filename=_NONE, uri=_NONE):
            self.filename = filename
            self.uri = uri

def getFileKey(uri):
    if USE_FILE_MD5:
        if not os.path.exists(uri):
            print("error:fileURI not exists")
            exit()
        md5file = open(uri, 'rb')
        md5 = hashlib.md5(md5file.read()).hexdigest()
        md5file.close()
        return md5
    else:
        return hashlib.md5(uri.encode("utf-8")).hexdigest()

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
        self.live = True
        self.twoPageMode = False
        # self.LoadImgPool = multiprocessing.Pool()
        self.filePipeList = []
        self.posQueueList = []
        self.imgQueue = multiprocessing.Queue()
        self.loadImgProcessList = []
        for i in range(CPU_COUNT):
            filePipe = multiprocessing.Queue()
            self.filePipeList.append(filePipe)
            posQueue = multiprocessing.Queue()
            self.posQueueList.append(posQueue)
            p = loadImgTh(filePipe, posQueue, self.imgQueue)
            p.start()

    class _now_file_info():
        def __init__(self, pos=-1, filename=_NONE, uri=None, file=_NONE, _class=CPS_CLASS):
            self.FilePos = pos
            self.Filename = filename
            self.File = file
            self.uri = uri
            self.FileClass = _class

    def finish(self):
        self.live = False

    def getNowFileInfo(self):
        global ChangeFileLock
        global mNowFileInfo

        ChangeFileLock.acquire()
        returnData = {'filename': mNowFileInfo['filename'],
                      'uri': mNowFileInfo['uri'],
                      'imgNum': self.imgNum}
        ChangeFileLock.release()
        return returnData

    def run(self):
        global mImgLoadQueueLock
        global changeImgLock
        global ChangeFileLock
        global ChangeFileFlag
        global willLoadImgQueue
        global OPEN_FILE_LIST
        global BOOKMARK_LIST
        global root
        global label
        global label2
        global mNowFileInfo
        global mNowImgInfo
        global InfoMessage
        global mConfigData
        global manageChecked
        global refreshManageBar
        global saveCurrentImg
        global deleteCurrentMark

        while self.live:
            time.sleep(0.08)
            ChangeFileLock.acquire()
            if not ChangeFileFlag["direct"] is NOCHANGE_FILE:
                t_direct = ChangeFileFlag["direct"]
                if not OPEN_FILE_LIST:
                    self.nowFileInfo.FilePos = -1
                    ChangeFileFlag["direct"] = NOCHANGE_FILE
                    mNowFileInfo['filename'] = ''
                    mNowFileInfo['uri'] = ''
                    mNowFileInfo['sumImgNum'] = 0
                    mNowFileInfo['fileClass'] = None
                    ChangeFileLock.release()
                    InfoMessage[IMG_NAME_MESSAGE].set('')
                    InfoMessage[IMG_NUM_MESSAGE].set('')
                    InfoMessage[FILE_NUM_MESSAGE].set('0/0')
                    InfoMessage[FILE_NAME_MESSAGE].set('No File')
                    self.imgList = []
                    self.nowShowImgPos = 0
                    self.nowFileInfo.Filename = None
                    self.nowFileInfo.uri = None
                    changeImgLock.acquire()
                    mNowImgInfo['imgPos'] = 0
                    changeImgLock.release()
                    self.imgCache = [_NONE for i in range(len(self.imgList))]
                    self.imgNum = 0
                    self.nextLoadImgPos = 0
                    self.shouldLoadImg = False
                    self.shouldRefreshImg = False
                    if self.loadImgProcess and self.loadImgProcess.is_alive():
                        self.loadImgProcess.finish()
                        self.loadImgProcess = None
                else:
                    if not (t_direct is CHANGE_FILE or mFileListMode is USE_BOOKMARK_LIST):
                        OPEN_FILE_LIST[self.nowFileInfo.FilePos]["CurrentPos"] = self.nowShowImgPos
                    self.nowShowImgPos = 0
                    if t_direct is JUMP_FILE:
                        self.nowFileInfo.FilePos = ChangeFileFlag["willFilePos"]
                    if t_direct is CHANGE_FILE:
                        self.nowFileInfo.FilePos = ChangeFileFlag["willFilePos"]
                        self.nowShowImgPos = ChangeFileFlag['imgPos']
                    ChangeFileFlag["direct"] = NOCHANGE_FILE
                    ChangeFileLock.release()
                    InfoMessage[IMG_NAME_MESSAGE].set('')
                    InfoMessage[IMG_NUM_MESSAGE].set('')
                    InfoMessage[FILE_NUM_MESSAGE].set('Loading/%d' % (len(OPEN_FILE_LIST)))
                    InfoMessage[FILE_NAME_MESSAGE].set('Loading')
                    if self.openFile(t_direct) is FILE_CLASS:
                        t_file_class = FILE_CLASS
                        self.imgList = self.getImageList(self.nowFileInfo.File[-1], isfile=True)
                    else:
                        t_file_class = CPS_CLASS
                        self.imgList = self.getImageList(self.nowFileInfo.File[-1])
                    self.nowFileInfo.FileClass = t_file_class
                    if not self.nowShowImgPos:
                        self.nowShowImgPos = OPEN_FILE_LIST[self.nowFileInfo.FilePos]["CurrentPos"]
                    mNowFileInfo['filename'] = OPEN_FILE_LIST[self.nowFileInfo.FilePos]["filename"]
                    mNowFileInfo['uri'] = OPEN_FILE_LIST[self.nowFileInfo.FilePos]["fileUri"]
                    mNowFileInfo['sumImgNum'] = self.imgNum
                    mNowFileInfo['fileClass'] = t_file_class
                    self.nowFileInfo.uri = mNowFileInfo['uri'] + mNowFileInfo['filename']


                    # print("self.nowShowImgPos: %d" % (self.nowShowImgPos))
                    # print("Load File Time: " + str(time.time() - st1))
                    self.nowFileInfo.Filename = OPEN_FILE_LIST[self.nowFileInfo.FilePos]["filename"]
                    try:
                        self.nowFileInfo.Filename = self.nowFileInfo.Filename.encode("cp437").decode("gbk")
                    except:
                        pass
                        # self.nowFileInfo.Filename = self.nowFileInfo.Filename.encode("utf-8").decode("utf-8")
                    changeImgLock.acquire()
                    mNowImgInfo['imgPos'] = self.nowShowImgPos
                    changeImgLock.release()
                    self.imgCache = [_NONE for i in range(len(self.imgList))]
                    self.imgNum = len(self.imgList)
                    self.nextLoadImgPos = self.nowShowImgPos
                    self.shouldLoadImg = TRUE
                    self.shouldRefreshImg = TRUE
                    self.clearImgQueue()
                    # for i in range(len(self.posQueueList)):
                    #     while not self.posQueueList[i].empty():
                    #         self.posQueueList[i].get()
                    for posQueue in self.posQueueList:
                        while not posQueue.empty():
                            posQueue.get()
                    for filePipe in self.filePipeList:
                        while not filePipe.empty():
                            filePipe.get()
                        filePipe.put(self.nowFileInfo.File[:-1])
                    self.addQueue(self.nowShowImgPos, self.nowFileInfo.File, self.nowFileInfo.FileClass, True)
                    print('asdasda')
                refreshManageBar = True
                if manageChecked == 1:
                    root.mainFrame.manageFrame.manageList.delete(0, END)
                    for info in self.imgList:
                        fn = info.filename.replace('\\', '/')
                        fn = fn.split('/')[-1]
                        try:
                            fn = fn.encode("cp437").decode("gbk")
                        except:
                            pass
                        root.mainFrame.manageFrame.manageList.insert(END, fn)
            else:
                ChangeFileLock.release()
                if self.imgList:
                    if mNowImgInfo['refresh']:
                        changeImgLock.acquire()
                        mNowImgInfo['refresh'] = False
                        mNowImgInfo['imgPos'] %= len(self.imgList)
                        self.nowShowImgPos = mNowImgInfo['imgPos']
                        self.shouldRefreshImg = TRUE
                        changeImgLock.release()
                        self.addQueue(self.nowShowImgPos, self.nowFileInfo.File, self.nowFileInfo.FileClass, False)

            if refreshManageBar:
                self.reloadManagebar()

            if saveCurrentImg:
                self.saveImg()

            if deleteCurrentMark:
                self.deleteBmark()

            st = time.time()
            if not self.imgQueue.empty():
                t_info = self.imgQueue.get()
                if t_info[3] != self.nowFileInfo.uri:
                    pass
                elif t_info[2] == "bad_file":
                    self.imgCache[t_info[0]] = BAD_FILE
                else:
                    try:
                        if t_info[1] == FILE_CLASS:
                            try:
                                self.imgCache[t_info[0]] = PIL.Image.open(t_info[2])
                            except:
                                self.imgCache[t_info[0]] = BAD_FILE
                        else:
                            self.imgCache[t_info[0]] = PIL.Image.open(io.BytesIO(t_info[2]))
                    except Exception as ex:
                        print(ex)
            # print('check imgQueue spend: %f.5' % (time.time() - st))

            if self.shouldRefreshImg and self.imgCache[self.nowShowImgPos]:
                if mConfigData.twoPageMode:
                    twoPageNum = (self.nowShowImgPos + 1) % self.imgNum
                # print("Change Img Time: %f " % (time.time() - nTime))
                if manageChecked == 1:
                    root.mainFrame.manageFrame.manageList.selection_clear(0, END)
                    root.mainFrame.manageFrame.manageList.selection_set(self.nowShowImgPos)

                st = time.time()
                self.shouldRefreshImg = False

                if mConfigData.twoPageMode:
                    isGoodImg = self.loadTwoPage(self.nowShowImgPos, twoPageNum)
                    if isGoodImg == 'Not load':
                        self.shouldRefreshImg = True
                        continue
                    changeImgLock.acquire()
                    if mNowImgInfo['direct'] is BACK_IMG:
                        if isGoodImg:
                            mNowImgInfo['used'] = 2
                            changeImgLock.release()
                        else:
                            if mNowImgInfo['step'] == 2:
                                mNowImgInfo['imgPos'] += 1
                                mNowImgInfo['imgPos'] %= self.imgNum
                                self.nowShowImgPos = mNowImgInfo['imgPos']
                            changeImgLock.release()
                            self.loadSinglePage(self.nowShowImgPos)
                    else:
                        if isGoodImg:
                            mNowImgInfo['used'] = 2
                            changeImgLock.release()
                        else:
                            changeImgLock.release()
                            self.loadSinglePage(self.nowShowImgPos)
                else:
                    self.loadSinglePage(self.nowShowImgPos)
                mNowImgInfo['step'] = 2

                # print("Sum Load Img Time: " + str(time.time() - st))

        for loadImgProcess in self.loadImgProcessList:
            if loadImgProcess and loadImgProcess.is_alive():
                loadImgProcess.finish()
                loadImgProcess.join()


    def loadSinglePage(self, imgPos):
        global label
        imgName = self.imgList[imgPos].filename
        imgName = self.checkImgName(imgName)
        global isShowManageList
        if isShowManageList:
            win_w = root.winfo_width() - MANAGE_BAR_BUTTON_WIDTH - MANAGE_BAR_LIST_WIDTH
        else:
            win_w = root.winfo_width() - MANAGE_BAR_BUTTON_WIDTH
        win_h = root.winfo_height() - MESSAGE_BAR_HEIGHT
        if win_h == 1:
            win_w = 800
            win_h = 600
        t_showImg = self.imgCache[self.nowShowImgPos]
        if mNowImgInfo['rotate']:
            t_showImg = t_showImg.rotate(mNowImgInfo['rotate'])
        reSize = self.getFitBoxSize(t_showImg, win_w, win_h, mConfigData.scaleFitMode)
        if not reSize:
            self.setImgMessage(False, imgName, imgPos)
            return False
        show_img_resize = self.resizePic(reSize[0], reSize[1], reSize[2], reSize[3], t_showImg)

        try:
            tk_img = PIL.ImageTk.PhotoImage(show_img_resize)
        except Exception as ex:
            print(ex)
            self.setImgMessage(False, imgName, imgPos)
            return False

        label['text']=""
        label.configure(image=tk_img)
        label.image = tk_img
        label2.configure(image="")
        setImgPlace(0, 0)
        self.setImgMessage(True, imgName, imgPos)
        changeImgLock.acquire()
        if mConfigData.scaleFitMode == SCALE_FIT_MODE_WIDTH and win_h < reSize[3]:
            scroll = (reSize[3] - win_h) / 2
            setImgPlace(0, scroll)
            mNowImgInfo['scrollX'] = 0
            mNowImgInfo['scrollY'] = scroll
        else:
            mNowImgInfo['scrollX'] = 0
            mNowImgInfo['scrollY'] = 0
        mNowImgInfo['imgSize'] = [reSize[0], reSize[1]]
        mNowImgInfo['boxSize'] = [reSize[2], reSize[3]]
        mNowImgInfo['used'] = 1
        mNowImgInfo['rotate'] = 0
        changeImgLock.release()
        return True

    def loadTwoPage(self, imgPos_a, imgPos_b):
        if imgPos_a == BAD_FILE or imgPos_b == BAD_FILE:
            return False
        imgName_a = self.imgList[imgPos_a].filename
        imgName_a = self.checkImgName(imgName_a)
        global isShowManageList
        if isShowManageList:
            win_w = root.winfo_width() - MANAGE_BAR_BUTTON_WIDTH - MANAGE_BAR_LIST_WIDTH
        else:
            win_w = root.winfo_width() - MANAGE_BAR_BUTTON_WIDTH
        win_h = root.winfo_height() - MESSAGE_BAR_HEIGHT
        if win_h == 1:
            win_w = 800
            win_h = 600

        t_showImg_a = self.imgCache[imgPos_a]
        reSize_a = self.getFitBoxSize(t_showImg_a, win_w / 2, win_h, SCALE_FIT_MODE_BOTH)
        if not reSize_a:
            return False
        if reSize_a[0] > reSize_a[1]:
            return False

        if not self.imgCache[imgPos_b]:
            return 'Not load'
        imgName_b = self.imgList[imgPos_b].filename
        imgName_b = self.checkImgName(imgName_b)
        t_showImg_b = self.imgCache[imgPos_b]
        reSize_b = self.getFitBoxSize(t_showImg_b, win_w / 2, win_h, SCALE_FIT_MODE_BOTH)
        if not reSize_b:
            return False
        if reSize_b[0] > reSize_b[1]:
            return False

        show_img_resize_a = self.resizePic(reSize_a[0], reSize_a[1], reSize_a[2], reSize_a[3], t_showImg_a)
        try:
            tk_img_a = PIL.ImageTk.PhotoImage(show_img_resize_a)
        except:
            return False
        show_img_resize_b = self.resizePic(reSize_b[0], reSize_b[1], reSize_b[2], reSize_b[3], t_showImg_b)
        try:
            tk_img_b = PIL.ImageTk.PhotoImage(show_img_resize_b)
        except:
            return False

        global mConfigData
        label['text']=""
        if mConfigData.mangaMode:
            label.configure(image=tk_img_b)
            label.image = tk_img_b
            label2.configure(image=tk_img_a)
            label2.image = tk_img_a
            self.setImgMessage(True, imgName_b + ' | ' + imgName_a, self.nowShowImgPos)
        else:
            label.configure(image=tk_img_a)
            label.image = tk_img_a
            label2.configure(image=tk_img_b)
            label2.image = tk_img_b
            self.setImgMessage(True, imgName_a + ' | ' + imgName_b, self.nowShowImgPos)
        setImgPlace(0, 0)
        return True

    def checkImgName(self, imgName):
        t_imgName = imgName.replace("\\", "/")
        t_imgName = t_imgName.split('/')[-1]
        try:
            t_imgName = t_imgName.encode('cp437')
            t_imgName = t_imgName.decode("gbk")
        except:
            pass
        return t_imgName

    def setImgMessage(self, isGoodImg, imgName, imgPos):
        if not isGoodImg:
            label.configure(image="")
            label2.configure(image="")
            label['text'] = "Bad Image"
            InfoMessage[IMG_NAME_MESSAGE].set(imgName)
            InfoMessage[IMG_NUM_MESSAGE].set('%d/%d' % (imgPos + 1, self.imgNum))
            InfoMessage[FILE_NUM_MESSAGE].set('%d/%d' % (self.nowFileInfo.FilePos + 1, len(OPEN_FILE_LIST)))
            InfoMessage[FILE_NAME_MESSAGE].set(self.nowFileInfo.Filename)
        else:
            setMessage(imgName,
                       '%d/%d' % (imgPos + 1, self.imgNum),
                       '%d/%d' % (self.nowFileInfo.FilePos + 1, len(OPEN_FILE_LIST)),
                       self.nowFileInfo.Filename)

    def getFitBoxSize(self, showImg, box_x, box_y, mode):
        if showImg is BAD_FILE:
            return False
        try:
            img_w, img_h = showImg.size
        except Exception as ex:
            print(showImg)
            print(ex)
            return
        if mode is SCALE_FIT_MODE_BOTH:
            scale = 1.0 * box_y / img_h
            if img_w * scale > box_x:
                scale = 1.0 * box_x / img_w
        elif mode is SCALE_FIT_MODE_HEIGHT:
            scale = 1.0 * box_y / img_h
        elif mode is SCALE_FIT_MODE_WIDTH:
            scale = 1.0 * box_x / img_w

        if scale <= 1:
            box_width = img_w * scale
            box_height = img_h * scale
        else:
            box_width = img_w
            box_height = img_h
        return [img_w, img_h, box_width, box_height]

    def resizePic(self, w, h, rw, rh, pil_image):
        if w == rw and h == rh:
            return pil_image
        global mConfigData
        f1 = 1.0 * rw / w
        f2 = 1.0 * rh / h
        factor = min([f1, f2])
        width = int(w * factor)
        height = int(h * factor)
        try:
            return pil_image.resize((width, height), mConfigData.scaleMode)
        except:
            return BAD_FILE

    def clearImgQueue(self):
        while not self.imgQueue.empty():
            self.imgQueue.get()

    def initPool(self):
        print('start')

    def addQueue(self, start_pos, file, fileClass, changeFile=True):
        print('add queue start')
        global mConfigData
        for posQueue in self.posQueueList:
            while not posQueue.empty():
                posQueue.get()
        add_queue = []
        if not self.imgCache[start_pos]:
            add_queue.append(start_pos)

        print('add queue')

        if mConfigData.useCache:
            if mConfigData.twoPageMode:
                list_num = len(self.imgList)
                t_nextLoadImgPos = (start_pos + 1) % list_num
                if not self.imgCache[t_nextLoadImgPos] and not t_nextLoadImgPos in add_queue:
                    add_queue.append(t_nextLoadImgPos)
                for i in range(1, min([5, list_num])):
                    t_nextLoadImgPos = (start_pos + i * 2) % list_num
                    if not self.imgCache[t_nextLoadImgPos] and not t_nextLoadImgPos in add_queue:
                        add_queue.append(t_nextLoadImgPos)
                    t_nextLoadImgPos = (start_pos + i * 2 +1) % list_num
                    if not self.imgCache[t_nextLoadImgPos] and not t_nextLoadImgPos in add_queue:
                        add_queue.append(t_nextLoadImgPos)
                    t_nextLoadImgPos = (start_pos - i * 2 + 1) % list_num
                    if not self.imgCache[t_nextLoadImgPos] and not t_nextLoadImgPos in add_queue:
                        add_queue.append(t_nextLoadImgPos)
                    t_nextLoadImgPos = (start_pos - i * 2) % list_num
                    if not self.imgCache[t_nextLoadImgPos] and not t_nextLoadImgPos in add_queue:
                        add_queue.append(t_nextLoadImgPos)
            else:
                list_num = len(self.imgList)
                for i in range(min([10, list_num])):
                    t_nextLoadImgPos = (start_pos + i) % list_num
                    if not self.imgCache[t_nextLoadImgPos] and not t_nextLoadImgPos in add_queue:
                        add_queue.append(t_nextLoadImgPos)
                    t_nextLoadImgPos = (start_pos - i) % list_num
                    if not self.imgCache[t_nextLoadImgPos] and not t_nextLoadImgPos in add_queue:
                        add_queue.append(t_nextLoadImgPos)
        if add_queue:
            # if not changeFile:
            #     self.LoadImgPool.join()
            #     for i in range(len(self.imgQueue)):
            #         if self.imgQueue[i] and self.imgQueue[i].ready():
            #             t_info = self.imgQueue[i].get()
            #             self.imgQueue[i] = ''
            #             for n, imgPos in enumerate(add_queue):
            #                 if i == imgPos:
            #                     add_queue.pop(n)
            #                     break
            #             if t_info[2] == "bad_file":
            #                 self.imgCache[t_info[0]] = BAD_FILE
            #             else:
            #                 try:
            #                     if t_info[1] == FILE_CLASS:
            #                         try:
            #                             self.imgCache[t_info[0]] = PIL.Image.open(t_info[2])
            #                         except:
            #                             self.imgCache[t_info[0]] = BAD_FILE
            #                     else:
            #                         self.imgCache[t_info[0]] = PIL.Image.open(io.BytesIO(t_info[2]))
            #                 except Exception as ex:
            #                     print(ex)
            print('add queue add')
            lenN = len(self.posQueueList)
            n = 0
            for pos in add_queue:
                self.posQueueList[n % lenN].put([self.imgList[pos], pos, self.nowFileInfo.uri])
                n += 1
            print('add queue over')

    def getImageList(self, cps, isfile=False):
        if isfile:
            if not cps.endswith(FILE_SIGN):
                cps += FILE_SIGN
            file_name_list = os.listdir(cps)
            t_img_list = [_fileImgInfo(filename=fn, uri=cps + fn) for fn in file_name_list
                          if (fn[-3:].lower() == 'jpg'
                              or fn[-3:].lower() == 'png'
                              or fn[-3:].lower() == 'gif')]
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
        global mConfigData
        for t_l in divide_list:
            if mConfigData.useCustomSort:
                t_img_list += self.sortFileName(t_l[1], key=lambda x: x.filename)
            else:
                t_img_list += sorted(t_l[1], key=lambda x: x.filename)
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
        global OPEN_FILE_LIST
        if direct is NEXT_FILE:
            now_file_pos += 1
        elif direct is BACK_FILE:
            now_file_pos -= 1
        now_file_pos %= len(OPEN_FILE_LIST)
        while OPEN_FILE_LIST[now_file_pos]["CanRead"] is False:
            if direct is BACK_FILE:
                now_file_pos -= 1
            else:
                now_file_pos += 1
            now_file_pos %= len(OPEN_FILE_LIST)
        return now_file_pos

    def openFile(self, direct):
        global st1
        st1 = time.time()
        global OPEN_FILE_LIST
        global PWD_JSON

        file_pos = self.nextCanReadFile(direct, self.nowFileInfo.FilePos)

        if OPEN_FILE_LIST[file_pos]["fileClass"] is FILE_CLASS:
            self.nowFileInfo.File = ['', OPEN_FILE_LIST[file_pos]["fileUri"] + OPEN_FILE_LIST[file_pos]['filename']]
            self.nowFileInfo.FilePos = file_pos
            self.nowFileInfo.FileClass = FILE_CLASS
            return FILE_CLASS
        return_fruit = False
        # print(FILE_LIST[file_pos]["filename"])
        filename = OPEN_FILE_LIST[file_pos]["filename"]
        file_uri = OPEN_FILE_LIST[file_pos]["fileUri"]
        if filename[-3:].lower() == 'rar':
            return_fruit = self.openRarFile(file_pos)
        elif filename[-3:].lower() == 'zip':
            return_fruit = self.openZipFile(file_pos)

        while not return_fruit:
            file_md5 = getFileKey(file_uri + filename)
            try:
                PWD_JSON[file_md5]
            except:
                PWD_JSON.update({file_md5:{"password": "", "badfile": True, "filename": filename, "uri": file_uri}})
            OPEN_FILE_LIST[file_pos]["CanRead"] = False
            file_pos = self.nextCanReadFile(direct, file_pos)
            filename = OPEN_FILE_LIST[file_pos]["filename"]
            file_uri = OPEN_FILE_LIST[file_pos]["fileUri"]
            if filename[-3:].lower() == 'rar':
                return_fruit = self.openRarFile(file_pos)
            elif filename[-3:].lower() == 'zip':
                return_fruit = self.openZipFile(file_pos)

        global mConfigData
        if mConfigData.saveFilePassword:
            t_pwd_json = json.dumps(PWD_JSON)
            with open('.' + FILE_SIGN + 'Pwd.json', 'w') as f:
                f.write(t_pwd_json)

        if mConfigData.saveLatelyFileInfo:
            try:
                i = mConfigData.latelyFileInfo.index({'filename': filename,
                                                      'uri': file_uri})
                t_info = mConfigData.latelyFileInfo.pop(i)
                mConfigData.latelyFileInfo.insert(0, t_info)
            except:
                if len(mConfigData.latelyFileInfo) > 10:
                    mConfigData.latelyFileInfo.pop(-1)
                mConfigData.latelyFileInfo.insert(0, {'filename': filename,
                                                      'uri': file_uri})
            global latelyMenu
            latelyMenu.delete(0, END)
            t_len = len(mConfigData.latelyFileInfo)
            if t_len > 0:
                latelyMenu.add_command(label=mConfigData.latelyFileInfo[0]['filename'], command=lambda: openLatelyFile(0))
            if t_len > 1:
                latelyMenu.add_command(label=mConfigData.latelyFileInfo[1]['filename'], command=lambda: openLatelyFile(1))
            if t_len > 2:
                latelyMenu.add_command(label=mConfigData.latelyFileInfo[2]['filename'], command=lambda: openLatelyFile(2))
            if t_len > 3:
                latelyMenu.add_command(label=mConfigData.latelyFileInfo[3]['filename'], command=lambda: openLatelyFile(3))

        self.nowFileInfo.File = return_fruit
        self.nowFileInfo.FilePos = file_pos

        return return_fruit

    def openZipFile(self, _file_pos):
        global OPEN_FILE_LIST
        global PWD_JSON
        global mConfigData

        _filename = OPEN_FILE_LIST[_file_pos]["filename"]
        _file_uri = OPEN_FILE_LIST[_file_pos]["fileUri"]

        if not os.path.exists(_file_uri + _filename):
            print("error:fileURI not exists")
            exit()
        # StartTime = time.time()
        file_md5 = getFileKey(_file_uri + _filename)
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
        t_pwd = ''
        if needs_password:
            try:
                pwd = PWD_JSON[file_md5]["password"]
                if not pwd:
                    raise Exception
                t_cps_file.setpassword(pwd.encode("utf-8"))
                t_cps_file.open(t_list[0])
                t_pwd = pwd.encode("utf-8")
                PWD_JSON[file_md5] = self.updateOldDataToNew(PWD_JSON[file_md5], _filename, _file_uri)
            except:
                has_pwd = False
                try:
                    pwd_default = mConfigData.defaultPassword
                except:
                    pwd_default = []
                if pwd_default:
                    for p in pwd_default:
                        try:
                            t_cps_file.setpassword(p.encode("utf-8"))
                            t_cps_file.open(t_list[0])
                            has_pwd = True
                            t_pwd = p.encode("utf-8")
                            PWD_JSON.update({file_md5:{"password": p, "badfile": False, "filename": _filename, "uri": _file_uri}})
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
                        PWD_JSON.update({file_md5:{"password": "", "badfile": False, "filename": _filename, "uri": _file_uri}})
                        return False
                    try:
                        t_cps_file.setpassword(pwd.encode("utf-8"))
                        t_cps_file.open(t_list[0])
                        has_pwd = True
                        t_pwd = pwd.encode("utf-8")
                        PWD_JSON.update({file_md5:{"password": pwd, "badfile": False, "filename": _filename, "uri": _file_uri}})
                    except Exception as ex:
                        print(ex)
                        print("Password is WRONG !")
        return [_file_uri + _filename, t_pwd, 'zip', t_cps_file]

    def openRarFile(self, _file_pos):
        global OPEN_FILE_LIST
        global PWD_JSON
        global mConfigData

        _filename = OPEN_FILE_LIST[_file_pos]["filename"]
        _file_uri = OPEN_FILE_LIST[_file_pos]["fileUri"]

        if not os.path.exists(_file_uri + _filename):
            print("error:fileURI not exists")
            exit()
        # st = time.time()
        file_md5 = getFileKey(_file_uri + _filename)
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

        pwd = _NONE
        if t_cps_file.needs_password():
            s_reload = True
            try:
                pwd = PWD_JSON[file_md5]["password"]
                if not pwd:
                    raise Exception
                t_cps_file.setpassword(pwd)
                # t_cps_file.read(t_cps_file.infolist()[0])
                # t_cps_file.testrar()
                PWD_JSON[file_md5] = self.updateOldDataToNew(PWD_JSON[file_md5], _filename, _file_uri)
                s_reload = False
            except:
                has_pwd = False
                try:
                    pwd_default = mConfigData.defaultPassword
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
                            PWD_JSON.update({file_md5:{"password": p, "badfile": False, "filename": _filename, "uri": _file_uri}})
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
                        PWD_JSON.update({file_md5:{"password": "", "badfile": False, "filename": _filename, "uri": _file_uri}})
                        return False
                    try:
                        t_cps_file.setpassword(pwd)
                        # t_cps_file.read(t_list[0])
                        t_cps_file.testrar()
                        has_pwd = True
                        PWD_JSON.update({file_md5:{"password": pwd, "badfile": False, "filename": _filename, "uri": _file_uri}})
                    except:
                        print("Password is WRONG !")

            # try:
            #    t_cps_file.testrar()
            # except:
            #    return False
            if s_reload:
                t_cps_file.close()
                t_cps_file = rarfile.RarFile(_file_uri + _filename)
                if pwd:
                    t_cps_file.setpassword(pwd)
                # CPS_FILE.testrar()
            if not self.getImageList(t_cps_file):
                return False
            t_cps_file.close()
        return [_file_uri + _filename, pwd, 'rar', t_cps_file]

    def updateOldDataToNew(self, info, filename, uri):
        try:
            info['filename']
            return info
        except:
            return {'password': info['password'], 'badfile': info['badfile'], 'filename': filename, 'uri': uri}

    def reloadManagebar(self):
        refreshManageBar = False
        if manageChecked == 0 and mFileListMode is USE_FILE_LIST:
            root.mainFrame.manageFrame.manageList.selection_clear(0, END)
            root.mainFrame.manageFrame.manageList.selection_set(self.nowFileInfo.FilePos)
        elif manageChecked == 1:
            root.mainFrame.manageFrame.manageList.delete(0, END)
            for info in self.imgList:
                fn = info.filename.replace('\\', '/')
                fn = fn.split('/')[-1]
                try:
                    fn = fn.encode("cp437").decode("gbk")
                except:
                    pass
                root.mainFrame.manageFrame.manageList.insert(END, fn)
            root.mainFrame.manageFrame.manageList.selection_clear(0, END)
            root.mainFrame.manageFrame.manageList.selection_set(self.nowShowImgPos)
        elif manageChecked == 2 and mFileListMode is USE_FAVORITE_LIST:
            root.mainFrame.manageFrame.manageList.selection_clear(0, END)
            root.mainFrame.manageFrame.manageList.selection_set(self.nowFileInfo.FilePos)
        elif manageChecked == 3 and mFileListMode is USE_BOOKMARK_LIST:
            root.mainFrame.manageFrame.manageList.selection_clear(0, END)
            root.mainFrame.manageFrame.manageList.selection_set(self.nowFileInfo.FilePos)

    def saveImg(self):
        t_sum = mNowFileInfo['sumImgNum']
        t_class = mNowFileInfo['fileClass']
        t_filename = mNowFileInfo['filename']
        t_uri = mNowFileInfo['uri']
        t_info = self.imgList[self.nowShowImgPos]
        t_imgName = t_info.filename
        key = getFileKey(t_uri + t_filename + t_imgName)
        for i in BOOKMARK_LIST:
            if i['key'] == key:
                saveCurrentImg = False
                continue
        if t_class is FILE_CLASS:
            with open(t_info.uri, 'rb') as fimg:
                with open("." + FILE_SIGN + "bookmark" + FILE_SIGN + key + '.' + t_imgName.split('.')[-1],'wb') as wfile:
                    wfile.write(fimg.read())
        elif t_class is CPS_CLASS:
            with open("." + FILE_SIGN + "bookmark" + FILE_SIGN + key + '.' + t_imgName.split('.')[-1],'wb') as wfile:
                wfile.write(self.nowFileInfo.File.read(t_info))
        BOOKMARK_LIST.append({'filename': t_filename,
                              'fileUri': t_uri,
                              "fileClass": t_class,
                              'sumImgNum': t_sum,
                              "CanRead": True,
                              "CurrentPos": self.nowShowImgPos,
                              'imgName': self.checkImgName(t_imgName),
                              'key': key})
        t_bm_json = json.dumps(BOOKMARK_LIST)
        with open('.' + FILE_SIGN + 'bookmark.json', 'w') as f:
            f.write(t_bm_json)
        saveCurrentImg = False

    def deleteBmark(self):
        if mFileListMode is not USE_BOOKMARK_LIST:
            deleteCurrentMark = False
            return
        t_imgName = BOOKMARK_LIST[self.nowFileInfo.FilePos]["imgName"]
        key = BOOKMARK_LIST[self.nowFileInfo.FilePos]["key"]
        for n, b in enumerate(BOOKMARK_LIST):
            if b['key'] == key:
                BOOKMARK_LIST.pop(n)
                try:
                    os.remove('./bookmark/' + key + '.' + t_imgName.split('.')[-1])
                except:
                    pass
                t_bm_json = json.dumps(BOOKMARK_LIST)
                with open('.' + FILE_SIGN + 'bookmark.json', 'w') as f:
                    f.write(t_bm_json)
                if manageChecked == 3:
                    root.mainFrame.manageFrame.manageList.delete(0, END)
                    for info in BOOKMARK_LIST:
                        root.mainFrame.manageFrame.manageList.insert(END, info['imgName'])
                if mFileListMode is USE_BOOKMARK_LIST:
                    OPEN_FILE_LIST = BOOKMARK_LIST
                    changeFile(CHANGE_FILE, 0)
                    refreshManageBar = True
                break
        deleteCurrentMark = False

class loadImgTh(multiprocessing.Process):
    def __init__(self, filePipe, posQueue, imgQueue):
        multiprocessing.Process.__init__(self)
        self.mLoadingFilePos = -1
        self.filePipe = filePipe
        self.fileClass = None
        self.cpsFile = None
        m = multiprocessing.Manager()
        self.live = m.Value('int', 1)
        self.posQueue = posQueue
        self.imgQueue = imgQueue

    def finish(self):
        self.live.value = 0

    def run(self):
        while self.live.value:
            if not self.filePipe.empty():
                print('change file')
                fileInfo = self.filePipe.get()
                if self.cpsFile:
                    self.cpsFile.close()
                if fileInfo[2] == FILE_CLASS:
                    t_cps_file = ''
                elif fileInfo[2] == 'zip':
                    t_cps_file = zipfile.ZipFile(fileInfo[0])
                    if fileInfo[1]:
                        t_cps_file.setpassword(fileInfo[1])
                elif fileInfo[2] == 'rar':
                    t_cps_file = rarfile.RarFile(fileInfo[0])
                    if fileInfo[1]:
                        t_cps_file.setpassword(fileInfo[1])
                self.fileUri = fileInfo[0]
                self.fileClass = fileInfo[2]
                self.cpsFile = t_cps_file
            elif self.cpsFile and not self.posQueue.empty():
                # print('loadImg ', )
                imgInfo = self.posQueue.get()
                if self.fileClass != FILE_CLASS:
                    try:
                        pil_image = self.cpsFile.read(imgInfo[0])
                    except Exception as ex:
                        print('loadImgTh ' + str(self.cpsFile) + '\n', ex)
                        pil_image = BAD_FILE
                else:
                    pil_image = imgInfo[0].uri
                self.imgQueue.put([imgInfo[1], self.fileClass, pil_image, imgInfo[2]])
                print('%d | Load img Over' % (imgInfo[1]), multiprocessing.current_process().name)
            else:
                time.sleep(0.05)
        print('loadImgTh is dead')

def loadImg(fileInfo):
    print('loadImg')
    print('%d | Load img Over' % (fileInfo['imgPos']))
    if fileInfo['fileClass'] == FILE_CLASS:
        t_class = FILE_CLASS
        try:
            pil_image = fileInfo["imgInfo"].uri
        except Exception as ex:
            print(ex)
            pil_image = BAD_FILE
    else:
        try:
            if fileInfo['CPS_FILE'][2] == 'zip':
                t_class = 'zip'
                t_cps_file = zipfile.ZipFile(fileInfo['CPS_FILE'][0])
                if fileInfo['CPS_FILE'][1]:
                    t_cps_file.setpassword(fileInfo['CPS_FILE'][1])
            else:
                t_class = 'rar'
                t_cps_file = rarfile.RarFile(fileInfo['CPS_FILE'][0])
                if fileInfo['CPS_FILE'][1]:
                    t_cps_file.setpassword(fileInfo['CPS_FILE'][1])
            pil_image = t_cps_file.read(fileInfo["imgInfo"])
            t_cps_file.close()
            # pil_image = PIL.Image.open(io.BytesIO(data))
        except Exception as ex:
            print(ex)
            pil_image = BAD_FILE
    return [fileInfo['imgPos'], t_class, pil_image]

def setMessage(imgName, imgNum, fileNum, fileName):
    # s_width = root.winfo_width()
    # print('s_width: ', s_width)
    # maxImgNameLen = (s_width * MESSAGE_BAR_IMG_NAME_WIDTH) / 10
    # if len(imgName.encode('utf-8')) > maxImgNameLen:
    #     imgName = imgName[:int(maxImgNameLen / 3)] + '...' + imgName[-int(maxImgNameLen / 3):]
    InfoMessage[IMG_NAME_MESSAGE].set(imgName)
    InfoMessage[IMG_NUM_MESSAGE].set(imgNum)
    InfoMessage[FILE_NUM_MESSAGE].set(fileNum)
    InfoMessage[FILE_NAME_MESSAGE].set(fileName)

def fileDialog(master, MODE):
    global nowFilePath
    openFileDialog(master, command=changeFileFromDialog, startPath=nowFilePath)

def rotateImg(MODE):
    global rotateModeVar
    changeImgLock.acquire()
    mNowImgInfo['rotate'] = MODE * 90
    mNowImgInfo['refresh'] = True
    changeImgLock.release()
    rotateModeVar.set(MODE)

def changeFileListFrom(index=0, useListClass=USE_FILE_LIST):
    global FILE_LIST
    global OPEN_FILE_LIST
    global mFileListMode
    if useListClass is USE_FILE_LIST and mFileListMode is not USE_FILE_LIST:
        mFileListMode = USE_FILE_LIST
        OPEN_FILE_LIST = FILE_LIST
        changeFile(CHANGE_FILE, index)
    elif useListClass is USE_FAVORITE_LIST and mFileListMode is not USE_FAVORITE_LIST:
        mFileListMode = USE_FAVORITE_LIST
        OPEN_FILE_LIST = FAVORITE_LIST
        changeFile(CHANGE_FILE, index)
    elif useListClass is USE_BOOKMARK_LIST and mFileListMode is not USE_BOOKMARK_LIST:
        mFileListMode = USE_BOOKMARK_LIST
        OPEN_FILE_LIST = BOOKMARK_LIST
        changeFile(CHANGE_FILE, index)

def changeFileFromDialog(path, imgPos=0, filename=''):
    global FILE_LIST
    global OPEN_FILE_LIST
    global mFileListMode
    global label
    global label2
    global ChangeFileFlag
    global nowFilePath
    global mConfigData
    global root
    label.configure(image="")
    label2.configure(image="")
    label['text'] = "Loading"
    mFileListMode = USE_FILE_LIST

    nowFilePath = path
    if filename:
        t_file_name = filename
    else:
        t_file_name = _NONE
        if os.path.isfile(nowFilePath):
            t_file_name = nowFilePath.split(FILE_SIGN)[-1]
            nowFilePath = nowFilePath.replace(t_file_name, "")

    t_file_list = getFileList(nowFilePath, subfile=mConfigData.scanSubFile, depth=mConfigData.scanSubFileDepth)
    sorted(t_file_list, key=lambda x: x['filename'])

    t_nowFilePos = 0
    for i,l in enumerate(t_file_list):
        if l["filename"] == t_file_name:
            t_nowFilePos = i
            break

    ChangeFileLock.acquire()
    FILE_LIST = t_file_list
    OPEN_FILE_LIST = t_file_list
    ChangeFileFlag["direct"] = CHANGE_FILE
    ChangeFileFlag["willFilePos"] = t_nowFilePos
    ChangeFileFlag["imgPos"] = imgPos
    ChangeFileLock.release()

    root.mainFrame.manageFrame.manageList.delete(0, END)
    for info in OPEN_FILE_LIST:
        root.mainFrame.manageFrame.manageList.insert(END, info['filename'])
    root.mainFrame.manageFrame.manageList.selection_clear(0, END)

    if not t_file_list:
        showwarning(title="对不起", message="该文件夹下没有可用文件")
        label['text'] = "No File"

def openLatelyFile(*args):
    global mConfigData
    info = mConfigData.latelyFileInfo[args[0]]
    changeFileFromDialog(path=info['uri'], filename=info['filename'])
    pass

def cleanLatelyFileData():
    global latelyMenu
    global mConfigData
    latelyMenu.delete(0, END)
    mConfigData.latelyFileInfo = []

def showInfoOfFile():
    global root
    global guardTask
    root.showInfoWin = Toplevel(root)
    root.showInfoWin.title('文件信息')
    root.showInfoWin.wm_attributes('-topmost', 0.5)
    root.showInfoWin.wm_resizable(width=False, height=False)
    s_x = root.winfo_x()
    s_y = root.winfo_y()
    t = root.winfo_geometry()
    win_w = int(t.split('x')[0])
    win_h = int(t.split('x')[1].split('+')[0])
    root.showInfoWin.geometry("390x250+%d+%d" % ((win_w - 500) / 2 + s_x, (win_h - 450) / 2 + s_y))

    t_info = guardTask.getNowFileInfo()
    t_filename = t_info['filename']
    t_uri = t_info['uri']
    path = os.path.join(t_uri, t_filename)
    a_time = os.path.getmtime(path)
    m_time = os.path.getmtime(path)
    c_time = os.path.getctime(path)

    if os.path.isfile(path):
        t_size = os.path.getsize(path)
        if t_filename.endswith('rar'):
            t_class = 'RAR文件'
        elif t_filename.endswith('zip'):
            t_class = 'ZIP文件'
    else:
        t_size = getDirSize(path)
        t_class = '文件夹'

    l = ['字节', 'KB', 'MB', 'GB']
    n = 0
    while n < 3 and t_size / 1024.0 > 1:
        t_size /= 1024.0
        n += 1
    t_size = ("%.1f"%(t_size)) + l[n]

    filenameTitleString = '文件名:'
    title1String = '类型:\n大小:\n图片数:'
    uriTitleString = '所在位置:'
    title2String = '访问日期:\n修改日期:\n创建日期:'

    info1String = t_class + '\n' + t_size + '\n' + str(t_info['imgNum'])
    info2String = time.strftime('%Y年%m月%d日%H时%M分%S秒', time.localtime(a_time))
    info2String += '\n' + time.strftime('%Y年%m月%d日%H时%M分%S秒', time.localtime(m_time))
    info2String += '\n' + time.strftime('%Y年%m月%d日%H时%M分%S秒', time.localtime(c_time))

    ft = Font(family='Fixdsys', size=10)
    root.showInfoWin.infoLabel = Label(root.showInfoWin, wraplength=270, text=filenameTitleString, font=ft, justify=LEFT)
    root.showInfoWin.infoLabel.grid(row=0, column=0, sticky=NW, padx=20, pady=10)
    root.showInfoWin.infoLabel = Label(root.showInfoWin, wraplength=270, text=t_filename, font=ft, justify=LEFT)
    root.showInfoWin.infoLabel.grid(row=0, column=1, sticky=NW, pady=10)

    root.showInfoWin.infoLabel = Label(root.showInfoWin, wraplength=270, text=title1String, font=ft, justify=LEFT)
    root.showInfoWin.infoLabel.grid(row=1, column=0, sticky=NW, padx=20)
    root.showInfoWin.infoLabel = Label(root.showInfoWin, wraplength=270, text=info1String, font=ft, justify=LEFT)
    root.showInfoWin.infoLabel.grid(row=1, column=1, sticky=NW)

    root.showInfoWin.infoLabel = Label(root.showInfoWin, wraplength=270, text=uriTitleString, font=ft, justify=LEFT)
    root.showInfoWin.infoLabel.grid(row=2, column=0, sticky=NW, padx=20)
    root.showInfoWin.infoLabel = Label(root.showInfoWin, wraplength=270, text=t_uri, font=ft, justify=LEFT)
    root.showInfoWin.infoLabel.grid(row=2, column=1, sticky=NW)

    root.showInfoWin.infoLabel = Label(root.showInfoWin, wraplength=270, text=title2String, font=ft, justify=LEFT)
    root.showInfoWin.infoLabel.grid(row=3, column=0, sticky=NW, padx=20)
    root.showInfoWin.infoLabel = Label(root.showInfoWin, wraplength=270, text=info2String, font=ft, justify=LEFT)
    root.showInfoWin.infoLabel.grid(row=3, column=1, sticky=NW)

    root.showInfoWin.mainloop()

def getDirSize(dir):
    size = 0
    for root, dirs, files in os.walk(dir):
        size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
    return size

def enableRandomJumpImg():
    global RANDOM_JUMP_IMG
    global mRandomSlide
    RANDOM_JUMP_IMG = not RANDOM_JUMP_IMG
    mRandomSlide.set(RANDOM_JUMP_IMG)

def setTwoPageMode():
    mConfigData.twoPageMode = not mConfigData.twoPageMode
    mNowImgInfo['refresh'] = True

def scaleFitMode(mode):
    mConfigData.scaleFitMode = mode
    mNowImgInfo['refresh'] = True

def setMangaMode():
    mConfigData.mangaMode = not mConfigData.mangaMode
    mNowImgInfo['refresh'] = True

def startSlide():
    global slideT
    global SLIDE_START
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

def stopSlide():
    global slideT
    global SLIDE_START
    if slideT.isAlive():
        slideLock.acquire()
        SLIDE_START = False
        slideLock.release()

def passwordConfig():
    global PWD_JSON
    passwordDialog(root, mConfigData.defaultPassword, PWD_JSON, command=setPasswordConfig)

def setPasswordConfig(defaultPassword, filePassword):
    global mConfigData
    if filePassword:
        global PWD_JSON
        PWD_JSON = filePassword
        if mConfigData.saveFilePassword:
            t_pwd_json = json.dumps(PWD_JSON)
            with open('.' + FILE_SIGN + 'Pwd.json', 'w') as f:
                f.write(t_pwd_json)

    if defaultPassword:
        if defaultPassword == [0]:
            mConfigData.defaultPassword = []
        else:
            mConfigData.defaultPassword = defaultPassword

def addFavorite():
    global FAVORITE_LIST
    t_filename = mNowFileInfo['filename']
    t_uri = mNowFileInfo['uri']
    t_sum = mNowFileInfo['sumImgNum']
    t_class = mNowFileInfo['fileClass']
    if t_filename:
        for i in FAVORITE_LIST:
            if i['filename'] == t_filename and i['fileUri'] == t_uri:
                return
        FAVORITE_LIST.append({'filename': t_filename, 'fileUri': t_uri, "fileClass": t_class, 'sumImgNum': t_sum, "CanRead": True, "CurrentPos": 0})
        t_favorite_json = json.dumps(FAVORITE_LIST)
        with open('.' + FILE_SIGN + 'favorite.json', 'w') as f:
            f.write(t_favorite_json)

def deleteFavorite():
    global FAVORITE_LIST
    t_filename = mNowFileInfo['filename']
    t_uri = mNowFileInfo['uri']
    if t_filename:
        for n, i in enumerate(FAVORITE_LIST):
            if i['filename'] == t_filename and i['fileUri'] == t_uri:
                FAVORITE_LIST.pop(n)
                t_favorite_json = json.dumps(FAVORITE_LIST)
                with open('.' + FILE_SIGN + 'favorite.json', 'w') as f:
                    f.write(t_favorite_json)
                if manageChecked == 2:
                    root.mainFrame.manageFrame.manageList.delete(0, END)
                    for info in BOOKMARK_LIST:
                        root.mainFrame.manageFrame.manageList.insert(END, info['filename'])
                if mFileListMode is USE_FAVORITE_LIST:
                    OPEN_FILE_LIST = FAVORITE_LIST
                    changeFile(CHANGE_FILE, 0)
                    refreshManageBar = True
                return

def addBookmark():
    global saveCurrentImg
    saveCurrentImg = True

def deleteBookmark():
    global deleteCurrentMark
    deleteCurrentMark = True

def initMenu(master):
    global mTwoViewMode
    global mConfigData
    master.menu = Menu(master)

    master.menu.filemenu = Menu(master)
    master.menu.add_cascade(label='文件', menu=master.menu.filemenu)
    master.menu.filemenu.add_command(label="打开...", command=lambda: fileDialog(master, OPEN_FILE))
    # master.menu.filemenu.add_command(label="管理收藏库...", command=testMyAskString)
    master.menu.filemenu.add_separator()
    master.menu.filemenu.add_command(label="文件属性...", command=showInfoOfFile)
    master.menu.filemenu.add_command(label="密码管理...", command=passwordConfig)
    master.menu.filemenu.add_command(label="首选项...", command=config)
    master.menu.filemenu.add_separator()
    master.menu.filemenu.s_submenu = Menu(master)
    master.menu.filemenu.add_cascade(label='打开最近', menu=master.menu.filemenu.s_submenu)
    master.menu.filemenu.add_command(label="清空最近", command=cleanLatelyFileData)
    global latelyMenu
    latelyMenu = master.menu.filemenu.s_submenu
    master.menu.filemenu.add_separator()
    master.menu.filemenu.add_command(label="退出", command=fileDialog)

    master.menu.viewmenu = Menu(master)
    master.menu.add_cascade(label='查看', menu=master.menu.viewmenu)
    global mTwoViewMode
    mTwoViewMode = IntVar()
    mTwoViewMode.set(mConfigData.twoPageMode)
    master.menu.viewmenu.add_checkbutton(variable=mTwoViewMode, label="双页模式",command=setTwoPageMode)
    global mMangaMode
    mMangaMode = IntVar()
    mMangaMode.set(mConfigData.mangaMode)
    master.menu.viewmenu.add_checkbutton(variable=mMangaMode, label="漫画模式",command=setMangaMode)
    master.menu.viewmenu.add_separator()
    global mViewMode
    mViewMode = IntVar()
    mViewMode.set(mConfigData.scaleFitMode)
    master.menu.viewmenu.add_radiobutton(variable=mViewMode, value=0, label="最佳适应模式", command=lambda: scaleFitMode(0))
    master.menu.viewmenu.add_radiobutton(variable=mViewMode, value=1, label="适应宽度模式", command=lambda: scaleFitMode(1))
    master.menu.viewmenu.add_radiobutton(variable=mViewMode, value=2, label="适应高度模式", command=lambda: scaleFitMode(2))
    master.menu.viewmenu.add_separator()
    global rotateModeVar
    rotateModeVar = IntVar()
    rotateModeVar.set(0)
    master.menu.viewmenu.add_radiobutton(variable=rotateModeVar, value=0, label="正常角度", command=lambda: rotateImg(0))
    master.menu.viewmenu.add_radiobutton(variable=rotateModeVar, value=3, label="顺时针旋转 90度", command=lambda: rotateImg(3))
    master.menu.viewmenu.add_radiobutton(variable=rotateModeVar, value=1, label="逆时针旋转 90度", command=lambda: rotateImg(1))
    master.menu.viewmenu.add_radiobutton(variable=rotateModeVar, value=2, label="旋转 180度", command=lambda: rotateImg(2))

    master.menu.jumpmenu = Menu(master)
    master.menu.add_cascade(label='跳转', menu=master.menu.jumpmenu)
    master.menu.jumpmenu.add_command(label="文件跳转...", command=fileJump)
    master.menu.jumpmenu.add_command(label="文件随机跳转", command=fileRandomJump)
    master.menu.jumpmenu.add_separator()
    master.menu.jumpmenu.add_command(label="图片跳转...", command=imgJump)
    # master.menu.jumpmenu.add_command(label="图片随机跳转", command=fileDialog)
    master.menu.jumpmenu.add_separator()
    master.menu.jumpmenu.add_command(label="下一页", command=lambda: changePicSingle(NEXT_IMG))
    master.menu.jumpmenu.add_command(label="上一页", command=lambda: changePicSingle(BACK_IMG))
    master.menu.jumpmenu.add_command(label="下一文件包", command=lambda: changeFile(NEXT_FILE))
    master.menu.jumpmenu.add_command(label="上一文件包", command=lambda: changeFile(BACK_FILE))
    master.menu.jumpmenu.add_separator()
    global mSlide
    mSlide = IntVar()
    mSlide.set(0)
    master.menu.jumpmenu.add_checkbutton(variable=mSlide, label="放映幻灯片", command=startSlide)
    global mRandomSlide
    mRandomSlide = IntVar()
    mRandomSlide.set(RANDOM_JUMP_IMG)
    master.menu.jumpmenu.add_checkbutton(variable=mRandomSlide, label="随机模式", command=enableRandomJumpImg)

    master['menu'] = master.menu

def initMouseRightMenu(master):
    global rightMenu
    rightMenu = Menu(master)

    rightMenu.add_command(label="收藏", command=addFavorite)
    rightMenu.add_command(label="加入书签", command=addBookmark)
    rightMenu.add_command(label="下一页", command=lambda: changePicSingle(NEXT_IMG))
    rightMenu.add_command(label="上一页", command=lambda: changePicSingle(BACK_IMG))
    rightMenu.add_separator()
    global mTwoViewMode
    rightMenu.add_checkbutton(variable=mTwoViewMode, label="双页模式", command=setTwoPageMode)
    global mMangaMode
    rightMenu.add_checkbutton(variable=mMangaMode, label="漫画模式",command=setMangaMode)
    global mRandomSlide
    rightMenu.add_checkbutton(variable=mRandomSlide, label="随机模式", command=enableRandomJumpImg)
    rightMenu.add_separator()
    rightMenu.add_command(label="文件随机跳转", command=fileRandomJump)
    rightMenu.add_command(label="图片跳转...", command=imgJump)
    rightMenu.add_command(label="文件属性...", command=showInfoOfFile)

def initMessage(master):
    global InfoMessage

    master.messageLabel = Label(master, bg='white')
    master.messageLabel.place(relx=0, rely=1, height=MESSAGE_BAR_HEIGHT, relwidth=1, anchor=SW)
    ImgNameVar = StringVar()
    master.messageLabel.infoImgNameMessage = tkinter.Message(master.messageLabel, aspect=4000, textvariable=ImgNameVar, justify=LEFT)
    master.messageLabel.infoImgNameMessage.place(in_=master.messageLabel,
                                                 relx=0, rely=0,
                                                 relheight=1,
                                                 relwidth=MESSAGE_BAR_IMG_NAME_WIDTH - 0.001,
                                                 anchor=NW)
    # master.messageLabel.infoImgNameMessage.pack(side=LEFT)
    ImgNumVar = StringVar()
    master.messageLabel.infoImgNumMessage = tkinter.Message(master.messageLabel, aspect=500, textvariable=ImgNumVar, justify=RIGHT)
    master.messageLabel.infoImgNumMessage.place(in_=master.messageLabel,
                                                relx=0.4, rely=0,
                                                relheight=1,
                                                relwidth=MESSAGE_BAR_IMG_NUM_WIDTH - 0.001,
                                                anchor=NW)
    FileNumVar = StringVar()
    master.messageLabel.infoFileNumMessage = tkinter.Message(master.messageLabel, aspect=500, textvariable=FileNumVar, justify=RIGHT)
    master.messageLabel.infoFileNumMessage.place(in_=master.messageLabel,
                                                 relx=0.5, rely=0,
                                                 relheight=1,
                                                 relwidth=MESSAGE_BAR_FILE_NUM_WIDTH - 0.001,
                                                 anchor=NW)
    FileNameVar = StringVar()
    master.messageLabel.infoFileNameMessage = tkinter.Message(master.messageLabel, aspect=4000, textvariable=FileNameVar, justify=RIGHT)
    master.messageLabel.infoFileNameMessage.place(in_=master.messageLabel,
                                                  relx=0.6, rely=0,
                                                  relheight=1,
                                                  relwidth=MESSAGE_BAR_FILE_NAME_WIDTH - 0.001,
                                                  anchor=NW)
    ImgNameVar.set('OK')
    ImgNumVar.set('OK')
    FileNumVar.set('OK')
    FileNameVar.set('OK')
    InfoMessage = [ImgNameVar, ImgNumVar, FileNumVar, FileNameVar]

def config():
    global mConfigData
    configDialog(root, command=setConfig, oldConfig=mConfigData)

def setConfig(data):
    if data:
        global mConfigData
        mConfigData.background = data.background
        label['fg'] = getInverse(mConfigData.background)
        label2['fg'] = getInverse(mConfigData.background)
        mConfigData.customBackground = data.customBackground
        mConfigData.restore = data.restore
        mConfigData.saveLatelyFileInfo = data.saveLatelyFileInfo
        mConfigData.scanSubFile = data.scanSubFile
        mConfigData.scanSubFileDepth = data.scanSubFileDepth
        mConfigData.useCache = data.useCache
        mConfigData.slideTime = data.slideTime
        mConfigData.saveFilePassword = data.saveFilePassword
        mConfigData.useCustomSort = data.useCustomSort
        mConfigData.scaleMode = data.scaleMode
        saveConfigToFile(mConfigData)

        root.mainFrame['bg'] = mConfigData.background
        root.mainFrame.imgFrame['bg'] = mConfigData.background
        label['bg'] = mConfigData.background
        label2['bg'] = mConfigData.background

def getConfigFromFile():
    t_config = _configData()
    try:
        with open('.' + FILE_SIGN + 'conf.json', 'r') as f:
            confJson = f.read()
        CONF_JSON = json.JSONDecoder().decode(confJson)
        t_config.setDataFromDict(CONF_JSON)
    except:
        t_conf_json = json.dumps(t_config.getDataDict())
        with open('.' + FILE_SIGN + 'conf.json', 'w') as f:
            f.write(t_conf_json)
    return t_config

def saveConfigToFile(config_data):
    t_conf_json = json.dumps(config_data.getDataDict())
    with open('.' + FILE_SIGN + 'conf.json', 'w') as f:
        f.write(t_conf_json)

def slide():
    # print ("slide")
    global slideLock
    global mConfigData
    while(True):
        slideLock.acquire()
        checkTmp = SLIDE_START
        slideLock.release()
        if checkTmp:
            ShowPic(NEXT_IMG)
            time.sleep(mConfigData.slideTime)
        else:
            break

def ShowPic(value, jump_num=0):
    global changeImgLock
    global mNowImgInfo
    global mConfigData
    global RANDOM_LIST
    global RANDOM_LIST_INDEX
    global RANDOM_LIST_LENGTH
    global rotateModeVar

    changeImgLock.acquire()
    if value is JUMP_IMG:
        mNowImgInfo['imgPos'] = jump_num
    else:
        if value is BACK_IMG:
            if mConfigData.twoPageMode:
                step = -2
            else:
                step = -1
        elif value is NEXT_IMG:
            step = mNowImgInfo['used']

        if RANDOM_JUMP_IMG:
            RANDOM_LIST_INDEX += step
            RANDOM_LIST_INDEX %= RANDOM_LIST_LENGTH
            mNowImgInfo['imgPos'] = RANDOM_LIST[RANDOM_LIST_INDEX]
        else:
            mNowImgInfo['imgPos'] += step
    mNowImgInfo['direct'] = value
    mNowImgInfo['refresh'] = True
    changeImgLock.release()
    rotateModeVar.set(0)

def changePicSingle(value):
    global changeImgLock
    global mNowImgInfo
    global rotateModeVar
    changeImgLock.acquire()
    mNowImgInfo['step'] = 1
    if value is BACK_IMG:
        mNowImgInfo['imgPos'] -= 1
    elif value is NEXT_IMG:
        mNowImgInfo['imgPos'] += 1
    mNowImgInfo['direct'] = value
    mNowImgInfo['refresh'] = True
    changeImgLock.release()
    rotateModeVar.set(0)

def changeFile(direct, jump_file=0):
    global label
    global label2
    global ChangeFileFlag
    stopSlide()
    label.configure(image="")
    label2.configure(image="")
    label['text'] = "Loading"

    ChangeFileLock.acquire()
    ChangeFileFlag["direct"] = direct
    ChangeFileFlag['imgPos'] = 0
    if direct is JUMP_FILE or direct is CHANGE_FILE:
        ChangeFileFlag["willFilePos"] = jump_file
    ChangeFileLock.release()

def manageButtonEvent(index):
    global manageButtonList
    global manageChecked
    global isShowManageList
    global root
    for i, b in enumerate(manageButtonList):
        if i == index and manageChecked != index:
            b['bg'] = '#F1F1F1'
        else:
            b['bg'] = '#D3D3D3'
    if manageChecked == index:
        isShowManageList = False
        manageChecked = -1
        showManageList(False)
        mNowImgInfo['refresh'] = True
        return
    if not isShowManageList:
        isShowManageList = True
        showManageList(True)
        mNowImgInfo['refresh'] = True
    manageChecked = index
    if index == 0:
        global FILE_LIST
        root.mainFrame.manageFrame.manageList.delete(0, END)
        for info in FILE_LIST:
            root.mainFrame.manageFrame.manageList.insert(END, info['filename'])
        root.mainFrame.manageFrame.manageList.selection_clear(0, END)
        global refreshManageBar
    elif index == 1:
        # global refreshManageBar
        pass
    elif index == 2:
        global FAVORITE_LIST
        root.mainFrame.manageFrame.manageList.delete(0, END)
        for info in FAVORITE_LIST:
            root.mainFrame.manageFrame.manageList.insert(END, info['filename'])
    elif index == 3:
        global BOOKMARK_LIST
        root.mainFrame.manageFrame.manageList.delete(0, END)
        for info in BOOKMARK_LIST:
            root.mainFrame.manageFrame.manageList.insert(END, info['imgName'])
    refreshManageBar = True

def showManageList(show):
    global root
    if show:
        # root.mainFrame.manageFrame.manageList.place(x=MANAGE_BAR_BUTTON_WIDTH, y=0, width=MANAGE_BAR_LIST_WIDTH - 10, relheight=1, anchor=NW)
        # root.mainFrame.manageFrame.listScrollBar.place(x=MANAGE_BAR_BUTTON_WIDTH, y=0, width=10, relheight=1, anchor=NW)
        root.mainFrame.manageFrame.place(width=MANAGE_BAR_BUTTON_WIDTH + MANAGE_BAR_LIST_WIDTH)
    else:
        root.mainFrame.manageFrame.place(width=MANAGE_BAR_BUTTON_WIDTH)
        # root.mainFrame.manageFrame.manageList.pack_forget()
        # root.mainFrame.manageFrame.listScrollBar.pack_forget()

def checkPosInManage(event):
    global isShowManageList
    if isShowManageList:
        managePos = MANAGE_BAR_BUTTON_WIDTH + MANAGE_BAR_LIST_WIDTH
    else:
        managePos = MANAGE_BAR_BUTTON_WIDTH
    t = root.winfo_geometry()
    win_w = int(t.split('+')[-2])
    ev_x = event.x_root - win_w
    if ev_x < managePos:
        return True
    return False

def mouseRightEvent(event):
    global rightMenu
    if checkPosInManage(event):
        return
    # global RIGHT_MENU_VISIBLE
    rightMenu.delete(2)
    rightMenu.insert_command(2, label="加入书签", command=addBookmark)
    if mFileListMode is USE_FILE_LIST:
        rightMenu.delete(1)
        rightMenu.insert_command(0, label="收藏", command=addFavorite)
    elif mFileListMode is USE_FAVORITE_LIST:
        rightMenu.delete(1)
        rightMenu.insert_command(0, label="取消收藏", command=deleteFavorite)
    elif mFileListMode is USE_BOOKMARK_LIST:
        rightMenu.delete(2)
        rightMenu.insert_command(2, label="删除书签", command=deleteBookmark)
    rightMenu.unpost()
    rightMenu.post(event.x_root, event.y_root)
    # RIGHT_MENU_VISIBLE = True

def mouseEvent(event):
    global nTime
    nTime = time.time()
    global slideT
    global SLIDE_START
    global rightMenu
    # global RIGHT_MENU_VISIBLE
    rightMenu.unpost()

    if checkPosInManage(event):
        return
    # if RIGHT_MENU_VISIBLE:
    #     rightMenu.unpost()
    #     RIGHT_MENU_VISIBLE = False
    #     return

    s_width = root.winfo_width()
    s_height = root.winfo_height()
    t=root.winfo_geometry()
    win_w = int(t.split('+')[-2])
    win_h = int(t.split('+')[-1])
    ev_x = event.x_root - win_w
    ev_y = event.y_root - win_h

    if ev_x > s_width / 3.0 * 2.0:
        ShowPic(NEXT_IMG)
    elif ev_x < s_width / 3.0:
        ShowPic(BACK_IMG)
    elif ev_y > s_height / 3.0 * 2.0:
        changeFile(NEXT_FILE)
    elif ev_y < s_height / 3.0:
        changeFile(BACK_FILE)
    else:
        startSlide()

def mouseWheelEvent(event):
    global mNowImgInfo
    global mConfigData
    global root
    if checkPosInManage(event):
        return

    if not (mConfigData.twoPageMode or mConfigData.scaleFitMode is SCALE_FIT_MODE_BOTH):
        img_w, img_h = mNowImgInfo['boxSize']
        box_w = root.winfo_width()
        box_h = root.winfo_height() - MESSAGE_BAR_HEIGHT
        t_scroll_x = mNowImgInfo['scrollX']
        t_scroll_y = mNowImgInfo['scrollY']
        if mConfigData.scaleFitMode is SCALE_FIT_MODE_WIDTH:
            max_scroll = (img_h - box_h) / 2
            if max_scroll < 0:
                return
            if event.num == 4:
                t_scroll_y = min([t_scroll_y + 20, max_scroll])
            elif event.num == 5:
                t_scroll_y = max(t_scroll_y - 20, -max_scroll)
        elif mConfigData.scaleFitMode is SCALE_FIT_MODE_HEIGHT:
            max_scroll = (img_w - box_w) / 2
            if max_scroll < 0:
                return
            if event.num == 4:
                t_scroll_x = min(t_scroll_x + 20, max_scroll)
            elif event.num == 5:
                t_scroll_x = max(t_scroll_x - 20, -max_scroll)
        setImgPlace(t_scroll_x, t_scroll_y)
        mNowImgInfo['scrollX'] = t_scroll_x
        mNowImgInfo['scrollY'] = t_scroll_y

def setImgPlace(mX, mY):
    global root
    global isShowManageList
    if isShowManageList:
        root.mainFrame.imgFrame.place(x=mX + (MANAGE_BAR_BUTTON_WIDTH + MANAGE_BAR_LIST_WIDTH) / 2, y=mY - MESSAGE_BAR_HEIGHT / 2)
    else:
        root.mainFrame.imgFrame.place(x=mX + MANAGE_BAR_BUTTON_WIDTH / 2, y=mY - MESSAGE_BAR_HEIGHT / 2)

def fileJump():
    jump_num = askstring(title='文件跳转', prompt="请输入跳转到的文件序号: ")
    try:
        jump_num = int(jump_num)
        jump_num = max([1, jump_num])
        jump_num = min([len(OPEN_FILE_LIST), jump_num])
        changeFile(JUMP_FILE, jump_file=jump_num - 1)
    except:
        showerror(title="错误", message="输入错误！")

def imgJump():
    jump_num = askstring(title='图片跳转', prompt="请输入跳转到的图片序号: ")
    try:
        jump_num = int(jump_num)
        jump_num = max([1, jump_num])
        ShowPic(JUMP_IMG, jump_num=jump_num - 1)
    except:
        print("输入错误")

def fileRandomJump():
    if askquestion(title="随机跳转", message="是否随机跳转到一个压缩包?") == YES:
        jump_num = random.randint(0, len(OPEN_FILE_LIST))
        changeFile(JUMP_FILE, jump_file=jump_num)

def onKeyPress(ev):
    global nTime
    nTime = time.time()
    global slideT
    global SLIDE_START
    # print(ev.keycode)
    if ev.keycode == KEY_CODE.codeS:
        startSlide()
        return
    stopSlide()

    if ev.keycode == KEY_CODE.codeLeft:
        ShowPic(BACK_IMG)
    elif ev.keycode == KEY_CODE.codeRight:
        ShowPic(NEXT_IMG)
    elif ev.keycode == KEY_CODE.codeD or ev.keycode == KEY_CODE.codeDown:
        changeFile(NEXT_FILE)
    elif ev.keycode == KEY_CODE.codeA or ev.keycode == KEY_CODE.codeUp:
        changeFile(BACK_FILE)
    elif ev.keycode == KEY_CODE.codeW:
        fileJump()
    elif ev.keycode == KEY_CODE.codeE:
        imgJump()
    elif ev.keycode == KEY_CODE.codeC:
        fileRandomJump()
    elif ev.keycode == KEY_CODE.codeM:
        dpw = ''
        if mConfigData.defaultPassword:
            dpw = mConfigData.defaultPassword[0]
            for pw in mConfigData.defaultPassword[1:]:
                dpw = dpw + ";" + pw
        add_password = askstring(title='默认密码', prompt="请输入欲添加的可待测试默认密码: \n  1.以\";\"分隔多个\n  2.多余的空格也会被视为密码", initialvalue=dpw)
        try:
            add_password = add_password.split(";")
        except:
            return
        for ap in add_password:
            try:
                mConfigData.defaultPassword.index(ap)
            except:
                mConfigData.defaultPassword.append(ap)
        saveConfigToFile(mConfigData)

def getFileList(file_uri, subfile=False, depth=0):
    if subfile:
        if SUB_FILE_DEPTH > 0 and depth > SUB_FILE_DEPTH:
            return []
    elif depth > 1:
        return []
    depth += 1
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
        elif os.path.isdir(file_uri + sub_file_name):
            t_file_list += getFileList(file_uri + sub_file_name, subfile=subfile, depth=depth)
    if has_pic:
        t_file_list.append({"filename": file_uri.split(FILE_SIGN)[-2], "fileUri": os.path.dirname(file_uri[:-1]) + '/', "fileClass": FILE_CLASS, "CanRead": TRUE, "CurrentPos": 0})
    return t_file_list

def closeWin():
    global mImgLoadQueueLock
    global changeImgLock
    global ChangeFileLock
    global mConfigData
    global guardTask
    global loadTask

    if mConfigData.restore:
        mImgLoadQueueLock.acquire()
        ChangeFileLock.acquire()
        mConfigData.restoreData['filename'] = mNowFileInfo['filename']
        mConfigData.restoreData['uri'] = mNowFileInfo['uri']
        mConfigData.restoreData['imgPos'] = mNowImgInfo['imgPos']
        mImgLoadQueueLock.release()
        ChangeFileLock.release()

    saveConfigToFile(mConfigData)

    guardTask.finish()
    while guardTask.isAlive():
        guardTask.finish()
        time.sleep(0.1)
    root.destroy()

def screenSizeChange(event):
    global root
    global SCREEN_WIDTH
    global SCREEN_HEIGHT
    global SCREEN_SIZE_CHANGE
    win_w = root.winfo_width()
    win_h = root.winfo_height()
    if win_h != 1:
        if SCREEN_WIDTH != win_w:
            SCREEN_SIZE_CHANGE = True
            SCREEN_WIDTH = win_w
        if SCREEN_HEIGHT != win_h:
            SCREEN_SIZE_CHANGE = True
            SCREEN_HEIGHT = win_h

def selectManageList(event):
    global mFileListMode
    if manageChecked == 0:
        if mFileListMode == USE_FILE_LIST:
            changeFile(JUMP_FILE, root.mainFrame.manageFrame.manageList.curselection()[0])
        else:
            changeFileListFrom(root.mainFrame.manageFrame.manageList.curselection()[0], USE_FILE_LIST)
    elif manageChecked == 1:
        ShowPic(JUMP_IMG, root.mainFrame.manageFrame.manageList.curselection()[0])
    elif manageChecked == 2:
        if mFileListMode == USE_FAVORITE_LIST:
            changeFile(JUMP_FILE, root.mainFrame.manageFrame.manageList.curselection()[0])
        else:
            changeFileListFrom(root.mainFrame.manageFrame.manageList.curselection()[0], USE_FAVORITE_LIST)
    elif manageChecked == 3:
        if mFileListMode == USE_BOOKMARK_LIST:
            changeFile(JUMP_FILE, root.mainFrame.manageFrame.manageList.curselection()[0])
        else:
            changeFileListFrom(root.mainFrame.manageFrame.manageList.curselection()[0], USE_BOOKMARK_LIST)

def getInverse(color):
    R_color_str = color[1:3]
    G_color_str = color[3:5]
    B_color_str = color[5:7]
    R_color_int = 255 - int(R_color_str, 16)
    G_color_int = 255 - int(G_color_str, 16)
    B_color_int = 255 - int(B_color_str, 16)
    R_color_inverse_str = hex(R_color_int)[-2:]
    G_color_inverse_str = hex(G_color_int)[-2:]
    B_color_inverse_str = hex(B_color_int)[-2:]
    return '#' + R_color_inverse_str + G_color_inverse_str + B_color_inverse_str

'''入口'''
if __name__ == '__main__':
    if PLATFORM == 'Linux':
        FILE_SIGN = "/"
        KEY_CODE = _KeyCode('Linux')
    elif PLATFORM == 'Windows':
        FILE_SIGN = "\\"
        KEY_CODE = _KeyCode('Windows')

    mConfigData = getConfigFromFile()
    mFileListMode = USE_FILE_LIST
    deleteCurrentMark = False
    saveCurrentImg = False

    root = tk.Tk()
    # root.iconbitmap('./tk.ico')
    root.geometry("800x600+%d+%d" % ((800 - root.winfo_width()) / 2, (600 - root.winfo_height()) / 2))
    root.protocol('WM_DELETE_WINDOW', closeWin)
    # TODO
    # root.wm_attributes('-zoomed',1)
    root.wm_attributes('-topmost', 0)
    root.bind("<Button-1>", mouseEvent)
    root.bind("<Button-3>", mouseRightEvent)
    root.bind("<Button-4>", mouseWheelEvent)
    root.bind("<Button-5>", mouseWheelEvent)
    # root.bind('<Configure>', screenSizeChange)
    root.bind("<Key>", onKeyPress)
    root.title('图包浏览器')
    initMenu(root)
    root.mainFrame = Frame(root, bg=mConfigData.background)
    root.mainFrame.pack(fill=BOTH, expand=1)
    # label = tk.Label(root, image=_NONE, width=600, height=550, font='Helvetica -18 bold', bg='red')
    root.mainFrame.manageFrame = Frame(root)
    root.mainFrame.manageFrame.fileButton = Button(root.mainFrame.manageFrame,
                                                   text='文\n件\n夹',
                                                   relief=FLAT,
                                                   width=1,
                                                   bg='#D3D3D3',
                                                   command=lambda: manageButtonEvent(0))
    root.mainFrame.manageFrame.fileButton.place(x=0, y=0, width=20, height=70)
    root.mainFrame.manageFrame.picButton = Button(root.mainFrame.manageFrame,
                                                  text='图\n片',
                                                  relief=FLAT,
                                                  width=1,
                                                  bg='#D3D3D3',
                                                  command=lambda: manageButtonEvent(1))
    root.mainFrame.manageFrame.picButton.place(x=0, y=70, width=20, height=70)
    root.mainFrame.manageFrame.favoriteButton = Button(root.mainFrame.manageFrame,
                                                       text='收\n藏\n夹',
                                                       relief=FLAT,
                                                       width=1,
                                                       bg='#D3D3D3',
                                                       command=lambda: manageButtonEvent(2))
    root.mainFrame.manageFrame.favoriteButton.place(x=0, y=140, width=20, height=70)
    root.mainFrame.manageFrame.bookmarkButton = Button(root.mainFrame.manageFrame,
                                                       text='书\n签',
                                                       relief=FLAT,
                                                       width=1,
                                                       bg='#D3D3D3',
                                                       command=lambda: manageButtonEvent(3))
    root.mainFrame.manageFrame.bookmarkButton.place(x=0, y=210, width=20, height=70)
    root.mainFrame.manageFrame.place(x=0, y=0, width=MANAGE_BAR_BUTTON_WIDTH + MANAGE_BAR_LIST_WIDTH, relheight=1, height=-MESSAGE_BAR_HEIGHT, anchor=NW)
    manageChecked = -1
    isShowManageList = False
    manageButtonList = [root.mainFrame.manageFrame.fileButton,
                        root.mainFrame.manageFrame.picButton,
                        root.mainFrame.manageFrame.favoriteButton,
                        root.mainFrame.manageFrame.bookmarkButton]

    refreshManageBar = False
    manageListVar = StringVar()
    root.mainFrame.manageFrame.manageList = Listbox(root.mainFrame.manageFrame, selectmode=SINGLE, listvariable=manageListVar, selectbackground='#FF7F50')
    root.mainFrame.manageFrame.listScrollBar = Scrollbar(root.mainFrame.manageFrame)
    root.mainFrame.manageFrame.listScrollHorizontalBar = Scrollbar(root.mainFrame.manageFrame, orient=HORIZONTAL)
    root.mainFrame.manageFrame.manageList.bind('<ButtonRelease-1>', selectManageList)
    showManageList(False)
    root.mainFrame.manageFrame.manageList.place(x=MANAGE_BAR_BUTTON_WIDTH, y=0, width=MANAGE_BAR_LIST_WIDTH - 10, relheight=1, height=-10, anchor=NW)
    root.mainFrame.manageFrame.listScrollBar.place(x=MANAGE_BAR_BUTTON_WIDTH + MANAGE_BAR_LIST_WIDTH - 10, y=0, width=10, relheight=1, height=-10, anchor=NW)
    root.mainFrame.manageFrame.listScrollHorizontalBar.place(x=MANAGE_BAR_BUTTON_WIDTH, rely=1, width=MANAGE_BAR_LIST_WIDTH, height=10, anchor=SW)
    root.mainFrame.manageFrame.manageList['yscrollcommand'] = root.mainFrame.manageFrame.listScrollBar.set
    root.mainFrame.manageFrame.listScrollBar['command'] = root.mainFrame.manageFrame.manageList.yview
    root.mainFrame.manageFrame.manageList['xscrollcommand'] = root.mainFrame.manageFrame.listScrollHorizontalBar.set
    root.mainFrame.manageFrame.listScrollHorizontalBar['command'] = root.mainFrame.manageFrame.manageList.xview

    root.mainFrame.imgFrame = Frame(root.mainFrame, bg=mConfigData.background)
    root.mainFrame.imgFrame.place(relx=0.5, rely=0.5, y=-MESSAGE_BAR_HEIGHT / 2, x=MANAGE_BAR_BUTTON_WIDTH / 2, anchor=CENTER)
    label = tk.Label(root.mainFrame.imgFrame, image=_NONE, font='Helvetica -18 bold', fg=getInverse(mConfigData.background), bg=mConfigData.background)
    label.grid()
    label2 = tk.Label(root.mainFrame.imgFrame, image=_NONE, font='Helvetica -18 bold', fg=getInverse(mConfigData.background), bg=mConfigData.background)
    label2.grid(row=0, column=1)
    # label2.grid_forget()
    # label.pack(padx=15, pady=15, expand=1, fill=BOTH)
    initMessage(root.mainFrame)
    initMouseRightMenu(root)

    SUB_FILE_DEPTH = mConfigData.scanSubFileDepth
    nowFilePath = os.getcwd() + '/'
    mNowImgInfo = {'imgPos': 0,
                   'used': 1,
                   'direct': NEXT_IMG,
                   'rotate': 0,
                   'step': 1,
                   'refresh': False,
                   'scrollX': 0,
                   'scrollY': 0,
                   'imgSize': [0, 0],
                   'boxSize': [0, 0]}
    FILE_LIST = []
    OPEN_FILE_LIST = []
    ChangeFileFlag = {"nowFilePos": 0, "direct": NOCHANGE_FILE, 'imgPos': 0}
    mNowFileInfo = {'filename': '', 'uri': '', 'imgPos': 0, 'fileClass': None, 'sumImgNum': 0}
    willLoadImgQueue = _NONE

    guardTask = guardTh()
    guardTask.twoPageMode = mConfigData.twoPageMode
    slideT = threading.Timer(0, slide)
    slideLock = threading.Lock()
    mImgLoadQueueLock = threading.Lock()
    changeImgLock = threading.Lock()
    ChangeFileLock = threading.Lock()
    SLIDE_START = False

    if not len(sys.argv) < 2:
        nowFilePath = _NONE
        for uri in sys.argv[1:]:
            nowFilePath += (uri + " ")
        nowFilePath = nowFilePath[:-1]
        t_file_uri = nowFilePath

        t_file_name = _NONE
        if os.path.isfile(nowFilePath):
            t_file_name = nowFilePath.split(FILE_SIGN)[-1]
            nowFilePath = nowFilePath.replace(t_file_name, "")

        FILE_LIST = getFileList(nowFilePath, subfile=mConfigData.scanSubFile)
        sorted(FILE_LIST, key=lambda x: x['filename'])
        OPEN_FILE_LIST = FILE_LIST
        ChangeFileFlag = {"nowFilePos": 0, "direct": CURRENT_FILE, 'imgPos': 0}

        try:
            guardTask.nowFilePos = OPEN_FILE_LIST.index({"filename": t_file_name, "fileUri": t_file_uri, "fileClass":CPS_CLASS, "CanRead": True, "CurrentPos": 0})
        except:
            guardTask.nowFilePos = 0
    elif mConfigData.restore and mConfigData.restoreData['filename']:
        t_path = mConfigData.restoreData['uri']
        t_imgPos = mConfigData.restoreData['imgPos']
        changeFileFromDialog(t_path, filename=mConfigData.restoreData['filename'], imgPos=t_imgPos)

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

    try:
        with open('.' + FILE_SIGN + 'favorite.json', 'r') as f:
            favoriteJson = f.read()
    except:
        with open('.' + FILE_SIGN + 'favorite.json', 'w') as f:
            f.write('')
        favoriteJson = ''
    try:
        FAVORITE_LIST = json.JSONDecoder().decode(favoriteJson)
    except:
        FAVORITE_LIST = []

    try:
        with open('.' + FILE_SIGN + 'bookmark.json', 'r') as f:
            bookmarkJson = f.read()
    except:
        with open('.' + FILE_SIGN + 'bookmark.json', 'w') as f:
            f.write('')
        bookmarkJson = ''
    try:
        BOOKMARK_LIST = json.JSONDecoder().decode(bookmarkJson)
    except:
        BOOKMARK_LIST = []
    if not os.path.exists("./bookmark/"):
        os.mkdir("./bookmark/")

    # 对旧版本保存的密码文件兼容
    if PWD_JSON:
        changed = False
        for key in PWD_JSON:
            if isinstance(PWD_JSON[key], str):
                PWD_JSON[key] = {"password": PWD_JSON[key], "badfile": False, "filename": '', "uri": ''}
                changed = True
        if changed:
            t_pwd_json = json.dumps(PWD_JSON)
            with open('.' + FILE_SIGN + 'Pwd.json', 'w') as f:
                f.write(t_pwd_json)
    try:
        PWD_JSON.pop('defaultPassword')
    except:
        pass
    for k,info in PWD_JSON.items():
        try:
            info['filename']
        except:
            PWD_JSON.update({k: {'password': info['password'], 'badfile': info['badfile'], 'filename': '', 'uri': ''}})

    guardTask.setDaemon(True)
    guardTask.start()

    root.mainloop()
