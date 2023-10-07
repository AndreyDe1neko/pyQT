from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5 import QtGui  # Добавьте этот импорт

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
        print(last_column)
        self.insertColumn(last_column)
        self.horizontalHeader().setSectionResizeMode(last_column, QHeaderView.Stretch)

        header_style = "QHeaderView::section { background-color: gray; color: white; font-size: 18px; font-weight: 900;}"
        self.setStyleSheet(header_style)
        # self.setStyleSheet()
        # self.loading = False
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

                # self.loading = False

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


class TablesWindow(QWidget):
    def __init__(self, connection):
        super().__init__()
        self.setWindowTitle('Tables')
        self.setGeometry(0, 0, 1000, 800)
        self.setStyleSheet("background-color: #121212; color: #ffffff;")
        self.connection = connection

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
        selection-background-color: #7a506f; /* Фіолетовий колір фону при виборі */
    }
    QComboBox QAbstractItemView::item {
        background-color: #2E2E2E;
        color: #FFFFFF;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: #7a506f; /* Фіолетовий колір фону при наведенні */
    }
    QComboBox::item:selected {
        background-color: #4CAF50;
    }
""")
        self.table_combobox.setFixedWidth(200)
        self.table_combobox.currentIndexChanged.connect(self.on_combobox_change)
        layout.addWidget(self.table_combobox)

        self.table_widget = LazyLoadTableWidget(connection, self)
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

    def on_combobox_change(self):
        self.table_widget.clearContents()
        self.table_widget.setRowCount(0)
        self.table_widget.loaded_rows = 0
        self.table_widget.load_more_data()

    # selected_table = self.table_combobox.currentText()
    # self.table_combobox.currentIndexChanged.connect(self.on_combobox_change)
    # selected_table = self.table_combobox.currentText()
    # self.table_combobox.currentIndexChanged.connect(self.on_combobox_change)
