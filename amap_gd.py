import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTableWidget, QTableWidgetItem, QHeaderView, 
                            QMessageBox, QComboBox, QFileDialog)
from PyQt5.QtCore import Qt
import requests
import csv
from datetime import datetime, date
import time

class AmapSearchGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = "you_api_key"
        # 添加缓存字典
        self.city_cache = {}  # 用于缓存城市数据
        self.district_cache = {}  # 用于缓存区域数据
        # 添加API调用计数器
        self.daily_query_count = 0
        self.last_query_time = time.time()
        self.query_date = date.today()
        
        # 初始化省份列表
        self.provinces = [
            "北京市", "天津市", "河北省", "山西省", "内蒙古自治区",
            "辽宁省", "吉林省", "黑龙江省", "上海市", "江苏省",
            "浙江省", "安徽省", "福建省", "江西省", "山东省",
            "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区",
            "海南", "重庆市", "四川省", "贵州省", "云南省",
            "西藏自治区", "陕西省", "甘肃省", "青海省", "宁夏回族自治区",
            "新疆维吾尔自治区"
        ]
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('POI查询')
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 搜索区域
        search_layout = QHBoxLayout()
        
        # 关键词输入
        keyword_label = QLabel('关键词:')
        self.keyword_input = QLineEdit()
        self.keyword_input.setFixedWidth(150)
        self.keyword_input.setPlaceholderText('输入关键词')
        search_layout.addWidget(keyword_label)
        search_layout.addWidget(self.keyword_input)
        
        # 省份选择
        province_label = QLabel('省份:')
        self.province_combo = QComboBox()
        self.province_combo.addItems(self.provinces)
        self.province_combo.setFixedWidth(150)
        self.province_combo.currentTextChanged.connect(self.update_cities)
        
        # 城市选择
        city_label = QLabel('城市:')
        self.city_combo = QComboBox()
        self.city_combo.setFixedWidth(150)
        self.city_combo.currentTextChanged.connect(self.update_districts)
        
        # 区域选择
        district_label = QLabel('区域:')
        self.district_combo = QComboBox()
        self.district_combo.setFixedWidth(150)
        
        search_layout.addWidget(province_label)
        search_layout.addWidget(self.province_combo)
        search_layout.addWidget(city_label)
        search_layout.addWidget(self.city_combo)
        search_layout.addWidget(district_label)
        search_layout.addWidget(self.district_combo)
        
        # 搜索按钮
        search_btn = QPushButton('搜索')
        search_btn.clicked.connect(self.search)
        search_layout.addWidget(search_btn)
        
        # 导出按钮
        export_btn = QPushButton('导出结果')
        export_btn.clicked.connect(self.export_results)
        search_layout.addWidget(export_btn)
        
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(8)
        self.result_table.setHorizontalHeaderLabels(['名称', '地址', '类型', '电话', '评分', '评价数', '经度', '纬度'])
        
        # 设置表格列宽可调整
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # 名称列
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # 地址列
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # 类型列
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # 电话列
        header.setSectionResizeMode(4, QHeaderView.Interactive)  # 评分列
        header.setSectionResizeMode(5, QHeaderView.Interactive)  # 评价数列
        header.setSectionResizeMode(6, QHeaderView.Interactive)  # 经度列
        header.setSectionResizeMode(7, QHeaderView.Interactive)  # 纬度列
        
        # 设置默认列宽
        self.result_table.setColumnWidth(0, 200)  # 名称列
        self.result_table.setColumnWidth(1, 300)  # 地址列
        self.result_table.setColumnWidth(2, 150)  # 类型列
        self.result_table.setColumnWidth(3, 120)  # 电话列
        self.result_table.setColumnWidth(4, 80)   # 评分列
        self.result_table.setColumnWidth(5, 80)   # 评价数列
        self.result_table.setColumnWidth(6, 100)  # 经度列
        self.result_table.setColumnWidth(7, 100)  # 纬度列
        
        # 允许表格根据内容调整行高
        self.result_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        layout.addWidget(self.result_table)
        
        # 更新区域下拉框
        self.update_districts(self.city_combo.currentText())
        
        # 添加页码和提示信息区域
        info_layout = QHBoxLayout()
        
        # 添加API调用限制提示
        api_limit_label = QLabel('注意: 每个key每日关键字搜索限制为100次，并发上限3次/秒，请合理使用')
        api_limit_label.setStyleSheet('color: red;')
        info_layout.addWidget(api_limit_label)
        
        # 添加结果计数
        self.result_count_label = QLabel('查询结果: 0 条')
        info_layout.addWidget(self.result_count_label)
        
        # 添加查询次数显示
        self.query_count_label = QLabel('今日查询次数: 0/100')
        self.query_count_label.setStyleSheet('color: blue;')
        info_layout.addWidget(self.query_count_label)
        
        # 添加页码控制
        page_layout = QHBoxLayout()
        
        # 添加每页显示数量控制
        page_size_label = QLabel('每页显示:')
        self.page_size_input = QLineEdit()
        self.page_size_input.setFixedWidth(50)
        self.page_size_input.setText('20')  # 修改这里，默认值改为20
        self.page_size_input.setPlaceholderText('1-50')
        page_size_unit = QLabel('条')
        
        page_layout.addWidget(page_size_label)
        page_layout.addWidget(self.page_size_input)
        page_layout.addWidget(page_size_unit)
        
        # 原有的页码控制
        self.page_label = QLabel('当前页码: 1')
        self.prev_btn = QPushButton('上一页')
        self.next_btn = QPushButton('下一页')
        self.prev_btn.clicked.connect(lambda: self.change_page(-1))
        self.next_btn.clicked.connect(lambda: self.change_page(1))
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        
        page_layout.addWidget(self.prev_btn)
        page_layout.addWidget(self.page_label)
        page_layout.addWidget(self.next_btn)
        
        info_layout.addLayout(page_layout)
        
        layout.addLayout(info_layout)
        
        # 添加分页相关的属性
        self.current_page = 1
        self.total_pages = 1
        self.last_search_params = None

    def export_results(self):
        if self.result_table.rowCount() == 0:
            QMessageBox.warning(self, '警告', '没有可导出的数据！')
            return
            
        # 生成默认文件名（包含时间戳）
        default_filename = f"POI查询结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # 打开文件保存对话框
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出结果",
            default_filename,
            "CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    # 写入表头
                    headers = []
                    for col in range(self.result_table.columnCount()):
                        headers.append(self.result_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # 写入数据
                    for row in range(self.result_table.rowCount()):
                        row_data = []
                        for col in range(self.result_table.columnCount()):
                            item = self.result_table.item(row, col)
                            row_data.append(item.text() if item else '')
                        writer.writerow(row_data)
                        
                QMessageBox.information(self, '成功', f'数据已成功导出到：\n{filename}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'导出失败：{str(e)}')
    
    def update_cities(self, province):
        """获取选中省份的城市列表"""
        self.city_combo.clear()
        if not province:
            return
            
        # 如果缓存中有数据，直接使用缓存
        if province in self.city_cache:
            self.city_combo.addItems(self.city_cache[province])
            return
            
        try:
            # 显示加载提示
            self.city_combo.addItem("加载中...")
            self.city_combo.setEnabled(False)
            
            url = "https://restapi.amap.com/v3/config/district"
            params = {
                "key": self.api_key,
                "keywords": province,
                "subdistrict": "1",
                "output": "json"
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] == "1" and data["districts"]:
                cities = [city["name"] for city in data["districts"][0]["districts"]]
                # 保存到缓存
                self.city_cache[province] = cities
                
                self.city_combo.clear()
                self.city_combo.addItems(cities)
        except Exception as e:
            QMessageBox.critical(self, '错误', f"获取城市列表失败：{str(e)}")
        finally:
            self.city_combo.setEnabled(True)

    def update_districts(self, city):
        """获取选中城市的区域列表"""
        self.district_combo.clear()
        if not city:
            return
            
        # 如果缓存中有数据，直接使用缓存
        if city in self.district_cache:
            self.district_combo.addItems(self.district_cache[city])
            return
            
        try:
            # 显示加载提示
            self.district_combo.addItem("加载中...")
            self.district_combo.setEnabled(False)
            
            url = "https://restapi.amap.com/v3/config/district"
            params = {
                "key": self.api_key,
                "keywords": city,
                "subdistrict": "1",
                "output": "json"
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] == "1" and data["districts"]:
                districts = [district["name"] for district in data["districts"][0]["districts"]]
                # 保存到缓存
                self.district_cache[city] = districts
                
                self.district_combo.clear()
                self.district_combo.addItems(districts)
        except Exception as e:
            QMessageBox.critical(self, '错误', f"获取区域列表失败：{str(e)}")
        finally:
            self.district_combo.setEnabled(True)

    def change_page(self, delta):
        """翻页处理"""
        new_page = self.current_page + delta
        if new_page < 1 or new_page > self.total_pages:
            return
            
        self.current_page = new_page
        self.page_label.setText(f'当前页码: {self.current_page}')
        
        # 使用上次的搜索参数重新索
        if self.last_search_params:
            self.do_search(**self.last_search_params)

    def search(self):
        """搜索入口函数"""
        keyword = self.keyword_input.text()
        city = self.city_combo.currentText()
        district = self.district_combo.currentText()
        
        if not keyword:
            QMessageBox.warning(self, '警告', '请输入关键词！')
            return
            
        # 重置页码
        self.current_page = 1
        self.page_label.setText('当前页码: 1')
        
        # 保存搜索参数
        self.last_search_params = {
            'keyword': keyword,
            'city': city,
            'district': district
        }
        
        # 执行搜索
        self.do_search(**self.last_search_params)

    def update_query_count(self):
        """更新查询次数"""
        # 检查是否是新的一天
        current_date = date.today()
        if current_date != self.query_date:
            self.daily_query_count = 0
            self.query_date = current_date
        
        self.daily_query_count += 1
        self.query_count_label.setText(f'今日查询次数: {self.daily_query_count}/100')
        
        # 根据查询次数设置不同的颜色
        if self.daily_query_count >= 90:
            self.query_count_label.setStyleSheet('color: red;')
        elif self.daily_query_count >= 70:
            self.query_count_label.setStyleSheet('color: orange;')
        else:
            self.query_count_label.setStyleSheet('color: blue;')
        
        # 当接近限制时显示警告
        if self.daily_query_count == 90:
            QMessageBox.warning(self, '警告', '今日查询次数已达到90次，即将达到限制！')

    def check_query_limit(self):
        """检查是否超出限制"""
        # 检查日期是否更新
        current_date = date.today()
        if current_date != self.query_date:
            self.daily_query_count = 0
            self.query_date = current_date
            return True
        
        # 检查日调用量限制
        if self.daily_query_count >= 100:
            QMessageBox.critical(self, '错误', '已达到每日查询次数限制（100次），请明天再试！')
            return False
        
        # 检查并发限制（确保每次查询间隔至少0.4秒）
        current_time = time.time()
        if current_time - self.last_query_time < 0.4:
            time.sleep(0.4 - (current_time - self.last_query_time))
        
        self.last_query_time = time.time()
        return True

    def do_search(self, keyword, city, district):
        """执行实际的搜索操作"""
        # 检查限制
        if not self.check_query_limit():
            return
            
        try:
            self.result_table.setRowCount(0)
            
            # 获取并验证每页显示数量
            try:
                page_size = int(self.page_size_input.text())
                if page_size < 1 or page_size > 50:
                    QMessageBox.warning(self, '警告', '每页显示数量必须在1-50之间！')
                    page_size = 20  # 修改这里，默认值改为20
                    self.page_size_input.setText('20')
            except ValueError:
                QMessageBox.warning(self, '警告', '请输入有效的数字！')
                page_size = 20  # 修改这里，默认值改为20
                self.page_size_input.setText('20')
            
            url = "https://restapi.amap.com/v3/place/text"
            params = {
                "key": self.api_key,
                "keywords": keyword,
                "city": city,
                "output": "json",
                "extensions": "all",
                "offset": page_size,  # 使用用户输入的每页显示数量
                "page": self.current_page
            }
            
            if district:
                params["keywords"] = f"{district} {keyword}"
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] == "1":
                # 更新查询次数
                self.update_query_count()
                
                pois = data["pois"]
                total_count = int(data.get("count", 0))
                self.total_pages = (total_count + page_size - 1) // page_size  # 根据新的页大小计算总页数
                
                # 更新结果计数
                self.result_count_label.setText(f'查询结果: {total_count} 条')
                
                # 更新翻页按钮状态
                self.prev_btn.setEnabled(self.current_page > 1)
                self.next_btn.setEnabled(self.current_page < self.total_pages)
                
                # 显示结果
                self.result_table.setRowCount(len(pois))
                for row, poi in enumerate(pois):
                    # 处理每个字段，确保是字符串类型
                    name = str(poi["name"]) if "name" in poi else ""
                    address = str(poi["address"]) if "address" in poi else ""
                    type_str = str(poi["type"]) if "type" in poi else ""
                    tel = str(poi.get("tel", ""))
                    
                    # 获取评分和评价数
                    rating = str(poi.get("biz_ext", {}).get("rating", ""))
                    rating_count = str(poi.get("biz_ext", {}).get("rating_count", ""))
                    
                    # 处理经纬度
                    try:
                        location = poi["location"].split(",")
                        lng = str(location[0])  # 经度
                        lat = str(location[1])  # 纬度
                    except:
                        lng = ""
                        lat = ""
                    
                    # 设置表格项
                    self.result_table.setItem(row, 0, QTableWidgetItem(name))
                    self.result_table.setItem(row, 1, QTableWidgetItem(address))
                    self.result_table.setItem(row, 2, QTableWidgetItem(type_str))
                    self.result_table.setItem(row, 3, QTableWidgetItem(tel))
                    self.result_table.setItem(row, 4, QTableWidgetItem(rating))
                    self.result_table.setItem(row, 5, QTableWidgetItem(rating_count))
                    self.result_table.setItem(row, 6, QTableWidgetItem(lng))
                    self.result_table.setItem(row, 7, QTableWidgetItem(lat))
            else:
                QMessageBox.critical(self, '错误', f"查询失败：{data.get('info', '未知错误')}")
                
        except Exception as e:
            QMessageBox.critical(self, '错误', f"发生错误：{str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = AmapSearchGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 
