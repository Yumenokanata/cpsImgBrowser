from tkinter import *
from tkinter.font import *
from tkinter import ttk
import os
import getpass
import time

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

    def __init__(self, master=None, rowWidth=170, rowHeight=25, titleHeight=25, column=0, row=0, data=[], height=450):
        Canvas.__init__(self, master, height=height)
        self.column = column
        self.row = row
        self.tableData = data
        self.tableRect = []
        for i in range(len(data)):
            self.tableRect.append([])
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
        self.RectCache = []
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
        if self.height:
            h = self.height
        else:
            h = 600

        t_height = self.rowHeight
        for row in range(self.row):
            if row != self.select_row:
                if row % 2 == 1:
                    bg = self.WHITE_COLOR
                else:
                    bg = self.BLACK_COLOR
            else:
                bg = self.SELECT_COLOR

            t_x = 2
            t_y = self.scrollY + self.titleHeight + row * self.rowHeight
            t_width = 2 + self.x_list[-1] + self.columnWidthList[-1]
            if t_y + t_height > 0:
                if t_y > h + t_height:
                    for i in range(row, len(self.tableData)):
                        if self.tableRect[i]:
                            self.RectCache.append(self.tableRect[i])
                            self.tableRect[i] = []
                        else:
                            break
                    break
                if self.tableRect[row]:
                    self.coords(self.tableRect[row][0], (t_x,
                                                         t_y,
                                                         t_x + t_width,
                                                         t_y + t_height))
                    self.itemconfig(self.tableRect[row][0], fill=bg)
                    for i, col in enumerate(self.tableRect[row][1]):
                        self.coords(col, (10 + self.x_list[i],
                                          3 + t_y))
                elif self.RectCache:
                    t_table = self.RectCache.pop()
                    self.coords(t_table[0], (t_x,
                                             t_y,
                                             t_x + t_width,
                                             t_y + t_height))
                    self.itemconfig(t_table[0], fill=bg)
                    for i, col in enumerate(t_table[1]):
                        self.coords(col, (10 + self.x_list[i],
                                          3 + t_y))
                        self.itemconfig(col, text=self.longStringToShort(self.tableData[row][i]))
                    self.tableRect[row] = t_table
                else:
                    t_rect = self.create_rectangle(t_x,
                                                   t_y,
                                                   t_x + t_width,
                                                   t_y + t_height,
                                                   width=1,
                                                   fill=bg)
                    t_rowList = []
                    for col in range(self.column):
                        t_text = self.create_text(10 + self.x_list[col],
                                                  3 + t_y,
                                                  anchor='nw',
                                                  text=self.longStringToShort(self.tableData[row][col]))
                        t_rowList.append(t_text)
                    self.tableRect[row] = [t_rect, t_rowList, t_x, t_y, row]
            else:
                if self.tableRect[row]:
                    self.RectCache.append(self.tableRect[row])
                    self.tableRect[row] = []
        for col in range(1, self.column):
            self.TableLines.append(self.create_line((1 + self.x_list[col], self.titleHeight, 1 + self.x_list[col], self.titleHeight + self.row * self.rowHeight)))

    def longStringToShort(self, String):
        if len(String.encode('gbk')) > 40:
            return String[:18] + '...' + String[-18:]
        else:
            return String
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
                             text=self.longStringToShort(self.titles[col]))
            self.titlesRect.append([t_rect, t_text])

    def cleanData(self):
        if self.tableRect:
            for row in self.tableRect:
                if row:
                    self.coords(row[0], (0,
                                         -100,
                                         100,
                                         -50))
                    for col in row[1]:
                        self.coords(col, (0,
                                          -100))
                    self.RectCache.append(row)
        if self.TableLines:
            for t_line in self.TableLines:
                self.delete(t_line)
        self.tableRect = []
        self.TableLines = []
        self.row = 0
        self.tableData = []
        self.select_row = -1
        self.minScrollY = 0
        self.scrollY = 0

    def setData(self, data, titles, columnWidthList=[], command=None):
        self.cleanData()

        self.scrollY = 0
        self.tableData = data
        self.tableRect = []
        n = len(data)
        for i in range(n):
            self.tableRect.append([])
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
        for i in range(len(add_data)):
            self.tableRect.append([])
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

    def getSelectedItem(self):
        data = None
        if self.select_row != -1:
            data = [self.select_row, self.tableData[self.select_row]]
        return data

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
        self.clickEvent(event, isDoubleClick=1)

    def clickEvent(self, event, isDoubleClick=0):
        if event.y < self.titleHeight:
            n = 0
            while event.x > self.x_list[n] + self.columnWidthList[n]:
                n += 1
            if callable(self.titleCommand):
                self.titleCommand(n)
            return

        # index = -1
        # n = 0
        # for i,t in enumerate(self.tableRect):
        #     if t[3] > event.y - self.titleHeight:
        #         index = n
        #         break
        #     n += 1
        # if index == -1:
        #     return
        index = int((event.y - self.scrollY - self.titleHeight) / self.rowHeight)
        if index < 0 or index > self.row:
            return
        if self.select_row != -1:
            if self.select_row % 2 == 1:
                bg = self.WHITE_COLOR
            else:
                bg = self.BLACK_COLOR
            for t_col in range(self.column):
                if self.tableRect[self.select_row]:
                    rt = self.tableRect[self.select_row][0]
                    self.itemconfigure(rt, fill=bg)
        if self.select_row != index:
            self.select_row = index

            rt = self.tableRect[index][0]
            self.itemconfigure(rt, fill=self.SELECT_COLOR)
        else:
            self.select_row = -1

        if isDoubleClick and callable(self.tableCommand):
            data = [index, self.tableData[index]]
            self.tableCommand(data)

class openFileDialog():
    def __init__(self, master, command=None, startPath=None):
        self.REVERSE_FILE_TABLE = False
        self.nowFileList = None
        self.nowFilePath = None
        if startPath:
            if not startPath.endswith('/'):
                startPath += '/'
            self.nowFilePath = startPath
        else:
            self.nowFilePath = os.getcwd() + '/'
        self.openFile(master)
        self.command = command

    def onDoubleClickFileTable(self, data):
        new_path = data[1][0]
        if new_path == '..':
            self.backUri()
            return
        if os.path.isdir(self.nowFilePath + new_path + '/'):
            self.nowFilePath = self.nowFilePath + new_path + '/'
            self.uriV.set(self.nowFilePath)
            self.refreshFileListBox(self.nowFilePath)

    def refreshFileListBox(self, Path):
        self.nowFileList = self.getFileInfoList(Path)
        self.openfileRoot.mountFrame.fileTable.setData(self.getFileListTable(self.nowFileList[0], filter=self.filterV.get()),
                                                       columnWidthList=[350, 100, 150],
                                                       titles=['文件名', '大小', '修改日期'],
                                                       command=self.reSortFileList)
        self.openfileRoot.mountFrame.fileTable.addData(self.getFileListTable(self.nowFileList[1], filter=self.filterV.get()))

    def reSortFileList(self, num):
        if num == 0:
            self.nowFileList[0].sort(key=lambda x: x.filename, reverse=self.REVERSE_FILE_TABLE)
            self.nowFileList[1].sort(key=lambda x: x.filename, reverse=self.REVERSE_FILE_TABLE)
        if num == 1:
            self.nowFileList[1].sort(key=lambda x: x.size, reverse=self.REVERSE_FILE_TABLE)
        if num == 2:
            self.nowFileList[0].sort(key=lambda x: x.atime, reverse=self.REVERSE_FILE_TABLE)
            self.nowFileList[1].sort(key=lambda x: x.atime, reverse=self.REVERSE_FILE_TABLE)
        print('reSortFileList ',num)

        self.openfileRoot.mountFrame.fileTable.cleanData()
        if self.REVERSE_FILE_TABLE:
            t = [0, 1]
            self.REVERSE_FILE_TABLE = False
        else:
            t = [0, 1]
            self.REVERSE_FILE_TABLE = True
        for i in t:
            self.openfileRoot.mountFrame.fileTable.addData(self.getFileListTable(self.nowFileList[i], filter=self.filterV.get()))

    def backUri(self):
        t_mlist = self.nowFilePath.split('/')[:-2]
        self.nowFilePath = '/'
        for m in t_mlist:
            if m != '':
                self.nowFilePath += (m + '/')
        self.uriV.set(self.nowFilePath)
        self.refreshFileListBox(self.nowFilePath)

    def changeMount(self, event):
        t = self.openfileRoot.mountList.curselection()
        now_mount = self.openfileRoot.mountList.get(t)
        self.nowFilePath = '/media/' + USER_NAME + '/' + now_mount + '/'
        self.uriV.set(self.nowFilePath)
        self.refreshFileListBox(self.nowFilePath)

    def changeFile(self, new_path):
        if new_path == '..':
            self.backUri()
            return
        self.nowFilePath = self.nowFilePath + new_path + '/'
        self.uriV.set(self.nowFilePath)
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

    def getFileListTable(self, nowFileInfoList, filter=None):
        # fileInfoTable = [['..', '', '']]
        fileInfoTable = []
        for fi in nowFileInfoList:
            if filter:
                try:
                    fi.filename.index(filter)
                except:
                    continue
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

    def setFileFilter(self, event):
        print(self.filterV.get())
        self.openfileRoot.mountFrame.fileTable.cleanData()
        for i in (0, 1):
            t_b = self.getFileListTable(self.nowFileList[i], filter=self.filterV.get())
            self.openfileRoot.mountFrame.fileTable.addData(t_b)
        # self.filterMenuIsClicked = True

    def clickOK(self):
        self.openfileRoot.destroy()
        if callable(self.command):
            data = self.openfileRoot.mountFrame.fileTable.getSelectedItem()
            if data:
                self.nowFilePath += data[1][0]
            self.command(self.nowFilePath)
        else:
            print('callback function is wrong')

    def clickCANCEL(self):
        self.openfileRoot.destroy()

    def inputPathFormEntry(self, event):
        newPath = self.uriV.get()
        if os.path.exists(newPath):
            if not newPath.endswith('/'):
                newPath += '/'
            self.nowFilePath = newPath
            self.uriV.set(self.nowFilePath)
            self.refreshFileListBox(self.nowFilePath)
        else:
            self.uriV.set(self.nowFilePath)

    # def onClick(self, event):
    #     self.filterMenuIsClicked = False
    #     if self.filterV.get() == self.oldFilter:
    #         return
    #     self.oldFilter = self.filterV.get()
    #     print(self.oldFilter)

    def openFile(self, master):
        # TODO
        print('openFile')
        self.openfileRoot = Toplevel(master)
        self.openfileRoot.wm_attributes('-topmost',1)
        t_screen_width, t_screen_height = master.maxsize()
        self.openfileRoot.geometry("800x600+%d+%d" % ((t_screen_width - 800) / 2, (t_screen_height - 600) / 2))
        # self.openfileRoot.bind('<Button-1>', self.onClick)

        self.openfileRoot.uirFrame = Frame(self.openfileRoot)
        # openfileRoot.uirFrame.place(in_=openfileRoot, x=10, y=10, relwidth=0.9, anchor=NW)
        self.openfileRoot.uirFrame.pack(fill=X, expand=0, padx=5, pady=5)
        self.openfileRoot.uirFrame.backButton = Button(self.openfileRoot.uirFrame, text="后退", relief=FLAT, command=self.backUri, height=1)
        self.openfileRoot.uirFrame.backButton.pack(side=LEFT,padx=5)
        self.uriV = StringVar()
        self.openfileRoot.uirFrame.mUriEntry = Entry(self.openfileRoot.uirFrame, textvariable=self.uriV)
        self.openfileRoot.uirFrame.mUriEntry.bind('<Return>', self.inputPathFormEntry)
        self.openfileRoot.uirFrame.mUriEntry.pack(side=RIGHT, fill=X, expand=1)

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

        self.openfileRoot.mountFrame = Frame(self.openfileRoot)
        self.openfileRoot.mountFrame.pack(fill=BOTH, expand=1, padx=5, pady=5)
        self.openfileRoot.mountFrame.fileTable = myTable(self.openfileRoot.mountFrame, height=450)
        self.openfileRoot.mountFrame.fileTable.pack(fill=X, expand=1)
        self.openfileRoot.mountFrame.fileTable.setDoubleButtonCallback(self.onDoubleClickFileTable)

        self.filterV = StringVar()
        self.openfileRoot.mountFrame.mFilterEntry = Entry(self.openfileRoot.mountFrame, textvariable=self.filterV, width=30)
        self.openfileRoot.mountFrame.mFilterEntry.bind('<KeyRelease>', self.setFileFilter)
        self.openfileRoot.mountFrame.mFilterEntry.pack(side=RIGHT, padx=50)

        self.openfileRoot.okFrame = Frame(self.openfileRoot)
        self.openfileRoot.okFrame.pack(fill=X, expand=1, padx=25, pady=5)
        self.openfileRoot.okFrame.okButton = Button(self.openfileRoot.okFrame, text='确认', width=10, command=self.clickOK)
        self.openfileRoot.okFrame.okButton.pack(side=RIGHT, padx=25)
        self.openfileRoot.okFrame.cancelButton = Button(self.openfileRoot.okFrame, text='取消', width=10, command=self.clickCANCEL)
        self.openfileRoot.okFrame.cancelButton.pack(side=RIGHT, padx=25)

        self.uriV.set(self.nowFilePath)
        self.refreshFileListBox(self.nowFilePath)

