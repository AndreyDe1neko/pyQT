from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDesktopWidget,
    QPushButton,
    QMainWindow,
    QFileDialog,
    QHBoxLayout,
    QGridLayout,
    QDateEdit,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5 import QtGui
import pdfkit
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

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

default_for_datetime = """
    QDateEdit {
        background-color: #2E2E2E;
        color: #FFFFFF;
        border: 1px solid #555555;
        padding: 5px;
        font-size: 16px;
    }
    QDateEdit QAbstractItemView {
        background-color: #2E2E2E;
        color: #FFFFFF;
        selection-background-color: #7a506f; 
    }
    QDateEdit QAbstractItemView::item {
        background-color: #2E2E2E;
        color: #FFFFFF;
    }
    QDateEdit QAbstractItemView::item:hover {
        background-color: #7a506f; 
    }
    QDateEdit::item:selected {
        background-color: #4CAF50;
    }
    QDateEdit::hover
    {
    background-color: purple;
    }
"""

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
    def __init__(self, connection, login):
        super().__init__()
        self.power_bi_app = None
        self.setWindowTitle('Засоби монітору якості повітря')
        self.setGeometry(0, 0, 1000, 800)
        self.setStyleSheet("background-color: #121212; color: #ffffff;")
        self.connection = connection
        self.login = login
        screen = QDesktopWidget().screenGeometry()
        window_size = self.geometry()
        x = int((screen.width() - window_size.width()) // 2)
        y = int((screen.height() - window_size.height()) // 3)
        self.move(x, y)

        if self.login == "access_tables":
            cursor = connection.cursor()
            sql_query = "SELECT tablename FROM pg_tables WHERE schemaname='public';"
            cursor.execute(sql_query)
            names = cursor.fetchall()

            self.table_names = [table_translation_dict.get(name[0]) for name in names]

            layout = QGridLayout(self)
            layout.setAlignment(Qt.AlignTop)

            self.table_combobox = QComboBox(self)
            self.table_combobox.addItems(self.table_names)
            self.table_combobox.setStyleSheet(default_for_combobox)
            self.table_combobox.setFixedWidth(200)
            self.table_combobox.currentIndexChanged.connect(self.on_combobox_change)
            layout.addWidget(self.table_combobox, 0, 0, 1, 2)

            self.table_widget = LazyLoadTableWidget(connection, self)
            layout.addWidget(self.table_widget, 1, 0, 1, 2)

        elif self.login == "postgres":

            cursor = connection.cursor()
            sql_query = "SELECT tablename FROM pg_tables WHERE schemaname='public';"
            cursor.execute(sql_query)
            names = cursor.fetchall()

            self.table_names = [table_translation_dict.get(name[0]) for name in names]

            layout = QGridLayout(self)
            layout.setAlignment(Qt.AlignTop)

            self.table_combobox = QComboBox(self)
            self.table_combobox.addItems(self.table_names)
            self.table_combobox.setStyleSheet(default_for_combobox)
            self.table_combobox.setFixedWidth(200)
            self.table_combobox.currentIndexChanged.connect(self.on_combobox_change)
            layout.addWidget(self.table_combobox, 0, 0, 1, 2)

            self.table_widget = LazyLoadTableWidget(connection, self)
            layout.addWidget(self.table_widget, 1, 0, 1, 2)

            self.power_bi_app_first = PowerBIApp_first(connection)
            self.power_bi_app_first_graphic = PowerBIApp_first_graphic(connection)
            self.power_bi_app_second = PowerBIApp_second(connection)
            self.power_like_bi_app = PowerLikeBIApp(connection)
            self.power_bi_report_count_values = PowerBIReportCountValues(connection)

            self.report_like_BI_button = QPushButton(
                'Звіт писок підключених станцій з можливістю друкувати та ковертувати в pdf', self)
            self.report_like_BI_button.clicked.connect(self.report_like_bi_function)
            self.report_like_BI_button.setStyleSheet(default_for_buttons)
            layout.addWidget(self.report_like_BI_button, 2, 0)

            self.report_BI_button = QPushButton('Список підключених станцій PowerBI', self)
            self.report_BI_button.clicked.connect(self.report_bi_function)
            self.report_BI_button.setStyleSheet(default_for_buttons)
            layout.addWidget(self.report_BI_button, 2, 1)

            self.connected_stations_without_dublicate_button = QPushButton(
                'Результати вимірювань станції за часовий період PowerBI', self)
            self.connected_stations_without_dublicate_button.clicked.connect(self.report_bi_second_function)
            self.connected_stations_without_dublicate_button.setStyleSheet(default_for_buttons)
            layout.addWidget(self.connected_stations_without_dublicate_button, 3, 0)

            self.first_graphic_button = QPushButton('Результати вимірювань станції за часовий період', self)
            self.first_graphic_button.clicked.connect(self.report_graphic_like_bi_function)
            self.first_graphic_button.setStyleSheet(default_for_buttons)
            layout.addWidget(self.first_graphic_button, 3, 1)

            self.count_values_view_button = QPushButton('Графічне зображення отриманих результатів', self)
            self.count_values_view_button.clicked.connect(self.report_count_values_function)
            self.count_values_view_button.setStyleSheet(default_for_buttons)
            layout.addWidget(self.count_values_view_button, 4, 0, 1, 2)

        elif self.login == "access_reports":
            layout = QGridLayout(self)
            layout.setAlignment(Qt.AlignTop)

            self.power_bi_app_first = PowerBIApp_first(connection)
            self.power_bi_app_first_graphic = PowerBIApp_first_graphic(connection)
            self.power_bi_app_second = PowerBIApp_second(connection)
            self.power_like_bi_app = PowerLikeBIApp(connection)
            self.power_bi_report_count_values = PowerBIReportCountValues(connection)

            self.report_like_BI_button = QPushButton(
                'Звіт писок підключених станцій з можливістю друкувати та ковертувати в pdf', self)
            self.report_like_BI_button.clicked.connect(self.report_like_bi_function)
            self.report_like_BI_button.setStyleSheet(default_for_buttons)
            layout.addWidget(self.report_like_BI_button, 2, 0)

            self.report_BI_button = QPushButton('Список підключених станцій PowerBI', self)
            self.report_BI_button.clicked.connect(self.report_bi_function)
            self.report_BI_button.setStyleSheet(default_for_buttons)
            layout.addWidget(self.report_BI_button, 2, 1)

            self.connected_stations_without_dublicate_button = QPushButton(
                'Результати вимірювань станції за часовий період PowerBI', self)
            self.connected_stations_without_dublicate_button.clicked.connect(self.report_bi_second_function)
            self.connected_stations_without_dublicate_button.setStyleSheet(default_for_buttons)
            layout.addWidget(self.connected_stations_without_dublicate_button, 3, 0)

            self.first_graphic_button = QPushButton('Результати вимірювань станції за часовий період', self)
            self.first_graphic_button.clicked.connect(self.report_graphic_like_bi_function)
            self.first_graphic_button.setStyleSheet(default_for_buttons)
            layout.addWidget(self.first_graphic_button, 3, 1)

            self.count_values_view_button = QPushButton('Графічне зображення отриманих результатів', self)
            self.count_values_view_button.clicked.connect(self.report_count_values_function)
            self.count_values_view_button.setStyleSheet(default_for_buttons)
            layout.addWidget(self.count_values_view_button, 4, 0, 1, 2)

        self.setLayout(layout)

    def report_count_values_function(self) -> None:
        if self.login != 'access_tables':
            try:
                self.power_bi_report_count_values.show()
            except Exception as e:
                print(f"Error in report_BI_function: {e}")

    def report_bi_function(self) -> None:
        if self.login != 'access_tables':
            try:
                self.power_bi_app_first.show()
            except Exception as e:
                print(f"Error in report_BI_function: {e}")

    def report_graphic_like_bi_function(self) -> None:
        if self.login != 'access_tables':
            try:
                self.power_bi_app_first_graphic.show()
            except Exception as e:
                print(f"Error in report_graphic_Like_BI_function: {e}")

    def report_bi_second_function(self) -> None:
        if self.login != 'access_tables':
            try:
                self.power_bi_app_second.show()
            except Exception as e:
                print(f"Error in report_BI_second_function: {e}")

    def report_like_bi_function(self) -> None:
        if self.login != 'access_tables':
            try:
                self.power_like_bi_app.show()
            except Exception as e:
                print(f"Error in report_like_BI_function: {e}")

    def on_combobox_change(self):
        self.table_widget.clearContents()
        self.table_widget.setRowCount(0)
        self.table_widget.loaded_rows = 0
        self.table_widget.load_more_data()
        self.table_widget.clear_table()  # Очищаємо таблицю перед завантаженням нових даних
        self.table_widget.load_more_data()


class PowerBIReportCountValues(QMainWindow):
    def __init__(self, connection):
        super().__init__()
        self.connection = connection
        self.setGeometry(100, 100, 1800, 900)
        self.initUI()

    def initUI(self):
        self.webview = QWebEngineView(self)
        self.setCentralWidget(self.webview)

        # Set custom web engine page to handle SSL certificate errors
        page = CustomWebEnginePage(self.webview)
        self.webview.setPage(page)

        # URL of the Power BI report
        report_url = "https://app.powerbi.com/groups/me/reports/a202ae3c-3b0d-4c76-a8d8-71fbe0072101/ReportSectionfd2a5a13900278aa8244?experience=power-bi"

        # Load the Power BI report in the QWebEngineView
        self.webview.load(QUrl(report_url))



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
        <h1 style="text-align:center; color: #44244c;">Список підключених станцій</h1>
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
        convert_button.setStyleSheet(default_for_buttons)
        # layout.addWidget(convert_button)

        print_button = QPushButton('Роздрукувати', self)
        print_button.clicked.connect(lambda: self.printToPdf(html_content))
        print_button.setStyleSheet(default_for_buttons)
        # layout.addWidget(print_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(print_button)
        button_layout.addWidget(convert_button)
        layout.addLayout(button_layout)

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Звіт')

    def printToPdf(self, html_content):
        document = QTextDocument()
        document.setHtml(html_content)

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)

        preview = QPrintPreviewDialog(printer)
        preview.paintRequested.connect(
            lambda: self.printPreview(document, printer))  # Подключаем слот для отображения содержимого
        preview.exec_()

    def printPreview(self, document, printer):
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
        self.setGeometry(100, 100, 1200, 800)
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
        self.setGeometry(100, 100, 1200, 800)
        self.connection = connection
        self.initUI()

    def initUI(self):
        self.webview = QWebEngineView(self)
        self.setCentralWidget(self.webview)

        page = CustomWebEnginePage(self.webview)
        self.webview.setPage(page)

        report_url = "https://app.powerbi.com/groups/me/reports/9abc14ba-e6cb-4f5e-9507-6fc776b81356/ReportSection?ctid=b42ffd57-19ac-4d2f-867f-e971c16b5159&pbi_source=shareVisual&visual=4872a1397275ad62d5d6&height=503.45&width=581.20&bookmarkGuid=b6ef4b18-ac65-423f-9b93-f8e5451ba06c"

        self.webview.load(QUrl(report_url))


class PowerBIApp_first_graphic(QMainWindow):
    def __init__(self, connection):
        super().__init__()
        self.setWindowTitle('Power BI Report')
        self.setGeometry(100, 100, 1500, 800)
        self.connection = connection

        main_layout = QVBoxLayout()

        date_layout = QHBoxLayout()

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setStyleSheet(default_for_datetime)
        date_layout.addWidget(self.start_date_edit, stretch=1)
        self.start_date_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setStyleSheet(default_for_datetime)
        date_layout.addWidget(self.end_date_edit, stretch=1)
        self.end_date_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        main_layout.addLayout(date_layout)

        self.comboBox = QComboBox()
        self.comboBox.setStyleSheet(default_for_combobox)
        main_layout.addWidget(self.comboBox)

        self.first_graphic_button = QPushButton('Показати', self)
        main_layout.addWidget(self.first_graphic_button)
        self.first_graphic_button.clicked.connect(self.handle_combobox_change)
        self.first_graphic_button.setStyleSheet(default_for_buttons)

        self.figure, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.populate_combobox()

    def populate_combobox(self):
        cursor = self.connection.cursor()
        sql_query_db_names = "SELECT DISTINCT Адреса FROM connected_stations_without_dublicate"
        cursor.execute(sql_query_db_names)
        address_name = cursor.fetchall()

        address_names = [list(name)[0] for name in address_name]
        self.comboBox.addItems(address_names)

    def handle_combobox_change(self):
        selected_address = self.comboBox.currentText()

        cursor = self.connection.cursor()
        sql_query = """
            SELECT "Вимір", MIN("Величина"), MAX("Величина"), AVG("Величина")
            FROM station_measurment_time_view
            WHERE "Адреса" = %s AND "Дата" BETWEEN %s AND %s
            GROUP BY "Вимір"
        """
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd 00:00:00+03")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd 23:59:59+03")

        cursor.execute(sql_query, (selected_address, start_date, end_date))
        results = cursor.fetchall()

        measurement_names = [row[0] for row in results]
        min_values = [row[1] for row in results]
        max_values = [row[2] for row in results]
        avg_values = [row[3] for row in results]

        self.ax.clear()

        for i, name in enumerate(measurement_names):
            min_val = min_values[i]
            max_val = max_values[i]
            avg_val = avg_values[i]

            self.ax.barh(f"{name}(min)", min_val, color='r')
            self.ax.barh(f"{name}(max)", max_val, color='b', left=0)
            self.ax.barh(f"{name}(avg)", avg_val, color='g', left=0)

        self.ax.set_xlabel('Значення')
        self.ax.set_ylabel('Величина вимірювання')
        self.ax.set_title(f'Мінімальні, максимальні та середні значення для адреси: {selected_address}')
        self.ax.legend()
        self.ax.grid(True)

        self.canvas.draw()
