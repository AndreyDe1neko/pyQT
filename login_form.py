import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTableWidget, \
    QTableWidgetItem
from PyQt5.QtCore import Qt
import psycopg2
from tables_form import TablesWindow


class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.tables_window = None

        self.setWindowTitle('Auth')
        self.setGeometry(0, 0, 500, 300)
        self.setStyleSheet("background-color: #121212; color: #ffffff;")

        self.label_login = QLabel('Нікнейм:', self)
        self.label_login.setStyleSheet('font-size: 20px; padding: 5px; text-align: center;')

        self.label_password = QLabel('Пароль:', self)
        self.label_password.setStyleSheet('font-size: 20px; padding: 5px; text-align: center;')

        self.login_textbox = QLineEdit(self)
        self.login_textbox.setStyleSheet('font-size: 20px; border-radius: 15px; background: #ffffff; color:#121212; padding: 5px 10px;')
        self.login_textbox.setPlaceholderText('postgres')

        self.pass_textbox = QLineEdit(self)
        self.pass_textbox.setEchoMode(QLineEdit.Password)
        self.pass_textbox.setStyleSheet('font-size: 20px; border-radius: 15px; background: #ffffff; color:#121212; padding: 5px 10px;')
        self.pass_textbox.setPlaceholderText('********')

        self.login_button = QPushButton('Увійти', self)
        self.login_button.clicked.connect(self.login_button_click_event)
        self.login_button.setStyleSheet('''
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
                box-shadow: 5px 5px 5px 5px blue;
            }
        ''')
        # self.exit_button = QPushButton('Exit', self)
        # self.exit_button.clicked.connect(self.close_window)
        # self.exit_button.setStyleSheet('font-size: 20px; padding: 10px 20px;')

        layout = QVBoxLayout(self)
        layout.addWidget(self.label_login)
        layout.addWidget(self.login_textbox)
        layout.addWidget(self.label_password)
        layout.addWidget(self.pass_textbox)
        # layout.addWidget(self.exit_button)
        layout.addWidget(self.login_button)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(100, 100, 100, 100)

        self.setLayout(layout)

    def close_window(self):
        return self.close()

    def login_button_click_event(self):
        login = self.login_textbox.text()
        password = self.pass_textbox.text()

        try:
            connection = psycopg2.connect(user=login, password=password, host="localhost", port="5432",
                                          database="MonitorAir")
            cursor = connection.cursor()

            self.tables_window = TablesWindow(connection)  # Создаем объект TablesWindow
            self.tables_window.show()
        except psycopg2.Error as e:
            print("Error: Unable to connect to the database")
            print(e)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AuthWindow()
    window.show()
    sys.exit(app.exec_())