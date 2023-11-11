import sys
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTableWidget, \
    QTableWidgetItem, QMessageBox, QDesktopWidget
from PyQt5.QtCore import Qt
import psycopg2
from tables_form import TablesWindow


class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.tables_window = None

        self.setWindowTitle('Авторизація')
        self.setGeometry(0, 0, 500, 300)
        self.setStyleSheet("background-color: #121212; color: #ffffff;")

        #По центру
        screen = QDesktopWidget().screenGeometry()
        window_size = self.geometry()
        x = int((screen.width() - window_size.width()) // 2)
        y = int((screen.height() - window_size.height()) // 3)
        self.move(x, y)

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
            self.close()
        except psycopg2.Error as e:
            alert = QMessageBox()
            alert.setText("email або пароль вказано неправильно")
            # result = alert.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AuthWindow()
    window.show()
    sys.exit(app.exec_())