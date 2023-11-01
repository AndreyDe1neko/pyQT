import os

import pandas as pd
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, \
    QDesktopWidget, QPushButton, QMainWindow, QFileDialog, QHBoxLayout
from PyQt5.QtCore import Qt, QUrl
from PyQt5 import QtGui, QtPrintSupport
import pdfkit
import plotly.express as px
import plotly.graph_objects as go
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

table_translation_dict = {
    "mqtt_server": "Сервер MQTT",
    "station": "Станція",
    "coordinates": "Координати",
    "favourite": "Улюблене",
    "category": "Категорія",
    "measured_unit": "Одиниця вимірювання",
    "optimal_value": "Оптимальні значення",
    "mqtt_message_unit": "Повідомлення MQTT",
    "measument": "Вимірювання"
}


class LazyLoadTableWidget(QTableWidget):

    def __init__(self, connection, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = connection
        self.batch_size = 100  # Кількість записів, які завантажуються за один раз
        self.loaded_rows = 0
        self.verticalHeader().setHidden(True)
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # Растягиваем столбцы под содержимое

        # Добавляем последний столбец, который будет растягиваться по ширине таблицы
        last_column = self.columnCount()
        self.insertColumn(last_column)
        self.horizontalHeader().setSectionResizeMode(last_column, QHeaderView.Stretch)

        header_style = """
        QHeaderView::section { 
            background-color: gray; 
            color: white; 
            font-size: 18px; 
            font-weight: 900;
            }
            """
        self.setStyleSheet(header_style)
        self.load_more_data()

    def load_more_data(self):
        table_translation_dict = {
            "mqtt_server": "Сервер MQTT",
            "station": "Станція",
            "coordinates_view": "Координати",
            "favourite_view": "Улюблене",
            "category": "Категорія",
            "measured_unit": "Одиниця вимірювання",
            "optimal_value_view": "Оптимальні значення",
            "mqtt_message_unit_view": "Повідомлення MQTT",
            "measument_view": "Вимірювання"
        }

        cursor = self.connection.cursor()
        selected_table = self.current_table_name()
        for k, v in table_translation_dict.items():
            if v == selected_table:
                selected_table = k
        sql_query = f"SELECT * FROM {selected_table} OFFSET {self.loaded_rows} LIMIT {self.batch_size};"
        cursor.execute(sql_query)
        data = cursor.fetchall()

        translation_dict = {
            "id_server": "ID сервера",
            "url": "URL",
            "server_status": "Статус сервера",

            "id_station": "ID станції",
            "city": "Місто",
            "name_station": "Назва станції",
            "status_station": "Статус станції",
            "id_saveecobot": "ID збереженого екобота",

            "longitude": "Довгота",
            "latitude": "Широта",
            "coordinate": "Координати",
            "category": "Категорії",
            "user_name": "Ім'я користувача",

            "id_category": "ID категорії",
            "designation": "Позначення категорії",

            "id_measured_unit": "ID одиниці вимірювання",
            "title": "Заголовок",
            "unit": "Одиниця вимірювання",

            "bottom_border": "Нижня границя",
            "upper_border": "Верхня границя",

            "messages": "Повідомлення",
            "order_mqtt_unit": "Порядок одиниці вимірювання",
            "measured_unit": "Вимірювальна одиниця",
            "id_measument": "ID вимірювання",
            "time_meas": "Час вимірювання",
            "value_meas": "Значення вимірювання"
        }

        if data:
            if self.loaded_rows == 0:
                column_names = [desc[0] for desc in cursor.description]
                # Перетворення назв стовпців за допомогою словника
                translated_column_names = [translation_dict.get(col, col) for col in column_names]
                self.setColumnCount(len(translated_column_names))
                self.setHorizontalHeaderLabels(translated_column_names)

            for row_data in data:
                row_position = self.loaded_rows

                self.insertRow(row_position)
                for col_num, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    item.setFont(QtGui.QFont("Arial", 14))  # Установите желаемый размер шрифта (например, 24)
                    self.setItem(row_position, col_num, item)

                self.loaded_rows += 1
                self.loading = False

    def current_table_name(self):
        return self.parent().table_combobox.currentText()

    def scrollContentsBy(self, dx, dy):
        # Викликається при прокручуванні вмісту
        super().scrollContentsBy(dx, dy)
        scrollbar = self.verticalScrollBar()
        max_value = scrollbar.maximum()
        current_value = scrollbar.value()
        # Якщо користувач долистав до кінця таблиці
        if current_value >= max_value:
            self.load_more_data()

    def clear_table(self):
        self.clearContents()
        self.setRowCount(0)
        self.loaded_rows = 0


class TablesWindow(QWidget):
    def __init__(self, connection):
        super().__init__()
        self.power_bi_app = None
        self.setWindowTitle('Tables')
        self.setGeometry(0, 0, 1000, 800)
        self.setStyleSheet("background-color: #121212; color: #ffffff;")
        self.connection = connection

        screen = QDesktopWidget().screenGeometry()
        window_size = self.geometry()
        x = int((screen.width() - window_size.width()) // 2)
        y = int((screen.height() - window_size.height()) // 3)
        self.move(x, y)

        cursor = connection.cursor()
        sql_query = "SELECT tablename FROM pg_tables WHERE schemaname='public';"
        cursor.execute(sql_query)
        names = cursor.fetchall()

        self.table_names = [table_translation_dict.get(name[0]) for name in names]

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        default_for_combobox = """
            QComboBox {
                background-color: #2E2E2E;
                color: #FFFFFF;
                border: 1px solid #555555;
                padding: 5px;
                font-size: 16px;
            }
            QComboBox QAbstractItemView {
                background-color: #2E2E2E;
                color: #FFFFFF;
                selection-background-color: #7a506f; 
            }
            QComboBox QAbstractItemView::item {
                background-color: #2E2E2E;
                color: #FFFFFF;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #7a506f; 
            }
            QComboBox::item:selected {
                background-color: #4CAF50;
            }
            QComboBox::hover
            {
            background-color: purple;
            }
        """

        default_for_buttons = '''
                    QPushButton {
                        background-color: #732370;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 15px;
                        font-size: 14px;
                        box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.5); /* Додайте тінь */
                    }
                    QPushButton:hover {
                        background-color: #9551a6;

                        }
                    QPushButton:pressed {
                        background-color: #43185d;  
                        border: 2px solid #9551a6;  
                    }
                    '''

        self.table_combobox = QComboBox(self)
        self.table_combobox.addItems(self.table_names)
        self.table_combobox.setStyleSheet(default_for_combobox)
        self.table_combobox.setFixedWidth(200)
        self.table_combobox.currentIndexChanged.connect(self.on_combobox_change)
        layout.addWidget(self.table_combobox)

        self.table_widget = LazyLoadTableWidget(connection, self)
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

        self.power_bi_app_first = PowerBIApp_first(connection)
        self.power_bi_app_first_graphic = PowerBIApp_first_graphic(connection)
        self.power_bi_app_second = PowerBIApp_second(connection)
        self.power_like_bi_app = PowerLikeBIApp(connection)

        self.report_like_BI_button = QPushButton('Показати', self)
        layout.addWidget(self.report_like_BI_button)
        self.report_like_BI_button.clicked.connect(self.report_like_BI_function)
        self.report_like_BI_button.setStyleSheet(default_for_buttons)

        self.report_BI_button = QPushButton('Показати', self)
        layout.addWidget(self.report_BI_button)
        self.report_BI_button.clicked.connect(self.report_BI_function)
        self.report_BI_button.setStyleSheet(default_for_buttons)

        self.connected_stations_without_dublicate_button = QPushButton('Показати', self)
        layout.addWidget(self.connected_stations_without_dublicate_button)
        self.connected_stations_without_dublicate_button.clicked.connect(self.report_BI_second_function)
        self.connected_stations_without_dublicate_button.setStyleSheet(default_for_buttons)

        self.first_graphic_button = QPushButton('Показати', self)
        layout.addWidget(self.first_graphic_button)
        self.first_graphic_button.clicked.connect(self.report_graphic_Like_BI_function)
        self.first_graphic_button.setStyleSheet(default_for_buttons)

    def report_BI_function(self):
        self.power_bi_app_first.show()

    def report_graphic_Like_BI_function(self):
        self.power_bi_app_first_graphic.show()

    def report_BI_second_function(self):
        self.power_bi_app_second.show()

    def report_like_BI_function(self):
        self.power_like_bi_app.show()



    def on_combobox_change(self):
        self.table_widget.clearContents()
        self.table_widget.setRowCount(0)
        self.table_widget.loaded_rows = 0
        self.table_widget.load_more_data()
        self.table_widget.clear_table()  # Очищаємо таблицю перед завантаженням нових даних
        self.table_widget.load_more_data()

    # selected_table = self.table_combobox.currentText()
    # self.table_combobox.currentIndexChanged.connect(self.on_combobox_change)
    # selected_table = self.table_combobox.currentText()
    # self.table_combobox.currentIndexChanged.connect(self.on_combobox_change)


class PowerLikeBIApp(QMainWindow):
    def __init__(self, connection):
        super().__init__()
        self.connection = connection
        self.initUI()

    def initUI(self):
        self.web_view = QWebEngineView()
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Создаем HTML-код для таблицы
        cursor = self.connection.cursor()
        sql_query = "SELECT * FROM connected_stations_without_dublicate"
        cursor.execute(sql_query)
        data = cursor.fetchall()
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #FFFFFF;
                    color: #000000;
                    margin: 20px;
                }}
                h1 {{
                    text-align: center;
                    color: #4CAF50;
                }}
                table {{
                    width: 80%;
                    margin: 20px auto;
                    border-collapse: collapse;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #723d7f;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #d7eaf9;
                }}
            </style>
        </head>
        <body>
            <table border="1">
                <tr>
                    <th>Адреса</th>
                    <th>Статус</th>
                    <th>Вимір</th>
                </tr>
                {''.join(["<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>".format(i1, i2, i3) for i1, i2, i3 in data])}
            </table>
        </body>
        </html>
        """

        web_view = QWebEngineView()
        web_view.setHtml(html_content)  # Устанавливаем HTML-код в QWebEngineView
        layout.addWidget(web_view)

        convert_button = QPushButton('Конвертувати в pdf', self)
        convert_button.clicked.connect(lambda: self.convertToPdf(html_content))
        convert_button.setStyleSheet('''
                    QPushButton {
                        background-color: #732370;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 15px;
                        font-size: 14px;
                        box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.5); /* Додайте тінь */
                    }
                    QPushButton:hover {
                        background-color: #9551a6;

                        }
                    QPushButton:pressed {
                        background-color: #43185d;  
                        border: 2px solid #9551a6;  
                    }
                    ''')
        # layout.addWidget(convert_button)

        print_button = QPushButton('Роздрукувати', self)
        print_button.clicked.connect(lambda: self.printToPdf(html_content))
        print_button.setStyleSheet('''
            QPushButton {
                background-color: #732370;
                color: white;
                padding: 10px 20px;
                border-radius: 15px;
                font-size: 14px;
                box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.5); /* Додайте тінь */
            }
            QPushButton:hover {
                background-color: #9551a6;

                }
            QPushButton:pressed {
                background-color: #43185d;  
                border: 2px solid #9551a6;  
            }
            ''')
        # layout.addWidget(print_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(print_button)
        button_layout.addWidget(convert_button)
        layout.addLayout(button_layout)

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('HTML Viewer')

    def printToPdf(self, html_content):
        # Создаем QTextDocument из HTML-кода
        document = QTextDocument()
        document.setHtml(html_content)

        # Создаем принтер
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)

        # Показываем превью перед печатью
        preview = QPrintPreviewDialog(printer)
        preview.paintRequested.connect(
            lambda: self.printPreview(document, printer))  # Подключаем слот для отображения содержимого
        preview.exec_()

    def printPreview(self, document, printer):
        # Отображаем содержимое в превью
        document.print_(printer)


    def convertToPdf(self, html_content):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Зберегти як PDF", "", "PDF Files (*.pdf);;All Files (*)",
                                                   options=options)

        if file_path:
            config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
            pdfkit.from_string(html_content, file_path, configuration=config)


class CustomWebEnginePage(QWebEnginePage):
    def certificateError(self, error):
        # Ignore SSL certificate errors
        return True


class PowerBIApp_second(QMainWindow):
    def __init__(self, connection):
        super().__init__()
        self.setWindowTitle('Power BI Report')
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        self.webview = QWebEngineView(self)
        self.setCentralWidget(self.webview)

        # Set custom web engine page to handle SSL certificate errors
        page = CustomWebEnginePage(self.webview)
        self.webview.setPage(page)

        # URL of the Power BI report
        report_url = "https://app.powerbi.com/groups/me/reports/3afd1bfa-a43c-42a6-90dd-b6c284878b1e/ReportSection?ctid=b42ffd57-19ac-4d2f-867f-e971c16b5159&experience=power-bi"


        # Load the Power BI report in the QWebEngineView
        self.webview.load(QUrl(report_url))


class PowerBIApp_first(QMainWindow):
    def __init__(self, connection):
        super().__init__()
        self.setWindowTitle('Power BI Report')
        self.setGeometry(100, 100, 800, 600)
        self.connection = connection
        self.initUI()

    def initUI(self):
        self.webview = QWebEngineView(self)
        self.setCentralWidget(self.webview)

        # Set custom web engine page to handle SSL certificate errors
        page = CustomWebEnginePage(self.webview)
        self.webview.setPage(page)

        # URL of the Power BI report
        report_url = "https://app.powerbi.com/groups/me/reports/9abc14ba-e6cb-4f5e-9507-6fc776b81356/ReportSection?ctid=b42ffd57-19ac-4d2f-867f-e971c16b5159&pbi_source=shareVisual&visual=4872a1397275ad62d5d6&height=503.45&width=581.20&bookmarkGuid=b6ef4b18-ac65-423f-9b93-f8e5451ba06c"

        # Load the Power BI report in the QWebEngineView
        self.webview.load(QUrl(report_url))


class PowerBIApp_first_graphic(QMainWindow):
    def __init__(self, connection):
        super().__init__()
        self.setWindowTitle('Power BI Report')
        self.setGeometry(100, 100, 800, 600)
        self.connection = connection

        # Створюємо головний контейнер для розміщення елементів у вікні
        main_layout = QVBoxLayout()

        # Додаємо QComboBox
        self.comboBox = QComboBox()
        self.comboBox.currentIndexChanged.connect(self.handle_combobox_change)
        self.comboBox.setStyleSheet("""
            QComboBox {
                background-color: #2E2E2E;
                color: #FFFFFF;
                border: 1px solid #555555;
                padding: 5px;
                font-size: 16px;
            }
            QComboBox QAbstractItemView {
                background-color: #2E2E2E;
                color: #FFFFFF;
                selection-background-color: #7a506f; 
            }
            QComboBox QAbstractItemView::item {
                background-color: #2E2E2E;
                color: #FFFFFF;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #7a506f; 
            }
            QComboBox::item:selected {
                background-color: #4CAF50;
            }
            QComboBox::hover
            {
            background-color: purple;
            }
        """)
        main_layout.addWidget(self.comboBox)

        # Створюємо Figure та встановлюємо його розміри та стиль графіку
        self.figure, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        # Створюємо центральний віджет та встановлюємо його головний контейнер
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Викликаємо метод для заповнення QComboBox початковими даними
        self.populate_combobox()

    def populate_combobox(self):
        cursor = self.connection.cursor()
        sql_query_db_names = "SELECT DISTINCT Адреса FROM connected_stations_without_dublicate"
        cursor.execute(sql_query_db_names)
        adress_name = cursor.fetchall()

        adress_names = [list(name)[0] for name in adress_name]
        for name in adress_names:
            self.comboBox.addItem(name)

    def handle_combobox_change(self):
        selected_address = self.comboBox.currentText()

        cursor = self.connection.cursor()
        sql_query = f"SELECT \"Вимір\", MIN(\"Величина\"), MAX(\"Величина\"), AVG(\"Величина\") FROM station_measurment_time_view WHERE \"Адреса\" = '{selected_address}' GROUP BY \"Вимір\""
        cursor.execute(sql_query)
        results = cursor.fetchall()
        # Розділіть результати на назви величин, мінімальні, максимальні та середні значення
        measurement_names = [row[0] for row in results]
        # print(measurement_names)
        min_values = [row[1] for row in results]
        max_values = [row[2] for row in results]
        avg_values = [row[3] for row in results]
        # print(max_values)
        # print(min_values)
        # print(avg_values)

        # Очистимо попередні дані з графіку та відобразимо нові дані
        self.ax.clear()

        # Побудова графіку для кожної величини
        for i, name in enumerate(measurement_names):
            min_val = min_values[i]
            max_val = max_values[i]
            avg_val = avg_values[i]

            self.ax.barh(f"{name} (min)", min_val, color='r', label='Мінімальне значення')
            self.ax.barh(f"{name} (max)", max_val, color='g', left=0, label='Максимальне значення')
            self.ax.barh(f"{name} (avg)", avg_val, color='b', left=0, label='Середнє значення')

        self.ax.set_xlabel('Значення')
        self.ax.set_ylabel('Величина вимірювання')
        self.ax.set_title(f'Мінімальні, максимальні та середні значення для адреси: {selected_address}')
        self.ax.legend()
        self.ax.grid(True)

        # Оновимо графік на віджеті FigureCanvas
        self.canvas.draw()