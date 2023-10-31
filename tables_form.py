import pandas as pd
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, \
    QDesktopWidget, QPushButton, QMainWindow, QFileDialog, QHBoxLayout
from PyQt5.QtCore import Qt, QUrl
from PyQt5 import QtGui, QtPrintSupport
import pdfkit
import plotly.express as px
import plotly.graph_objects as go

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
        print(current_value)
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

        self.table_combobox = QComboBox(self)
        self.table_combobox.addItems(self.table_names)
        self.table_combobox.setStyleSheet("""
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
        self.table_combobox.setFixedWidth(200)
        self.table_combobox.currentIndexChanged.connect(self.on_combobox_change)
        layout.addWidget(self.table_combobox)

        self.table_widget = LazyLoadTableWidget(connection, self)
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

        self.report_like_BI_button = QPushButton('Показати', self)
        layout.addWidget(self.report_like_BI_button)
        self.report_like_BI_button.clicked.connect(self.report_like_BI_function)
        self.report_like_BI_button.setStyleSheet('''
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

    def report_like_BI_function(self):
        if not self.power_bi_app:
            self.power_bi_app = PowerBIApp(self.connection)
        self.power_bi_app.show()

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


class PowerBIApp(QMainWindow):
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
        sql_query = "SELECT * FROM connected_stations_list_view"
        cursor.execute(sql_query)
        data = cursor.fetchall()
        print(data)
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
        self.show()

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
















    # def __init__(self, connection, table_widget):
    #     super().__init__()
    #     self.connection = connection
    #
    #     self.table_widget = table_widget
    #     self.setWindowTitle("Power BI-like App")
    #     self.setGeometry(100, 100, 800, 600)
    #
    #     layout = QVBoxLayout()
    #     self.web_view = QWebEngineView()
    #
    #     central_widget = QWidget()
    #     central_layout = QVBoxLayout()
    #     central_layout.addWidget(self.web_view)
    #     central_widget.setLayout(central_layout)
    #     layout.addWidget(central_widget)
    #
    #     self.setCentralWidget(central_widget)
    #     self.load_data_and_plot()
    #     self.export_button = QPushButton("Експорт в Excel")
    #     self.export_button.clicked.connect(self.export_to_excel)
    #
    #     layout.addWidget(self.export_button)
    #     self.export_button.show()  # Убедитесь, что кнопка видна
    #
    # def export_to_excel(self):
    #     cursor = self.connection.cursor()
    #     sql_query = "SELECT * FROM connected_stations_list_view"
    #     cursor.execute(sql_query)
    #     data = cursor.fetchall()
    #     if data:
    #         # Преобразуйте кортеж в DataFrame
    #         df = pd.DataFrame(data, columns=['Location', 'Status', 'Parameter'])  # Замените названия столбцов на свои
    #         excel_file_path = 'D:/my_projects/python/Tkinter/data.xlsx'
    #         df.to_excel(excel_file_path, index=False)
    #         print(f'Data exported to {excel_file_path}')
    #     else:
    #         print('No data to export')
    #
    # def load_data_and_plot(self):
    #         # Load data (replace this with your data loading logic)
    #     cursor = self.connection.cursor()
    #     sql_query = "SELECT * FROM connected_stations_list_view"
    #     cursor.execute(sql_query)
    #     data = cursor.fetchall()
    #
    #     # Create a DataFrame from the retrieved data
    #     df = pd.DataFrame(data, columns=['Location', 'Status', 'Parameter'])
    #
    #     # Create a Plotly table from the DataFrame
    #     fig = go.Figure(data=[go.Table(header=dict(values=list(df.columns)),
    #                                    cells=dict(values=[df.Location, df.Status, df.Parameter]))
    #                           ])
    #
    #     # Save the Plotly table as an HTML file
    #     html_file_path = 'D:/my_projects/python/Tkinter/plotly_chart.html'
    #     fig.write_html(html_file_path, auto_open=False)
    #
    #     # Load the HTML file into the web widget
    #     self.web_view.load(QUrl.fromLocalFile(html_file_path))



    # def load_data_and_plot(self):
    #     # Load data (replace this with your data loading logic)
    #     data = []
    #     for row in range(self.table_widget.rowCount()):
    #         row_data = []
    #         for column in range(self.table_widget.columnCount()):
    #             item = self.table_widget.item(row, column)
    #             if item is not None:
    #                 row_data.append(item.text())
    #             else:
    #                 row_data.append(None)
    #         data.append(row_data)
    #     print(data)
    #     # Створити DataFrame з отриманих даних
    #     column_names = [self.table_widget.horizontalHeaderItem(col).text() for col in
    #                     range(self.table_widget.columnCount())]
    #     print(column_names)
    #     df = pd.DataFrame(data, columns=column_names)
    #     #
    #     # Створити графік Plotly з DataFrame
    #     fig = px.bar(df, x=column_names[0], y=column_names[1], title='Reporting services')
    #     #
    #     # # Зберегти графік Plotly як HTML-файл
    #     fig.write_html('D:/my_projects/python/Tkinter/plotly_chart.html', auto_open=False)
    #
    #     # Завантажити HTML-файл у веб-віджет
    #     self.web_view.load(QUrl.fromLocalFile('D:/my_projects/python/Tkinter/plotly_chart.html'))
