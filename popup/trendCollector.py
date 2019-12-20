# _*_ coding:utf-8 _*_
# __Author__： zizle
import re
import json
import xlrd
import datetime
import requests
from xlrd import xldate_as_tuple
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QDialog, QTreeWidget, QWidget, QGridLayout, QLabel, QLineEdit,\
    QPushButton, QComboBox, QTableWidget, QTreeWidgetItem, QFileDialog, QHeaderView, QTableWidgetItem
from PyQt5.QtCore import Qt, QPoint
import settings
from widgets.base import TableRowDeleteButton
from popup.tips import WarningPopup


# 新建数据表
class CreateNewTrendTablePopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(CreateNewTrendTablePopup, self).__init__(*args, **kwargs)
        # 绑定当前显示的页面(0, 上传数据表)、(1, 新增数据组别)
        self.current_option = 0
        # 左侧类别树
        self.variety_tree = QTreeWidget(clicked=self.variety_tree_clicked)
        # 上传表格数据控件
        self.udwidget = QWidget()  # upload data widget
        # 右侧上传数据控件布局
        udwlayout = QGridLayout(margin=0)
        udwlayout.addWidget(QLabel('所属品种:'), 0, 0)
        udwlayout.addWidget(QLabel(parent=self, objectName='VarietyError'), 1, 0, 1, 2)
        self.attach_variety = QLabel(objectName='AttachVariety')
        self.attach_variety.vid = None
        udwlayout.addWidget(self.attach_variety, 0, 1)
        udwlayout.addWidget(QLabel('所属组别:'), 2, 0)
        udwlayout.addWidget(QLabel(parent=self, objectName='groupError'), 3, 0, 1, 2)
        self.attach_group = QLabel(objectName='AttachGroup')
        self.attach_group.gid = None
        udwlayout.addWidget(self.attach_group, 2, 1)
        udwlayout.addWidget(QLabel('数据名称:'), 4, 0)
        udwlayout.addWidget(QLabel(parent=self, objectName='tbnameError'), 5, 0, 1, 2)
        self.tnedit = QLineEdit()  # table name edit数据组名称编辑
        self.tnedit.textChanged.connect(self.tbname_changed)
        udwlayout.addWidget(self.tnedit, 4, 1)
        udwlayout.addWidget(QLabel('时间类型:'), 6, 0)
        self.date_type = QComboBox(parent=self, objectName='dateTypeCombo')
        self.date_type.currentTextChanged.connect(self.change_date_type)
        udwlayout.addWidget(self.date_type, 6, 1)
        udwlayout.addWidget(QPushButton('导入', objectName='selectTable', clicked=self.select_data_table), 7, 0)
        udwlayout.addWidget(QLabel(parent=self, objectName='commitError'), 7, 1)
        self.review_table = QTableWidget(objectName='reviewTable')
        # self.review_table.verticalHeader().hide()
        udwlayout.addWidget(self.review_table, 8, 0, 1, 2)
        # 上传添加数据表按钮布局
        addlayout = QHBoxLayout()
        self.add_table_btn = QPushButton('确认添加', parent=self, objectName='addTable', clicked=self.add_new_table)
        addlayout.addWidget(self.add_table_btn, alignment=Qt.AlignRight)
        self.udwidget.setLayout(udwlayout)
        # 布局
        layout = QHBoxLayout()  # 总的左右布局
        llayout = QVBoxLayout()  # 左侧上下布局
        rlayout = QVBoxLayout()  # 右侧上下布局
        llayout.addWidget(self.variety_tree, alignment=Qt.AlignLeft)
        llayout.addWidget(QPushButton('新建组别', clicked=self.create_table_group), alignment=Qt.AlignLeft)
        rlayout.addWidget(self.udwidget)
        rlayout.addLayout(addlayout)
        layout.addLayout(llayout)
        layout.addLayout(rlayout)
        self.setLayout(layout)
        # 样式
        self.setWindowTitle('新建数据')
        self.setFixedSize(1000, 550)
        self.variety_tree.header().hide()
        self.setObjectName('myself')
        self.setStyleSheet("""
        #AttachVariety, #AttachGroup, #tgpopAttachTo{
            color:rgb(180,20,30)
        }
        #ngWidget{
            background-color: rgb(245,245,245);
            border-radius: 3px;
        }
        #addTable {
            max-width: 55px;
        }
        #selectTable{
            max-width: 55px;
        }
        #closeBtn, #addGroupBtn{
            max-width: 55px
        }
        #tgpopupVError,#tgpopupNError,#tbnameError,#groupError{
            color:rgb(200,10,20)
        }
        """)
        # 初始化
        self.get_date_type()

    # 数据时间类型选择
    def get_date_type(self):
        date_type = [
            {'name': '年度（年）', 'fmt': '%Y'},
            {'name': '月度（年-月）', 'fmt': '%Y-%m'},
            {'name': '日度（年-月-日）', 'fmt': '%Y-%m-%d'},
            {'name': '时度（年-月-日 时）', 'fmt': '%Y-%m-%d %H'},
            {'name': '分度（年-月-日 时:分）', 'fmt': '%Y-%m-%d %H:%M'},
            {'name': '秒度（年-月-日 时:分:秒）', 'fmt': '%Y-%m-%d %H:%M:%S'},
        ]
        for t in date_type:
            self.date_type.addItem(t['name'], t['fmt'])
        self.date_type.setCurrentIndex(self.date_type.count() - 1)

    # 该变时间类型
    def change_date_type(self, t):
        fmt = self.date_type.currentData()
        row_count = self.review_table.rowCount()
        for row in range(row_count):
            item = self.review_table.item(row, 0)
            if hasattr(item, 'date'):  # date属性是在填充表格时绑定，详见self._show_file_data函数
                text = item.date.strftime(fmt)
                item.setText(text)

    # 获取品种树内容
    def getVarietyTableGroups(self):
        self.variety_tree.clear()
        try:
            r = requests.get(
                url=settings.SERVER_ADDR + 'trend/varieties/group/?mc=' + settings.app_dawn.value('machine'),
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 200:
                raise ValueError(response['message'])
        except Exception:
            return
        for index, variety_item in enumerate(response['data']):
            print(index, variety_item)
            variety = QTreeWidgetItem(self.variety_tree)
            variety.setText(0, variety_item['name'])
            variety.vid = variety_item['id']
            for group_item in variety_item['trend_table_groups']:
                group = QTreeWidgetItem(variety)
                group.setText(0, group_item['name'])
                group.gid = group_item['id']
        # # 目录树填充完毕手动设置当前第一个，并触发点击事件
        # self.variety_tree.setCurrentIndex(self.variety_tree.model().index(0, 0))  # 最顶层设置为当前
        # self.variety_tree_clicked()  # 手动调用点击事件

    # 新增数据表的组别
    def create_table_group(self):
        # 获取当前选择的品种
        variety = self.attach_variety.text()
        table_group_popup = QDialog(parent=self)
        table_group_popup.attach_variety_id = self.attach_variety.vid
        def commit_table_group():
            if not table_group_popup.attach_variety_id:  # 所属品种
                table_group_popup.findChild(QLabel, 'tgpopAttachTo').setText('请选择品种后再添加!')
                return
            group_name = re.sub(r'\s+', '', table_group_popup.group_name_edit.text())
            if not group_name:
                table_group_popup.findChild(QLabel, 'tgpopupNError').setText('请输入数据组名称！')
                return
            # 提交
            try:
                r = requests.post(
                    url=settings.SERVER_ADDR + 'trend/' + str(table_group_popup.attach_variety_id) + '/group-tables/?mc=' + settings.app_dawn.value('machine'),
                    headers={'AUTHORIZATION': settings.app_dawn.value('AUTHORIZATION')},
                    data=json.dumps({'group_name': group_name})
                )
                response = json.loads(r.content.decode('utf-8'))
                if r.status_code != 201:
                    raise ValueError(response['message'])
            except Exception as e:
                table_group_popup.findChild(QLabel, 'tgpopupNError').setText(str(e))
            else:
                table_group_popup.close()
        playout = QGridLayout()  # table group popup layout
        playout.addWidget(QLabel('所属品种：'), 0, 0)
        playout.addWidget(QLabel(variety, parent=table_group_popup, objectName='tgpopAttachTo'), 0, 1)
        playout.addWidget(QLabel(parent=table_group_popup, objectName='tgpopupVError'), 1, 0, 1, 2)  # variety error
        playout.addWidget(QLabel('数据组名：'), 2, 0)
        table_group_popup.group_name_edit = QLineEdit(parent=table_group_popup, objectName='ngEdit')
        playout.addWidget(table_group_popup.group_name_edit, 2, 1)
        playout.addWidget(QLabel(parent=table_group_popup, objectName='tgpopupNError'), 3, 0, 1, 2)  # name error
        abtlayout = QHBoxLayout()
        abtlayout.addWidget(QPushButton('增加', objectName='addGroupBtn', clicked=commit_table_group),
                            alignment=Qt.AlignRight)
        playout.addLayout(abtlayout, 4, 1)
        table_group_popup.setLayout(playout)
        table_group_popup.setFixedSize(400, 150)
        table_group_popup.setWindowTitle('增加数据组')
        if not table_group_popup.exec_():
            table_group_popup.deleteLater()
            self.getVarietyTableGroups() # 重新请求当前左侧列表数据
            del table_group_popup

    # 新建表的表名称编辑框文字改变
    def tbname_changed(self, t):
        el = self.findChild(QLabel, 'tbnameError')
        el.setText('')

    # 选择数据表文件
    def select_data_table(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '打开文件', '', "Excel files(*.xls *.xlsx)")
        if not file_path:
            return
        # 处理文件名称填入表名称框
        file_name_ext = file_path.rsplit('/', 1)[1]
        file_name = file_name_ext.rsplit('.', 1)[0]
        tbname = re.sub(r'\s+', '', file_name)
        self.tnedit.setText(tbname)
        # 读取文件内容预览
        self._show_file_data(file_path)

    # 读取文件内容填入预览表格
    def _show_file_data(self, file_path):
        # 处理Excel数据写入表格预览
        rf = xlrd.open_workbook(filename=file_path)
        sheet1 = rf.sheet_by_index(0)
        labels = sheet1.row_values(0)
        # xlrd读取的类型ctype： 0 empty,1 string, 2 number, 3 date, 4 boolean, 5 error
        nrows = sheet1.nrows
        ncols = sheet1.ncols
        self.review_table.clear()
        self.review_table.setRowCount(nrows - 1)
        self.review_table.setColumnCount(ncols)
        self.review_table.setHorizontalHeaderLabels([str(i) for i in labels])
        self.review_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 时间类型约束
        date_type = self.date_type.currentData()
        # 数据填入预览表格
        for row in range(1, nrows):
            row_content = []
            for col in range(ncols):
                ctype = sheet1.cell(row, col).ctype
                cell = sheet1.cell_value(row, col)
                if ctype == 2 and cell % 1 == 0:  # 如果是整形
                    cell = int(cell)
                    item = QTableWidgetItem(str(cell))
                elif ctype == 3:
                    # 转成datetime对象
                    date = datetime.datetime(*xldate_as_tuple(cell, 0))
                    cell = date.strftime(date_type)
                    # 填入预览表格cell就是每个数据
                    item = QTableWidgetItem(str(cell))
                    item.date = date
                else:
                    item = QTableWidgetItem(str(cell))
                item.setTextAlignment(Qt.AlignCenter)
                self.review_table.setItem(row - 1, col, item)
                row_content.append(cell)

    # 读取预览表格的数据
    def _read_review_data(self):
        row_count = self.review_table.rowCount()
        column_count = self.review_table.columnCount()
        data_dict = dict()
        data_dict['value_list'] = list()
        data_dict['header_labels'] = list()
        for row in range(row_count):
            row_content = list()
            for col in range(column_count):
                if row == 0:  # 获取表头内容
                    data_dict['header_labels'].append(self.review_table.horizontalHeaderItem(col).text())
                item = self.review_table.item(row, col)
                row_content.append(item.text())
            data_dict['value_list'].append(row_content)
        # 添加第一行表头数据
        data_dict['value_list'].insert(0, data_dict['header_labels'])
        return data_dict

    # 新增数据表
    def add_new_table(self):
        self.add_table_btn.setEnabled(False)
        # vid = self.attach_variety.vid
        gid = self.attach_group.gid
        if not gid:
            el = self.findChild(QLabel, 'groupError')
            el.setText('请选择数据所属组.如需新建组,请点击左下角【新建组别】.')
            self.add_table_btn.setEnabled(True)
            return
        # 表名称与正则替换空格
        tbname = re.sub(r'\s+', '', self.tnedit.text())
        if not tbname:
            el = self.findChild(QLabel, 'tbnameError')
            el.setText('请输入数据表名称.')
            self.add_table_btn.setEnabled(True)
            return
        # 读取预览表格的数据
        table_data = self._read_review_data()
        if not table_data['value_list']:
            el = self.findChild(QLabel, 'commitError')
            el.setText('请先导入数据再上传.')
            self.add_table_btn.setEnabled(True)
            return
        # 数据上传
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'trend/group/' + str(gid) + '/table/?mc=' + settings.app_dawn.value('machine'),
                headers={'AUTHORIZATION': settings.app_dawn.value('AUTHORIZATION')},
                data=json.dumps({
                    "table_name": tbname,
                    "table_data": table_data
                }),
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            self.findChild(QLabel, 'commitError').setText(str(e))
            self.add_table_btn.setEnabled(True)
            return
        self.close()

    # 点击品种树
    def variety_tree_clicked(self):
        item = self.variety_tree.currentItem()
        if item.childCount():  # has children open the root
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)
        text = item.text(0)
        if item.parent():
            if self.current_option == 0:
                # 改变数据所属（品种的id是'vid', 组的id是gid。详情见'self.get_varieties'函数）
                self.attach_variety.vid = item.parent().vid
                self.attach_group.gid = item.gid
                self.attach_variety.setText(item.parent().text(0))
                self.attach_group.setText(text)
                # 提示消息清除
                el = self.findChild(QLabel, 'groupError')
                el.setText('')

            else:
                # 只能在品种下创建数据组别
                el = self.ng_widget.findChild(QLabel, 'errorLabel')
                el.setText('只能在品种下创建数据组别')
                addBtn = self.ng_widget.findChild(QPushButton, 'addGroupBtn')
                addBtn.setEnabled(False)
        else:
            if self.current_option == 0:
                # 该表所属品种(只有显示提示作用)
                self.attach_variety.setText(text)
                self.attach_variety.vid = item.vid
                # 清除所属组别和提示消息
                self.attach_group.setText('')
                self.attach_group.gid = None
                el = self.findChild(QLabel, 'groupError')
                el.setText('')
            else:
                # 显示所属品种
                self.ng_widget.attach_variety = item.vid
                ngwAttachTo = self.ng_widget.findChild(QLabel, 'ngwAttachTo')
                ngwAttachTo.setText(text)
                error_label = self.ng_widget.findChild(QLabel, 'errorLabel')
                error_label.setText('')
                addBtn = self.ng_widget.findChild(QPushButton, 'addGroupBtn')
                addBtn.setEnabled(True)
                
                
# 显示当前数据表
class ShowTableDetailPopup(QDialog):
    def __init__(self, *args, **kwargs):
        super(ShowTableDetailPopup, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.setMinimumSize(820, 450)
        self.setLayout(layout)

    # 显示数据
    def showTableData(self, headers, table_contents):
        # 设置行列
        self.table.setRowCount(len(table_contents))
        headers.pop(0)
        col_count = len(headers)
        self.table.setColumnCount(col_count)
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        for row, row_content in enumerate(table_contents):
            for col in range(1, col_count + 1):
                item = QTableWidgetItem(row_content[col])
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col-1, item)


# 编辑当前数据表
class EditTableDetailPopup(QDialog):
    def __init__(self, table_id, *args, **kwargs):
        super(EditTableDetailPopup, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(margin=0)
        self.table_id = table_id
        # 操作按钮布局
        operate_button_layout = QHBoxLayout()
        self.add_rows_button = QPushButton('粘贴新数据', clicked=self.copy_new_rows)  # 添加数据
        operate_button_layout.addWidget(self.add_rows_button)
        # 删除选中行
        self.delete_current_button = QPushButton('删除选中行', clicked=self.delete_current_row)
        operate_button_layout.addWidget(self.delete_current_button)
        self.delete_current_button.hide()
        # 新增一行
        self.add_new_row_button = QPushButton('新增一行', clicked=self.new_table_add_row)
        operate_button_layout.addWidget(self.add_new_row_button)
        self.add_new_row_button.hide()
        operate_button_layout.addStretch()
        # 删除这张表
        self.delete_table = QPushButton('删除整张表', styleSheet='color:rgb(240,20,50); border:none',
                                        cursor=Qt.PointingHandCursor, clicked=self.delete_this_table)
        operate_button_layout.addWidget(self.delete_table, alignment=Qt.AlignRight)
        layout.addLayout(operate_button_layout)
        self.table = QTableWidget()
        layout.addWidget(self.table)
        # 新数据的表格
        self.new_table = QTableWidget()
        self.new_table_headers = []
        self.new_table.hide()
        layout.addWidget(self.new_table)
        # 确认增加新数据
        self.commit_new_button = QPushButton('确认增加', clicked=self.commit_new_table_rows)
        self.commit_new_button.hide()
        layout.addWidget(self.commit_new_button, alignment=Qt.AlignRight)
        # 错误提示
        self.network_result_label = QLabel()
        layout.addWidget(self.network_result_label, alignment=Qt.AlignLeft)
        self.setMinimumSize(820, 450)
        self.setLayout(layout)

    # 黏贴新数据
    def copy_new_rows(self):
        self.table.hide()
        self.new_table.show()
        self.commit_new_button.show()
        self.delete_current_button.show()
        self.add_new_row_button.show()
        # 获取当前剪贴板的内容
        clipboard = QApplication.clipboard()
        # 处理数据
        contents = re.split(r'\n', clipboard.text())
        # 在新表格中添加数据
        new_row_count = len(self.new_table_headers)
        self.new_table.setRowCount(len(contents))
        self.new_table.setColumnCount(new_row_count)
        self.new_table.setHorizontalHeaderLabels(self.new_table_headers)
        self.new_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        for row, row_content in enumerate(contents):
            row_content = re.split(r'\t', row_content)
            if not row_content[0]:
                continue
            for col, item_text in enumerate(row_content):
                if col > new_row_count - 1:
                    continue
                new_item = QTableWidgetItem(item_text)
                new_item.setTextAlignment(Qt.AlignCenter)
                self.new_table.setItem(row, col, new_item)

    # 删除选中行（追加数据时）
    def delete_current_row(self):
        self.new_table.removeRow(self.new_table.currentRow())

    # 新增一行(追加数据时)
    def new_table_add_row(self):
        self.new_table.insertRow(self.new_table.rowCount())

    # 确认新增新数据
    def commit_new_table_rows(self):
        self.commit_new_button.setEnabled(False)
        self.network_result_label.setText('上传中...')
        # 读取表格中的数
        row_count = self.new_table.rowCount()
        column_count = self.new_table.columnCount()
        data_dict = dict()
        data_dict['value_list'] = list()
        # data_dict['header_labels'] = list()
        for row in range(row_count):
            if not self.new_table.item(row, 0):
                continue
            row_content = list()
            for col in range(column_count):
                # if row == 0:  # 获取表头内容
                #     data_dict['header_labels'].append(self.review_table.horizontalHeaderItem(col).text())
                item = self.new_table.item(row, col)
                row_content.append(item.text() if item else '')
            data_dict['value_list'].append(row_content)
        # # 添加第一行表头数据
        # data_dict['value_list'].insert(0, data_dict['header_labels'])
        # 上传新数据至当前表
        try:
            r = requests.post(
                url=settings.SERVER_ADDR + 'trend/table/' + str(self.table_id) + '/?look=1&mc=' + settings.app_dawn.value('machine'),
                headers={'AUTHORIZATION': settings.app_dawn.value('AUTHORIZATION')},
                data=json.dumps(data_dict)
            )
            response = json.loads(r.content.decode('utf-8'))
            if r.status_code != 201:
                raise ValueError(response['message'])
        except Exception as e:
            self.network_result_label.setText(str(e))
            self.commit_new_button.setEnabled(True)
        else:
            self.network_result_label.setText(response['message'])

    # 显示数据
    def showTableData(self, headers, table_contents):
        # 设置行列
        self.table.setRowCount(len(table_contents))
        headers.pop(0)
        self.new_table_headers = headers
        col_count = len(headers) + 1
        self.table.setColumnCount(col_count)
        self.table.setHorizontalHeaderLabels(headers + [''])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        for row, row_content in enumerate(table_contents):
            for col, col_text in enumerate(row_content):
                if col == 0:
                    continue
                item = QTableWidgetItem(row_content[col])
                item.setTextAlignment(Qt.AlignCenter)
                if col == 1:
                    item.col_id = row_content[0]
                self.table.setItem(row, col - 1, item)
                # 添加删除按钮
                if col == len(row_content) - 1:
                    delete_button = TableRowDeleteButton('删除')
                    delete_button.button_clicked.connect(self.delete_button_clicked)
                    self.table.setCellWidget(row, col, delete_button)

    # 删除一行数据
    def delete_button_clicked(self, delete_button):
        try:
            current_row, _ = self.get_widget_index(delete_button)
            row_id = self.table.item(current_row, 0).col_id
            def delete_row_content():
                try:
                    r = requests.delete(
                        url=settings.SERVER_ADDR + 'trend/table/' + str(
                            self.table_id) + '/?mc=' + settings.app_dawn.value('machine'),
                        headers={'AUTHORIZATION': settings.app_dawn.value('AUTHORIZATION')},
                        data=json.dumps({'row_id': row_id})
                    )
                    response = json.loads(r.content.decode('utf-8'))
                    if r.status_code != 200:
                        raise ValueError(response['message'])
                except Exception as e:
                    self.network_result_label.setText(str(e))
                else:
                    # 表格移除当前行
                    self.table.removeRow(current_row)
                    popup.close()
                    self.network_result_label.setText(response['message'])
            # 警示框
            popup = WarningPopup(parent=self)
            popup.confirm_button.connect(delete_row_content)
            if not popup.exec_():
                popup.deleteLater()
                del popup
        except Exception as e:
            print(e)

    # 删除整张表
    def delete_this_table(self):
        def delete_table():
            try:
                r = requests.delete(
                    url=settings.SERVER_ADDR + 'trend/table/' + str(
                        self.table_id) + '/?mc=' + settings.app_dawn.value('machine'),
                    headers={'AUTHORIZATION': settings.app_dawn.value('AUTHORIZATION')},
                    data=json.dumps({'operate': 'all'})
                )
                response = json.loads(r.content.decode('utf-8'))
                if r.status_code != 200:
                    raise ValueError(response['message'])
            except Exception as e:
                self.network_result_label.setText(str(e))
            else:
                popup.close()
                self.close()
        # 警示框
        popup = WarningPopup(parent=self)
        popup.confirm_button.connect(delete_table)
        if not popup.exec_():
            popup.deleteLater()
            del popup

    # 获取控件所在行和列
    def get_widget_index(self, widget):
        index = self.table.indexAt(QPoint(widget.frameGeometry().x(), widget.frameGeometry().y()))
        return index.row(), index.column()





