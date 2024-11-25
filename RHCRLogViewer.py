import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QSlider, QLabel, QFileDialog, QGraphicsRectItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QHBoxLayout, QPushButton, QGraphicsLineItem, QGraphicsRectItem, QGraphicsItem,QGraphicsTextItem
from PyQt5.QtGui import QDragEnterEvent, QDropEvent,QPen, QColor,QBrush,QFont,QKeyEvent,QMouseEvent,QPainter
import json as js
import re

class GridAndAxesItem(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemHasNoContents, False)  # 允许绘制内容

    def boundingRect(self):
        # 设置图形项的边界框，这个边界框定义了图形项的绘制区域
        return QRectF(-40000, -40000, 80000, 80000)

    def paint(self, painter, option, widget=None):
        # 设置画笔颜色和宽度
        painter.setPen(QPen(QColor(200, 200, 200), 1, Qt.SolidLine))

        # 绘制网格
        grid_size = 20
        for x in range(-40000, 40001, grid_size):
            painter.drawLine(x, -40000, x, 40000)  # 垂直线
        for y in range(-40000, 40001, grid_size):
            painter.drawLine(-40000, y, 40000, y)  # 水平线

        # 设置坐标轴的画笔
        painter.setPen(QPen(QColor(0, 0, 0), 2, Qt.SolidLine))

        # 绘制 X 轴
        painter.drawLine(-40000, 0, 40000, 0)

        # 绘制 Y 轴
        painter.drawLine(0, -40000, 0, 40000)

        # 绘制箭头 (X 轴和 Y 轴的箭头)
        arrow_size = 10
        painter.drawLine(40000, 0, 39990, 10)
        painter.drawLine(40000, 0, 39990, -10)
        painter.drawLine(0, 40000, -10, 39990)
        painter.drawLine(0, 40000, 10, 39990)

        # 绘制坐标轴标签
        painter.setPen(QPen(QColor(0, 0, 0), 1, Qt.SolidLine))
        painter.drawText(40010, 10, "X")  # X 轴标签
        painter.drawText(10, 40010, "Y")  # Y 轴标签

class MapView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)  # 允许拖动地图
        self.setRenderHint(QPainter.SmoothPixmapTransform)  # 启用平滑缩放

    def wheelEvent(self, event):
        """
        鼠标滚轮事件来进行缩放
        """
        angle = event.angleDelta().y()
        # 调整所有图形项的大小
        rate = 0.9
        self.adjust_item_sizes(rate if angle > 0 else 1/rate)
        # 调用父类的缩放功能以调整视图
        if angle > 0:
            self.scale(1/rate, 1/rate)  # 放大视图
        else:
            self.scale(rate, rate)  # 缩小视图

    def adjust_item_sizes(self, scale_factor):
        """
        调整所有图形项的大小，确保它们在滚轮缩放时变大或变小。
        """
        for item in self.scene().items():
            if isinstance(item, QGraphicsEllipseItem):
                # 获取当前矩形尺寸并根据缩放因子调整
                rect = item.rect()
                rect.setHeight(rect.height()*scale_factor)
                rect.setWidth(rect.width()*scale_factor)
                item.setRect(rect)  # 设置新的大小
                pen = item.pen()
                pen.setWidth(int(pen.width()*scale_factor))
                item.setPen(pen)
                item.setBrush(QBrush(QColor(255, 0, 0)))
                continue
            if isinstance(item,QGraphicsRectItem):
                self.scene().removeItem(item)
            
class MapApp(QWidget):
    def __init__(self):
        super().__init__()

        # 启用拖放
        self.setAcceptDrops(True)

        # 创建场景
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-4000, -4000, 8000, 8000)  # 设置场景的大小
        # 创建视图
        self.view = MapView(self.scene)
        self.view.setSceneRect(-40000, -40000, 80000, 80000)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.combo1 = QComboBox(self)
        self.combo1.addItems(["请拖入地图文件"])
        self.combo1.currentIndexChanged.connect(lambda:self.update_map(self.combo1.currentText()))
        # 布局设置
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.combo1)
        self.setLayout(layout)

        # 绘制坐标轴
        grid_axes_item = GridAndAxesItem()
        self.scene.addItem(grid_axes_item)
        
        # 记录数据
        self.cur_area = ""
        self.points_to_xy = {}

    # 更新显示地图
    def update_map(self, area_name):
        points = []

        # 删除之前的点
        for item in self.scene.items():
            if isinstance(item,QGraphicsEllipseItem):
                self.scene.removeItem(item)

        self.scene.setSceneRect(-40000, -40000, 80000, 80000)  # 设置场景的大小
        for area in self.js["areas"]:
            if area["name"] !=area_name:
                continue
            print("areaname:",area["name"])
            advanced_points = area["logicalMap"]["advancedPoints"]
            for point in advanced_points:
                points.append((100*point["pos"]["x"],-100*point["pos"]["y"]))
            self.add_items_to_scene(points)
            self.cur_area = area_name
            break
        self.view.adjust_item_sizes(1/self.view.transform().m11())

    def dragEnterEvent(self, event: QDragEnterEvent):
        # 检查拖拽的内容类型是否为文件
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            # 获取文件路径
            file_path = urls[0].toLocalFile()
            # 获取文件后缀名
            if file_path.endswith('.scene'):
                event.accept()  # 接受拖拽事件
            else:
                event.ignore()  # 忽略非 .scene 文件的拖拽
        else:
            event.ignore()  # 如果不是文件，忽略事件

    def dropEvent(self, event):
        # 获取拖入的文件路径
        urls = event.mimeData().urls()
        if urls:
            self.load_file(urls[0].toLocalFile())

    # 加载文件
    def load_file(self, file_path):
        print(f"加载文件: {file_path}")
        self.file_path = file_path
        fid = open(self.file_path, encoding= 'UTF-8')
        self.js = js.load(fid)
        fid.close()
        self.combo1.clear()
        for area in self.js["areas"]:
            self.combo1.addItem(area["name"])
            advanced_points = area["logicalMap"]["advancedPoints"]
            for point in advanced_points:
                self.points_to_xy[int(point["instanceName"][2:])] = (100*point["pos"]["x"],-100*point["pos"]["y"])

    def add_items_to_scene(self, points,points_string = ""):
        """将多个坐标点添加到场景中"""
        for point in points:
            x, y = point
            # 创建一个椭圆形项来代表一个点
            width = 3
            ellipse_item = QGraphicsEllipseItem(x-width, y-width, width*2, width*2)
            ellipse_item.setBrush(QBrush(QColor(255, 0, 0)))
            self.scene.addItem(ellipse_item)
        """将需要绘制的线添加"""

        # 去除之前的线
        for item in self.scene.items():
            if isinstance(item,QGraphicsLineItem):
                self.scene.removeItem(item)

        #地图还未加载
        if len(self.points_to_xy) == 0:
            return
        if points_string !="":
            path_match = re.search(r'path:([^\s]+)', points_string)
            if path_match:
                path_str = path_match.group(1)  # 获取路径部分
                # 使用 "->" 将路径拆分为两个列表
                left_list = path_str.split('->')[:-1]  # 获取 '->' 左侧部分（不包括最后的元素）
                right_list = path_str.split('->')[1:]  # 获取 '->' 右侧部分（不包括最前面的元素）
            if len(left_list)==len(right_list):
                length = len(left_list)
                threshhold = 8
                color_factor = int(255/threshhold)
                for i in range(len(left_list)):
                    # 只显示最新规划的几段
                    if length -i > threshhold:
                        continue
                    
                    start = int(left_list[i].replace(",",""))
                    end = int(right_list[i].replace(",",""))
                    line_pen = QPen(QColor(255, color_factor*(length -i), color_factor*(length-i)))
                    line_pen.setWidth(8)
                    try:
                        line_item = QGraphicsLineItem(self.points_to_xy[start][0], self.points_to_xy[start][1], self.points_to_xy[end][0], self.points_to_xy[end][1])  # 起点(0,0) 到 终点(100,100)
                    except:
                        print("no such line")
                    line_item.setPen(line_pen)
                    self.scene.addItem(line_item)
                    # if i == length-1:
                    #     x = self.points_to_xy[end][0]
                    #     y = self.points_to_xy[end][1]
                    #     width = 5
                    #     ellipse_item = QGraphicsEllipseItem(x-width, y-width, width*2, width*2)
                    #     ellipse_item.setBrush(QBrush(QColor(255, 0, 0)))
                    #     self.scene.addItem(ellipse_item)

class LogAnalyzer(QWidget):
    def __init__(self):
        super().__init__()

        # 初始化UI
        self.setWindowTitle("日志分析器")
        self.setGeometry(100, 100, 300, 200)

        # 启用拖放
        self.setAcceptDrops(True)

        # 创建主布局
        self.layout = QVBoxLayout()
        
        # 初始化三个下拉框
        self.combo1 = QComboBox(self)
        self.combo2 = QComboBox(self)
        self.combo3 = QComboBox(self)

        # 给下拉框添加默认选项
        self.combo1.addItems(["请拖入RHCR文件"])
        self.combo2.addItems(["请选择Start时间"])
        self.combo3.addItems(["请选择Order时间"])

        # 添加标签来显示拖动条的值
        self.value_label = QLabel("拖动条值: 0", self)

        # 初始化拖动条
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)  # 默认值

        # 连接信号
        self.combo1.currentIndexChanged.connect(lambda:self.update_combo2(self.combo1.currentText()))
        self.combo2.currentIndexChanged.connect(lambda:self.update_combo3(self.combo2.currentText()))
        self.combo3.currentIndexChanged.connect(lambda:self.update_slider_range(self.combo3.currentText()))
        self.slider.valueChanged.connect(self.update_label)

        # 布局管理
        self.layout.addWidget(self.combo1)
        self.layout.addWidget(self.combo2)
        self.layout.addWidget(self.combo3)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.value_label)

        # 设置主窗口的布局
        self.setLayout(self.layout)

        # 记录当前日志路径
        self.file_path = ""
        self.starts = []
        self.orders = []
        self.planns = []
        self.paths = []
        self.lines = []

    def update_slider_range(self,currentItem):
        if currentItem == "":
            return
        lines = self.lines
        for i in self.planns:
            if i[0] == currentItem:
                start_p = i[1]
        self.paths = []
        for index,line in enumerate(lines):
            if index<=start_p:
                continue
            if " path:" in line:
                line = line.strip()
                self.paths.append((line,index))
            if "planning: " in line :
                break

        self.slider.setRange(0,len(self.paths)-1)

    def update_label(self):
        # 更新标签显示拖动条当前值
        if len(self.paths)==0:
            self.value_label.setText("please push in logs.")
            return
        self.value_label.setText(self.paths[self.slider.value()][0])

    def dragEnterEvent(self, event: QDragEnterEvent):
        # 检查拖拽的内容类型是否为文件
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            # 获取文件路径
            file_path = urls[0].toLocalFile()
            # 获取文件后缀名
            if file_path.endswith('.log'):
                event.accept()  # 接受拖拽事件
            else:
                event.ignore()  # 忽略非 .txt 文件的拖拽
        else:
            event.ignore()  # 如果不是文件，忽略事件

    def dropEvent(self, event):
        # 获取拖入的文件路径
        urls = event.mimeData().urls()
        if urls:
            self.load_file(urls[0].toLocalFile())

    def load_file(self, file_path):
        # 在这里实现文件加载的逻辑
        # 假设文件是文本文件，我们从中读取内容并更新下拉框
        print(f"加载文件: {file_path}")
        self.file_path = file_path

        # 模拟从文件加载新项
        new_items = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.lines = file.readlines()
                for index,line in enumerate(self.lines):
                    if "RHCR START!" in line:
                        line = line.strip()
                        new_items.append(line)
                        self.starts.append((line,index))

        except Exception as e:
            print(f"读取文件时出错: {e}")
            new_items = ["错误加载文件"]

        # 更新下拉框内容
        self.combo1.clear()
        self.combo1.addItems(new_items)

    def update_combo2(self,currentItem):
        if currentItem == "":
            return
        new_items = []
        lines = self.lines
        for i in self.starts:
            if i[0] == currentItem:
                start_p = i[1]
        self.orders = []
        for index,line in enumerate(lines):
            if index<=start_p:
                continue
            if "order info(" in line:
                line = line.strip()
                new_items.append(line)
                self.orders.append((line,index))
            if "RHCR START!" in line:
                break


        self.combo2.clear()
        self.combo2.addItems(new_items)

    def update_combo3(self,currentItem):
        if currentItem == "":
            return
        new_items = []
        lines = self.lines
        for i in self.orders:
            if i[0] == currentItem:
                start_p = i[1]
        self.planns = []
        for index,line in enumerate(lines):
            if index<=start_p:
                continue
            if "planning: " in line:
                line = line.strip()
                new_items.append(line)
                self.planns.append((line,index))
            if "order info(" in line :
                break

        self.combo3.clear()
        self.combo3.addItems(new_items)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建 MapApp 和 LogAnalyzer 实例
        map_widget = MapApp()
        log_analyzer = LogAnalyzer()

        log_analyzer.slider.valueChanged.connect(lambda:map_widget.add_items_to_scene([],log_analyzer.paths[log_analyzer.slider.value()][0]))
        # 创建垂直布局来显示两个部件
        layout = QVBoxLayout()

        # 创建一个 QWidget 来容纳布局
        central_widget = QWidget()
        central_widget.setLayout(layout)

        # 将地图和日志分析器部件添加到水平布局中
        layout.addWidget(map_widget, 4)
        layout.addWidget(log_analyzer, 1)

        # 设置中心部件
        self.setCentralWidget(central_widget)

        self.setWindowTitle("地图和日志分析器")
        self.setGeometry(100, 100, 1200, 800)
 
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建并显示主窗口
    window = MainWindow()

    sys.exit(app.exec_())