# _*_ coding:utf-8 _*_
"""
product service frame
Create: 2019-08-07
Author: zizle
"""
import sys
import json
import requests
from lxml import etree
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QScrollArea, QTextBrowser, QLabel, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

import config
from thread.request import RequestThread
from widgets.base import Loading, FileShowTable


class MarketAnalysis(QWidget):
    def __init__(self, *args, **kwargs):
        super(MarketAnalysis, self).__init__(*args, **kwargs)
        layout = QVBoxLayout()
        self.loading = Loading()
        self.table = FileShowTable()
        layout.addWidget(self.loading)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.get_contents()

    def get_contents(self):
        self.loading.show()
        data = [
            {'id':1, 'name': '市场分析1', 'create_time':'2019-08-07 13:12:47', 'to_look': '唯一请求字段1'},
            {'id':2, 'name': '市场分析2', 'create_time':'2019-08-07 13:13:47', 'to_look': '唯一请求字段2'},
            {'id':3, 'name': '市场分析3', 'create_time':'2019-08-07 13:14:47', 'to_look': '唯一请求字段3'},
            {'id':4, 'name': '市场分析4', 'create_time':'2019-08-07 13:15:47', 'to_look': '唯一请求字段4'},
            {'id':5, 'name': '市场分析5', 'create_time':'2019-08-07 13:16:47', 'to_look': '唯一请求字段5'},
        ]
        keys=[('id','序号'),('name', '标题'), ('create_time', '创建时间'), ('to_look', '')]
        self.table.show_content(content=data, keys=keys)
        self.loading.hide()


class MsgCommunication(QScrollArea):
    def __init__(self, *args, **kwargs):
        super(MsgCommunication, self).__init__(*args, **kwargs)
        self.setWidgetResizable(True)
        self.container = QWidget()
        layout = QVBoxLayout()
        # show data loading
        self.loading = Loading()
        self.loading.clicked.connect(self.get_message_communication)
        loading_layout = QVBoxLayout(self)
        loading_layout.addWidget(self.loading)
        self.container.setLayout(layout)
        self.setStyleSheet("""
        QTextBrowser{
            border: none;
            border-bottom: 1px solid rgb(200,200,200)
        }
        QTextBrowser:hover{
            background:rgb(220,220,220);   
        }
        """)
        self.get_message_communication()


    def get_message_communication(self):
        self.loading.show()
        self.msg_thread = RequestThread(
            url=config.SERVER_ADDR + 'pservice/consult/msg/',
            method='get',
            data=json.dumps({'machine_code': config.app_dawn.value('machine')}),
            cookies=config.app_dawn.value('cookies')
        )
        self.msg_thread.response_signal.connect(self.msg_thread_back)
        self.msg_thread.finished.connect(self.msg_thread.deleteLater)
        self.msg_thread.start()

    def msg_thread_back(self, content):
        print('frame.pservice.py {} 短信通数据: '.format(sys._getframe().f_lineno), content)
        if content['error']:
            self.loading.retry()
            return
        if not content['data']:
            self.loading.no_data()
            return
        self.loading.hide()
        # show content
        for item in content['data']:
            content = "<h2 style='display:inline-block'>" + item['title'] + "</h2>" + \
                              "<span style='display:inline-block'>" + item['create_time'] + "</span>" + \
                          item['content']
            text_browser = QTextBrowser()
            text_browser.setText(content)
            text_browser.setMinimumHeight(text_browser.document().lineCount() * 30)
            self.container.layout().addWidget(text_browser)

        self.setWidget(self.container)


class PersonTrain(QScrollArea):
    def __init__(self):
        super(PersonTrain, self).__init__()
        self.setWidgetResizable(True)
        layout = QVBoxLayout(spacing=0)
        self.loading = Loading()
        layout.addWidget(self.loading)
        self.window = QWidget()
        self.window.setLayout(layout)
        self.show_content()
        self.setWidget(self.window)
        self.setStyleSheet("""
        QTextBrowser{
            border:none;
            line-height:30px;
        }
        QLabel{
            background-color:rgb(255,255,255);
            font-size:20px;
            font-weight:bold;
        }
        """)

    def show_content(self):
        # get article from server
        self.loading.show()
        try:
            response = requests.get(
                url=config.SERVER_ADDR + 'pservice/adviser/pst/',
                data=json.dumps({'machine_code': config.app_dawn.value('machine')}),
                cookies=config.app_dawn.value('cookies')
            )
        except Exception as error:
            QMessageBox(self, '错误', '请求数据失败.{}'.format(error), QMessageBox.Yes)
            self.loading.hide()
            return
        response_data = json.loads(response.content.decode('utf-8'))
        article = response_data['data']
        html = etree.HTML(article['content'])
        all_element = html.xpath('//*')
        text = ''
        title = QLabel(article['title'])
        title.setAlignment(Qt.AlignCenter)
        self.window.layout().addWidget(title)
        for element in all_element:
            if element.tag == 'p':
                # print('p标签', element.xpath('string()'))
                # 整理要显示文本
                text += '<p style=text-indent:30px;font-size:15px;line-height:20px>' + element.xpath('string()') + '</p>'
            elif element.tag == 'image':
                # 重置已显示文本,  添加图片
                # print('image标签', element)
                text_browser = QTextBrowser()
                text_browser.setText(text)
                text_browser.setMaximumHeight(50*text_browser.document().lineCount())
                self.window.layout().addWidget(text_browser)
                text = ''
                # 处理图片
                src = config.SERVER_ADDR + element.xpath('@src')[0]
                pixmap = QPixmap()
                img_label = QLabel()
                response = requests.get(src).content
                pixmap.loadFromData(response)
                img_label.setPixmap(pixmap)
                self.window.layout().addWidget(img_label)
            else:
                continue
        if text:
            # 还有文本，还需显示
            text_browser = QTextBrowser()
            text_browser.setText(text)
            text_browser.setMaximumHeight(50 * text_browser.document().lineCount())
            self.window.layout().addWidget(text_browser)
            text = ''
        self.window.layout().addStretch()
        self.loading.hide()

