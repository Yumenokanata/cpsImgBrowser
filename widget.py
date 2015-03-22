from tkinter import *
from tkinter.font import *
from tkinter import ttk
from tkinter import colorchooser
from tkinter.messagebox import *
import os
import getpass
import time
import hashlib
from cpsImgBrowser import _configData

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

    def __init__(self, master=None, rowWidth=170, rowHeight=25, titleHeight=25, column=0, row=0, data=[], height=450, font=None, bg='#ffffff'):
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
        self.bind('<B1-Motion>', self.scrollBarEvent)
        self.bind('<ButtonRelease>', self.releaseEvent)
        self.scrollY = 0
        self.minScrollY = 0
        self.TableLines = []
        self.x_list = []
        self.columnWidthList = []
        self.titleCommand = None
        self.titlesRect = []
        self.titles = []
        self.doubleClickCommand = None
        self.onClickCommand = None
        self.RectCache = []
        h = self.winfo_height()
        if h != 1:
            self.height = h
        else:
            self.height = 600
        self.showScrollBar = False
        self.scrollBarHeight = self.height
        self.scrollBarY = 0
        self.clickScrollBar = False
        self.scrollBarBgRect = None
        self.scrollBarRect = None

        self.SELECT_COLOR = '#FF7F50'
        self.BLACK_COLOR = '#F5F5F5'
        self.WHITE_COLOR = 'white'
        self.TITLE_COLOR = '#D3D3D3'
        self.bg = self.create_rectangle(0, 0, 450, self.height, fill=bg)
        if font:
            self.ft = font
        else:
            self.ft = Font(family='Fixdsys', size=10)

    def draw(self):
        h = self.winfo_height()
        if h != 1 and h != self.height:
            self.height = h
            self.minScrollY = min(h - (self.row + 1) * self.rowHeight - 2, 0)
            self.scrollBarHeight = self.height * min(1, self.height / self.row / self.rowHeight)
            self.coords(self.bg, 0, 0, self.rightPos, self.height)

        self.scrollY = min(self.scrollY, 0)
        self.scrollY = max(self.scrollY, self.minScrollY)

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
                if t_y > self.height + t_height:
                    for i in range(row - 1, len(self.tableData)):
                        if self.tableRect[i]:
                            self.coords(self.tableRect[i][0], (0, -100, 100, -50))
                            for col in self.tableRect[i][1]:
                                self.coords(col, (0, -100))
                            self.RectCache.append(self.tableRect[i])
                            self.tableRect[i] = []
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
                        self.itemconfig(col, text=self.longStringToShort(self.tableData[row][i], self.columnWidthList[i]))
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
                                                  text=self.longStringToShort(self.tableData[row][col], self.columnWidthList[col]),
                                                  font=self.ft)
                        t_rowList.append(t_text)
                    self.tableRect[row] = [t_rect, t_rowList]
            else:
                if self.tableRect[row]:
                    self.coords(self.tableRect[row][0], (0, -100, 100, -50))
                    for col in self.tableRect[row][1]:
                        self.coords(col, (0, -100))
                    self.RectCache.append(self.tableRect[row])
                    self.tableRect[row] = []
        # print('self.RectCache.append: ', t)
        for col in range(1, self.column):
            self.TableLines.append(self.create_line((1 + self.x_list[col],
                                                     self.titleHeight,
                                                     1 + self.x_list[col],
                                                     self.titleHeight + self.row * self.rowHeight)))
        if self.height < self.row * self.rowHeight:
            self.scrollBarY = max(self.height * (-self.scrollY / self.row / self.rowHeight) - 2, 2)
            self.coords(self.scrollBarRect, (self.rightPos, self.scrollBarY, self.rightPos + 10, self.scrollBarY + self.scrollBarHeight))

    def longStringToShort(self, String, width):
        if self.ft.measure(String) > width - 20:
            cut_len = (width - 35 - self.ft.measure('...')) / 2
            top_string = ''
            for s in String:
                top_string += s
                if self.ft.measure(top_string) > cut_len:
                    break
            bottom_string = ''
            for i in range(1, len(String) + 1):
                s = String[-i]
                bottom_string = s + bottom_string
                if self.ft.measure(bottom_string) > cut_len:
                    break
            return top_string + '...' + bottom_string
        return String

    def longStringToShort2(self, String, width):
        length = 0.0
        b_string = String.encode('utf-8')
        b_string.decode('utf-8')
        for i in b_string:
            if i >= 128:
                length += 0.666
            else:
                length += 1
        if length > width / 20 * 2:
            cut_len = min(int(width * 2 / 20 - 1.5), int(length / 3))
            t_length = 0
            for n, i in enumerate(b_string):
                if i >= 128:
                    t_length += 0.66
                else:
                    t_length += 1
                if t_length > cut_len:
                    t_cut_num = n
                    break
            n = 0
            while True:
                try:
                    top_string = b_string[:t_cut_num + n].decode('utf-8')
                    break
                except:
                    n += 1
            t_length = 0
            for i in range(1, len(b_string)):
                b = b_string[-i]
                if b >= 128:
                    t_length += 0.66
                else:
                    t_length += 1
                if t_length > cut_len:
                    t_cut_num = i
                    break
            n = 0
            while True:
                try:
                    bottom_string = b_string[-(t_cut_num + n):].decode('utf-8')
                    break
                except:
                    n += 1
            return top_string + '...' + bottom_string
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
                raise Exception
            for col_w in columnWidthList:
                x_list.append(t_x_offset)
                t_x_offset += col_w
        self.columnWidthList = columnWidthList
        self.x_list = x_list
        self.rightPos = x_list[-1] + columnWidthList[-1] + 4
        if self.scrollBarBgRect:
            self.delete(self.scrollBarBgRect)
        self.scrollBarBgRect = self.create_rectangle(self.rightPos, 0, self.rightPos + 10, self.height, width=1, fill='#ffffff')
        if self.scrollBarRect:
            self.delete(self.scrollBarRect)
        self.scrollBarRect = self.create_rectangle(self.rightPos, 0, self.rightPos + 10, self.height, width=2, outline='#B8B8B8', fill='#E6E6E6')

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
                                      text=self.longStringToShort(self.titles[col], self.columnWidthList[col]))
            self.titlesRect.append([t_rect, t_text])

    def cleanData(self):
        if self.tableRect:
            for row in self.tableRect:
                if row:
                    self.coords(row[0], (0, -100, 100, -50))
                    for col in row[1]:
                        self.coords(col, (0, -100))
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
        self.coords(self.bg, 0, 0, self.rightPos, self.height)

        # TODO
        self.scrollBarHeight = self.height * min(1, self.height / self.row / self.rowHeight)
        self.minScrollY = min(self.height - (self.row + 1) * self.rowHeight - 2, 0)
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

        h = self.winfo_height()
        if h != 1:
            self.height = h
        self.coords(self.bg, 0, 0, self.rightPos, self.height)

        self.row += len(add_data)
        self.scrollBarHeight = self.height * min(1, self.height / self.row / self.rowHeight)
        self.minScrollY = min(self.height - (self.row + 1) * self.rowHeight - 2, 0)
        self.draw()

        for col in range(1, self.column):
            self.TableLines.append(self.create_line((1 + self.x_list[col],
                                                     self.scrollY + self.titleHeight,
                                                     1 + self.x_list[col],
                                                     self.scrollY + self.titleHeight + self.row * self.rowHeight)))

        self.refreshTitle()

    def getSelectedItem(self):
        data = None
        if self.select_row != -1:
            data = [self.select_row, self.tableData[self.select_row]]
        return data

    def setDoubleClickCallback(self, command):
        if callable(command):
            self.doubleClickCommand = command

    def setOnClickCallback(self, command):
        if callable(command):
            self.onClickCommand = command

    def mouseWheel(self, event):
        if event.num == 4:
            self.scrollY += 20
        elif event.num == 5:
            self.scrollY -= 20

        self.draw()
        self.refreshTitle()
        # for row in range(len(self.tableRect)):
        #     t_rect = self.tableRect[row][0]
        #     t_rowList = self.tableRect[row][1]
        #     self.move(t_rect, 0, direct)
        #     for col in range(self.column):
        #         self.move(t_rowList[col], 0, direct)
        pass

    def scrollBarEvent(self, event):
        if self.clickScrollBar:
            self.scrollY -= (event.y - self.startMotionY) / self.height * self.row * self.rowHeight
            self.startMotionY = event.y
            self.draw()

    def releaseEvent(self, event):
        self.clickScrollBar = False

    def onClick(self, event):
        self.clickEvent(event)

    def onDoubleClick(self, event):
        self.clickEvent(event, isDoubleClick=1)

    def clickEvent(self, event, isDoubleClick=0):
        if event.x > self.rightPos:
            if self.scrollBarY < event.y < self.scrollBarY + self.scrollBarHeight:
                self.clickScrollBar = True
                self.startMotionY = event.y
            return

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

        if isDoubleClick and callable(self.doubleClickCommand):
            data = [index, self.tableData[index]]
            self.doubleClickCommand(data)
        elif callable(self.onClickCommand):
            data = [index, self.tableData[index]]
            self.onClickCommand(data)

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
        self.openfileRoot.mainloop()

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
        self.REVERSE_FILE_TABLE = not self.REVERSE_FILE_TABLE
        self.openfileRoot.mountFrame.fileTable.addData(self.getFileListTable(self.nowFileList[0], filter=self.filterV.get()))
        self.openfileRoot.mountFrame.fileTable.addData(self.getFileListTable(self.nowFileList[1], filter=self.filterV.get()))

    def backUri(self):
        t_mlist = self.nowFilePath.split('/')[:-2]
        self.nowFilePath = '/'
        for m in t_mlist:
            if m != '':
                self.nowFilePath += (m + '/')
        self.uriV.set(self.nowFilePath)
        self.refreshFileListBox(self.nowFilePath)

    def changeMount(self, event):
        t = self.openfileRoot.mountList.curselection()[0]
        self.nowFilePath = self.mountList[t] + '/'
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
        self.openfileRoot.wm_resizable(width=False, height=False)
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
        mListMedia = os.listdir('/media/' + USER_NAME)
        for m in mListMedia:
            self.openfileRoot.mountList.insert(END, m)
        t_listHome = os.listdir('/home/' + USER_NAME)
        mListHome = []
        for m in t_listHome:
            if not m.startswith('.'):
                mListHome.append(m)
                self.openfileRoot.mountList.insert(END, m)
        self.mountList = ['/media/' + USER_NAME + '/' + info1 for info1 in mListMedia] +\
                         ['/home/' + USER_NAME + '/' + info2 for info2 in mListHome]
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
        self.openfileRoot.mountFrame.fileTable.setDoubleClickCallback(self.onDoubleClickFileTable)

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

class configDialog():
    def __init__(self, master, command=None, oldConfig=None):
        self.scaleModeList = ['最近邻插值',
                              '抗锯齿',
                              '双线性插值',
                              '立方插值',
                              '自动']
        self.command = command
        self.configData = oldConfig
        self.ft = Font(family='Fixdsys', size=10)
        self.configRoot = Toplevel(master)
        self.configRoot.wm_attributes('-topmost', 0.5)
        self.configRoot.wm_resizable(width=False, height=False)
        s_x = master.winfo_x()
        s_y = master.winfo_y()
        t = master.winfo_geometry()
        win_w = int(t.split('x')[0])
        win_h = int(t.split('x')[1].split('+')[0])
        self.configRoot.geometry("500x320+%d+%d" % ((win_w - 500) / 2 + s_x, (win_h - 450) / 2 + s_y))

        self.initBackgroundChoice(self.configRoot)
        self.initFile(self.configRoot)
        self.initOther(self.configRoot)

        self.configRoot.cancelButton = Button(self.configRoot, text='取消', command=self.clickCancel)
        self.configRoot.cancelButton.place(x=305, y=280, width=70, height=30)
        self.configRoot.cancelButton = Button(self.configRoot, text='确认', command=self.clickOk)
        self.configRoot.cancelButton.place(x=395, y=280, width=70, height=30)

        self.configRoot.mainloop()

    def clickCancel(self):
        if callable(self.command):
            self.command(None)
        self.configRoot.destroy()

    def clickOk(self):
        t_b = self.backIntV.get()
        if t_b == 0:
            self.configData.background = '#d3d3d3'
        elif t_b == 1:
            self.configData.background = '#000000'
        elif t_b == 2:
            self.configData.background = self.customBackground
        self.configData.customBackground = self.customBackground
        self.configData.restore = bool(self.restore.get())
        self.configData.saveLatelyFileInfo = bool(self.saveLatelyFileInfo.get())
        self.configData.scanSubFile = bool(self.scanSubFile.get())
        self.configData.scanSubFileDepth = self.scanSubFileDepth.get()
        self.configData.useCache = bool(self.useCache.get())
        self.configData.slideTime = self.slideTime.get()
        self.configData.saveFilePassword = bool(self.saveFilePassword.get())
        self.configData.useCustomSort = bool(self.useCustomSort.get())
        self.configData.scaleMode = self.scaleModeList.index(self.scaleMode.get())
        if callable(self.command):
            self.command(self.configData)
        self.configRoot.destroy()

    def initBackgroundChoice(self, master):
        master.backgroundFrame = LabelFrame(master, text='背景', font=self.ft)
        master.backgroundFrame.place(x=20, y=10, width=220, height=150, anchor=NW)
        self.backIntV = IntVar()
        if self.configData.background == '#d3d3d3':
            self.backIntV.set(0)
            self.customBackground = '#ffffff'
        elif self.configData.background == '#000000':
            self.backIntV.set(1)
            self.customBackground = '#ffffff'
        else:
            self.customBackground = self.configData.background
            self.backIntV.set(2)

        master.backgroundFrame.lightRadioButton = Radiobutton(master.backgroundFrame,
                                                              text='使用灰色背景',
                                                              font=self.ft,
                                                              variable=self.backIntV,
                                                              value=0)
        master.backgroundFrame.lightRadioButton.grid(columnspan=2, sticky=NW)
        master.backgroundFrame.blackRadioButton = Radiobutton(master.backgroundFrame,
                                                              text='使用黑色背景',
                                                              font=self.ft,
                                                              variable=self.backIntV,
                                                              value=1)
        master.backgroundFrame.blackRadioButton.grid(row=1, columnspan=2, sticky=NW)
        master.backgroundFrame.customRadioButton = Radiobutton(master.backgroundFrame,
                                                               text='使用自定义颜色',
                                                               font=self.ft,
                                                               variable=self.backIntV,
                                                               value=2)
        master.backgroundFrame.customRadioButton.grid(row=2, sticky=NW, pady=4)
        master.backgroundFrame.colorChoiceButton = Button(master.backgroundFrame,
                                                          width=6,
                                                          command=self.choiceColor)
        master.backgroundFrame.colorChoiceButton.grid(row=2, column=1, sticky=NW, padx=10)
        master.backgroundFrame.colorChoiceButton.colorLabel = Label(master.backgroundFrame.colorChoiceButton,
                                                                    bg=self.customBackground)
        master.backgroundFrame.colorChoiceButton.colorLabel.place(x=-1,
                                                                  y=-1,
                                                                  relx=0.5,
                                                                  rely=0.5,
                                                                  anchor=CENTER,
                                                                  relheight=0.8,
                                                                  relwidth=0.8)
        master.backgroundFrame.colorChoiceButton.colorLabel.bind('<Button-1>', self.choiceColor)

    def choiceColor(self, *args):
        self.configRoot.wm_attributes('-topmost', 0)
        color_w = colorchooser.Chooser(master=self.configRoot,initialcolor=self.configData.background)
        c = color_w.show()[1]
        self.configRoot.backgroundFrame.colorChoiceButton.colorLabel['bg'] = c
        self.customBackground = c
        self.configRoot.wm_attributes('-topmost', 0.5)

    def initFile(self, master):
        master.fileFrame = LabelFrame(master, text='文件', font=self.ft)
        master.fileFrame.place(x=260, y=10, width=220, height=150, anchor=NW)

        self.restore = IntVar()
        self.restore.set(self.configData.restore)
        master.fileFrame.restoreCheckButton = Checkbutton(master.fileFrame,
                                                                text='启动时恢复上次浏览',
                                                                font=self.ft,
                                                                variable=self.restore)
        master.fileFrame.restoreCheckButton.grid(sticky=NW)

        self.saveLatelyFileInfo = IntVar()
        self.saveLatelyFileInfo.set(self.configData.saveLatelyFileInfo)
        master.fileFrame.saveLatelyCheckButton = Checkbutton(master.fileFrame,
                                                                   text='保存最近文件信息',
                                                                   font=self.ft,
                                                                   variable=self.saveLatelyFileInfo)
        master.fileFrame.saveLatelyCheckButton.grid(row=1, sticky=NW)

        self.scanSubFile = IntVar()
        self.scanSubFile.set(self.configData.scanSubFile)
        master.fileFrame.scanSubFileCheckButton = Checkbutton(master.fileFrame,
                                                                    text='扫描子文件夹',
                                                                    font=self.ft,
                                                                    variable=self.scanSubFile)
        master.fileFrame.scanSubFileCheckButton.grid(row=2, sticky=NW)

        master.fileFrame.scanSubFileDepthLabel = Label(master.fileFrame,
                                                             text='扫描扫描深度(-1为无限制)',
                                                             font=self.ft)
        master.fileFrame.scanSubFileDepthLabel.grid(row=3, sticky=NW, padx=30)
        self.scanSubFileDepth = IntVar()
        self.scanSubFileDepth.set(self.configData.scanSubFileDepth)
        master.fileFrame.scanSubFileDepthSpinbox = Spinbox(master.fileFrame,
                                                                 from_=-1,
                                                                 to=99,
                                                                 increment=1,
                                                                 textvariable=self.scanSubFileDepth,)
        master.fileFrame.scanSubFileDepthSpinbox.grid(row=4, sticky=NW, padx=30)
        master.fileFrame.scanSubFileDepthSpinbox.bind('<Return>', self.inputDepth)

    def inputDepth(self, *args):
        try:
            depth = int(self.scanSubFileDepth.get())
            if depth > 99:
                raise Exception
            elif depth < -1:
                raise Exception
            self.configData.scanSubFileDepth = depth
        except:
            self.scanSubFileDepth.set(self.configData.scanSubFileDepth)

    def initOther(self, master):
        master.otherFrame = LabelFrame(master, text='杂项', font=self.ft)
        master.otherFrame.place(x=20, y=170, width=460, height=100, anchor=NW)

        self.saveFilePassword = IntVar()
        self.saveFilePassword.set(self.configData.saveFilePassword)
        master.otherFrame.saveFilePasswordCheckButton = Checkbutton(master.otherFrame,
                                                                    text='保存文件密码',
                                                                    font=self.ft,
                                                                    variable=self.saveFilePassword)
        master.otherFrame.saveFilePasswordCheckButton.place(relx=0, rely=0, anchor=NW)

        self.useCache = IntVar()
        self.useCache.set(self.configData.useCache)
        master.otherFrame.useCacheCheckButton = Checkbutton(master.otherFrame,
                                                            text='启用缓存',
                                                            font=self.ft,
                                                            variable=self.useCache)
        master.otherFrame.useCacheCheckButton.place(relx=0, rely=0.3, anchor=NW)

        self.useCustomSort = IntVar()
        self.useCustomSort.set(self.configData.useCustomSort)
        master.otherFrame.useCustomSortCheckButton = Checkbutton(master.otherFrame,
                                                                 text='使用专有排序规则',
                                                                 font=self.ft,
                                                                 variable=self.useCustomSort)
        master.otherFrame.useCustomSortCheckButton.place(relx=0, rely=0.6, anchor=NW)

        master.otherFrame.slideTimeLabel = Label(master.otherFrame,
                                                 text='幻灯片延时',
                                                 font=self.ft)
        master.otherFrame.slideTimeLabel.place(relx=0.45, rely=0, anchor=NW)
        self.slideTime = IntVar()
        self.slideTime.set(self.configData.slideTime)
        master.otherFrame.slideTimeSpinbox = Spinbox(master.otherFrame,
                                                     from_=1,
                                                     to=20,
                                                     increment=1,
                                                     textvariable=self.slideTime)
        master.otherFrame.slideTimeSpinbox.place(relx=0.67, rely=0, relwidth=0.3, anchor=NW)
        master.otherFrame.slideTimeSpinbox.bind('<Return>', self.inputSlide)

        master.otherFrame.scaleModeLabel = Label(master.otherFrame,
                                                 text='图像放大方式',
                                                 font=self.ft)
        master.otherFrame.scaleModeLabel.place(relx=0.45, rely=0.4, anchor=NW)
        self.scaleMode = StringVar()
        self.scaleMode.set(self.scaleModeList[self.configData.scaleMode])
        master.otherFrame.scaleModeCombo = ttk.Combobox(master.otherFrame, textvariable=self.scaleMode, values=self.scaleModeList)
        master.otherFrame.scaleModeCombo.place(relx=0.668, rely=0.38, relwidth=0.301, relheight=0.35, anchor=NW)

    def inputSlide(self, *args):
        try:
            slideTime = int(self.slideTime.get())
            if slideTime > 20:
                raise Exception
            elif slideTime < 1:
                raise Exception
            self.configData.slideTime = slideTime
        except:
            self.slideTime.set(self.configData.slideTime)

class passwordDialog():
    def __init__(self, master, defaultPassword, filePassword, command):
        self.command = command
        self.defaultPassword = defaultPassword
        self.filePassword = filePassword.copy()
        self.keys = filePassword.keys()
        self.changed = False
        self.REVERSE = False
        self.ft = Font(family='Fixdsys', size=10)
        self.passwordRoot = Toplevel(master)
        self.passwordRoot.wm_attributes('-topmost', 0.5)
        self.passwordRoot.wm_resizable(width=False, height=False)
        self.passwordRoot.title = '密码管理'
        # self.passwordRoot.wm_resizable(width=False, height=False)
        s_x = master.winfo_x()
        s_y = master.winfo_y()
        t = master.winfo_geometry()
        win_w = int(t.split('x')[0])
        win_h = int(t.split('x')[1].split('+')[0])
        self.passwordRoot.geometry("800x600+%d+%d" % ((win_w - 800) / 2 + s_x, (win_h - 600) / 2 + s_y))

        self.passwordRoot.tabNotebook = ttk.Notebook(self.passwordRoot)
        self.passwordRoot.tabNotebook.place(x=5, y=5, relwidth=0.987, relheight=0.9)
        self.initFilePwdTab(self.passwordRoot.tabNotebook)
        self.initDefaultPwdTab(self.passwordRoot.tabNotebook)

        self.passwordRoot.cleanButton = ttk.Button(self.passwordRoot,
                                                   text='取消',
                                                   width=10,
                                                   command=self.onclickCancel)
        self.passwordRoot.cleanButton.place(relx=1, rely=1, x=-160, y=-12, anchor=SE)
        self.passwordRoot.cleanButton = ttk.Button(self.passwordRoot,
                                                   text='确认',
                                                   width=10,
                                                   command=self.onclickOK)
        self.passwordRoot.cleanButton.place(relx=1, rely=1, x=-40, y=-12, anchor=SE)

        self.passwordRoot.mainloop()

    def initFilePwdTab(self, notebook):
        notebook.filePwdTab = Frame(notebook)
        ft = Font(family='Fixdsys', size=9)
        notebook.filePwdTab.passwordTable = myTable(notebook.filePwdTab, height=360)
        notebook.filePwdTab.passwordTable.place(x=20, y=10, relwidth=0.95, anchor=NW)
        notebook.filePwdTab.passwordTable.setOnClickCallback(self.onSelectedItem)
        self.emptyDict = {}
        self.dataList = self.getDataToList(self.filePassword)
        notebook.filePwdTab.passwordTable.setData(data=self.dataList, titles=['文件名', '密码', '路径'], columnWidthList=[370, 150, 210], command=self.sortList)

        notebook.filePwdTab.infoFrame = LabelFrame(notebook.filePwdTab, text='信息')
        notebook.filePwdTab.infoFrame.filenameTitleLabel = ttk.Label(notebook.filePwdTab.infoFrame,
                                                                     text='文件名:',
                                                                     wraplength=270,
                                                                     font=ft,
                                                                     justify=LEFT)
        notebook.filePwdTab.infoFrame.filenameTitleLabel.grid(row=0, column=0, padx=10, sticky=NW)
        self.filenameVar = StringVar()
        notebook.filePwdTab.infoFrame.filenameLabel = ttk.Label(notebook.filePwdTab.infoFrame,
                                                                textvariable=self.filenameVar,
                                                                wraplength=360,
                                                                font=ft,
                                                                justify=LEFT)
        notebook.filePwdTab.infoFrame.filenameLabel.grid(row=0, column=1, sticky=NW)
        notebook.filePwdTab.infoFrame.filenameTitleLabel = ttk.Label(notebook.filePwdTab.infoFrame,
                                                                     text='密码:',
                                                                     wraplength=270,
                                                                     font=ft,
                                                                     justify=LEFT)
        notebook.filePwdTab.infoFrame.filenameTitleLabel.grid(row=1, column=0, padx=10, sticky=NW)
        self.passwordVar = StringVar()
        notebook.filePwdTab.infoFrame.filenameLabel = ttk.Label(notebook.filePwdTab.infoFrame,
                                                                textvariable=self.passwordVar,
                                                                wraplength=360,
                                                                font=ft,
                                                                justify=LEFT)
        notebook.filePwdTab.infoFrame.filenameLabel.grid(row=1, column=1, padx=10, sticky=NW)
        notebook.filePwdTab.infoFrame.filenameTitleLabel = ttk.Label(notebook.filePwdTab.infoFrame,
                                                                     text='位置:',
                                                                     wraplength=270,
                                                                     font=ft,
                                                                     justify=LEFT)
        notebook.filePwdTab.infoFrame.filenameTitleLabel.grid(row=2, column=0, padx=10, sticky=NW)
        self.uriVar = StringVar()
        notebook.filePwdTab.infoFrame.filenameLabel = ttk.Label(notebook.filePwdTab.infoFrame,
                                                                textvariable=self.uriVar,
                                                                wraplength=360,
                                                                font=ft,
                                                                justify=LEFT)
        notebook.filePwdTab.infoFrame.filenameLabel.grid(row=2, column=1, sticky=NW)
        notebook.filePwdTab.infoFrame.place(x=20, y=380, width=400, height=120, anchor=NW)

        notebook.filePwdTab.buttonFrame = Frame(notebook.filePwdTab)
        self.filterV = StringVar()
        notebook.filePwdTab.buttonFrame.filterEntry = Entry(notebook.filePwdTab.buttonFrame,
                                                            textvariable=self.filterV,
                                                            width=27)
        notebook.filePwdTab.buttonFrame.filterEntry.bind('<KeyRelease>', self.setFileFilter)
        notebook.filePwdTab.buttonFrame.filterEntry.place(x=0, y=0, anchor=NW)
        self.sumVar = StringVar()
        self.sumVar.set('总数: ' + str(len(self.dataList)))
        notebook.filePwdTab.buttonFrame.sumLabel = ttk.Label(notebook.filePwdTab.buttonFrame,
                                                             textvariable=self.sumVar,
                                                             wraplength=360,
                                                             font=ft,
                                                             justify=LEFT)
        notebook.filePwdTab.buttonFrame.sumLabel.place(relx=1, x=-50, y=1, anchor=NE)
        notebook.filePwdTab.buttonFrame.cleanButton = ttk.Button(notebook.filePwdTab.buttonFrame,
                                                                 text='清空密码',
                                                                 width=10,
                                                                 command=self.cleanPwdList)
        notebook.filePwdTab.buttonFrame.cleanButton.place(x=0, y=30, anchor=NW)
        notebook.filePwdTab.buttonFrame.cleanButton = ttk.Button(notebook.filePwdTab.buttonFrame,
                                                                 text='删除密码',
                                                                 width=10,
                                                                 command=self.deleteOne)
        notebook.filePwdTab.buttonFrame.cleanButton.place(x=120, y=30, anchor=NW)

        notebook.filePwdTab.buttonFrame.place(x=440, y=390, width=340, height=140, anchor=NW)

        notebook.add(notebook.filePwdTab, text='已保存密码')

    def getDataToList(self, data):
        t_list = []
        self.emptyDict = {}
        for k, info in data.items():
            if info['filename'] and info['password']:
                t_list.append([info['filename'], info['password'], info['uri']])
            else:
                self.emptyDict.update({k: info})
        return t_list

    def onSelectedItem(self, data):
        self.filenameVar.set(data[1][0])
        self.passwordVar.set(data[1][1])
        self.uriVar.set(data[1][2])

    def setFileFilter(self, event):
        filter_word = self.filterV.get()
        if filter_word:
            self.passwordRoot.tabNotebook.filePwdTab.passwordTable.cleanData()
            self.passwordRoot.tabNotebook.filePwdTab.passwordTable.addData(self.filter(filter_word))
        else:
            self.passwordRoot.tabNotebook.filePwdTab.passwordTable.cleanData()
            self.passwordRoot.tabNotebook.filePwdTab.passwordTable.addData(self.dataList)

    def filter(self, filter_word):
        t_list = []
        for l in self.dataList:
            try:
                l[0].index(filter_word)
                t_list.append(l)
            except:
                continue
        return t_list

    def sortList(self, num):
        if num == 0:
            self.dataList.sort(key=lambda x: x[0], reverse=self.REVERSE)
        elif num == 1:
            self.dataList.sort(key=lambda x: x[1], reverse=self.REVERSE)
        elif num == 2:
            self.dataList.sort(key=lambda x: x[2], reverse=self.REVERSE)

        self.REVERSE = not self.REVERSE
        filter_word = self.filterV.get()
        if filter_word:
            self.passwordRoot.tabNotebook.filePwdTab.passwordTable.cleanData()
            self.passwordRoot.tabNotebook.filePwdTab.passwordTable.addData(self.filter(filter_word))
        else:
            self.passwordRoot.tabNotebook.filePwdTab.passwordTable.cleanData()
            self.passwordRoot.tabNotebook.filePwdTab.passwordTable.addData(self.dataList)

    def cleanPwdList(self):
        self.passwordRoot.wm_attributes('-topmost', 0)
        if askquestion(title="清除密码", message="是否清除所有已保存密码?") == YES:
            self.dataList = []
            self.keys = {}
            self.sumVar.set('总数: ' + str(len(self.dataList)))
            self.passwordRoot.tabNotebook.filePwdTab.passwordTable.cleanData()
        self.passwordRoot.wm_attributes('-topmost', 0.5)

    def deleteOne(self):
        # self.passwordRoot.wm_attributes('-topmost', 0)
        # if askquestion(title="删除密码", message="是否删除保存的所选文件密码记录?") == YES:
        del self.filePassword[hashlib.md5((self.uriVar.get() + self.filenameVar.get()).encode("utf-8")).hexdigest()]
        self.dataList.remove([self.filenameVar.get(), self.passwordVar.get(), self.uriVar.get()])
        self.sumVar.set('总数: ' + str(len(self.dataList)))
        self.passwordRoot.tabNotebook.filePwdTab.passwordTable.cleanData()
        self.passwordRoot.tabNotebook.filePwdTab.passwordTable.addData(self.dataList)
        # self.passwordRoot.wm_attributes('-topmost', 0.5)

    def initDefaultPwdTab(self, notebook):
        notebook.defaultPwdTab = Frame(notebook)
        ft = Font(family='Fixdsys', size=10)

        notebook.defaultPwdTab.defaultText = Text(notebook.defaultPwdTab, font=ft)
        defaultString = ''
        for p in self.defaultPassword:
            defaultString += (p + '\n')
        notebook.defaultPwdTab.defaultText.insert(1.0, defaultString)
        notebook.defaultPwdTab.defaultText.place(x=20, y=20, relwidth=0.95, height=400, anchor=NW)

        notebook.defaultPwdTab.infoLabel = ttk.Label(notebook.defaultPwdTab,
                                                     text='')

        notebook.add(notebook.defaultPwdTab, text='默认密码')

    def onclickOK(self):
        t_s = self.passwordRoot.tabNotebook.defaultPwdTab.defaultText.get('1.0', END)
        t_list = []
        for s in t_s.split('\n'):
            if s:
                t_list.append(s)
        print(t_list)
        if t_list == []:
            t_list = [0]
        if callable(self.command):
            self.command(t_list, self.filePassword)
        self.passwordRoot.destroy()

    def onclickCancel(self):
        if callable(self.command):
            self.command(None, None)
        self.passwordRoot.destroy()

# TODO:机制测试失败
def myAskString(master, title, message):
    import threading
    t_Lock = threading.Lock()
    t_d = _myDialog(master, Lock=t_Lock, title=title, message=message)
    t_Lock.acquire()
    returnData = t_d.returnData
    t_Lock.release()
    return returnData

class _myDialog():
    def __init__(self, master, Lock, title, message):
        self.Lock = Lock
        self.Lock.acquire()
        self.root = tkinter.Tk()
        self.root.wm_attributes('-topmost', 1)
        self.returnData = None
        self.root.protocol('WM_DELETE_WINDOW', self.closeWinWhenCancel)
        self.root.bind('<Return>', self.colseWinWhenOK)
        self.root.wm_resizable(height=False)
        s_x = master.winfo_x()
        s_y = master.winfo_y()
        t = master.winfo_geometry()
        win_w = int(t.split('x')[0])
        win_h = int(t.split('x')[1].split('+')[0])
        self.root.geometry("200x150+%d+%d" % ((win_w - 200) / 2 + s_x, (win_h - 150) / 2 + s_y))

        self.root.title(title)
        self.root.messageLabel = Label(self.root, text=message)
        self.root.messageLabel.place(relx=0, rely=0, x=20, relwidth=0.9, height=30, anchor=NW)

        self.callbackData = StringVar()
        self.root.inputEntry = Entry(self.root, textvariable=self.callbackData, width=30)
        self.root.inputEntry.place(relx=0, rely=0.3, x=20, relwidth=0.9, height=30, anchor=NW)

        self.root.cancelButton = Button(self.root, text='取消', command=self.closeWinWhenCancel)
        self.root.cancelButton.place(relx=1, rely=1, x=-90, y=-10, width=70, height=30, anchor=SE)
        self.root.cancelButton = Button(self.root, text='确认', command=self.closeWinWhenCancel)
        self.root.cancelButton.place(relx=1, rely=1, x=-40, y=-10, width=70, height=30, anchor=SE)
        self.root.mainloop()
        self.closeWinWhenCancel()

    def closeWinWhenCancel(self):
        self.root.destroy()
        self.Lock.release()

    def colseWinWhenOK(self):
        self.returnData = self.callbackData.get()
        self.closeWinWhenCancel()