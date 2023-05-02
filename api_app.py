import sys
import openpyxl
import requests
from typing import List

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QPlainTextEdit,
    QHBoxLayout,
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QTextDocument

from request_thread import RequestThread
from api_request import APIRequest
from data_processor import DataProcessor
from token_provider import TokenProvider


class APIRequest:
    def __init__(self, access_token: str):
        self.access_token = access_token

    def send_request(self, url: str) -> bool:
        max_retries = 3
        headers = {"Authorization": f"Bearer {self.access_token}"}

        attempts = 0
        success = False
        while not success and attempts < max_retries:
            try:
                response = requests.put(url, headers=headers)
                if response.status_code >= 301:
                    raise requests.exceptions.RequestException(f"Error response: {response.status_code}")
                success = True
            except requests.exceptions.RequestException as e:
                attempts += 1

        return success


class DataProcessor:
    def __init__(self, event_id: str):
        self.event_id = event_id

    def generate_links(self, data_dict: dict) -> List[str]:
        links = []
        for key, value_list in data_dict.items():
            for value in value_list:
                link = f"https://api.bizzabo.com/v1/events/{self.event_id}/agenda/sessions/{key}/registrations/{value}"
                links.append(link)
        return links

    def process_excel_data(self, file_path: str) -> dict:
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active

        data_dict = {}

        for col in sheet.columns:
            key = col[0].value
            if key is None:
                continue

            key_int = int(key)

            values = []
            for cell in col[1:]:
                if cell.value is None:
                    continue

                if isinstance(cell.value, int):
                    values.append(cell.value)
                else:
                    value_str = format(cell.value, '.0f') if cell.value.is_integer() else format(cell.value,
                                                                                                 '.{}g'.format(
                                                                                                     cell.number_format.count(
                                                                                                         '0')))
                    values.append(value_str)
            data_dict[key_int] = values
        return data_dict


class TokenProvider:
    @staticmethod
    def get_access_token(client_id: str, client_secret: str, account_id: str) -> str:
        url = 'https://auth.bizzabo.com/oauth/token'

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        payload = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'audience': 'https://api.bizzabo.com/api',
            'account_id': account_id
        }

        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            access_token = response.json()['access_token']
            return access_token
        else:
            return ''


class APIApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.request_thread = None
        self.delete_request_thread = None
        self.running = False

    def init_ui(self):
        layout = QVBoxLayout()
        self.setFixedSize(400, 700)

        # Client ID
        self.client_id_label = QLabel("Client ID:")
        self.client_id = QLineEdit()
        layout.addWidget(self.client_id_label)
        layout.addWidget(self.client_id)
        self.client_id.setText("")

        # Client Secret
        self.client_secret_label = QLabel("Client Secret:")
        self.client_secret = QLineEdit()
        layout.addWidget(self.client_secret_label)
        layout.addWidget(self.client_secret)
        self.client_secret.setText("")

        # Account ID
        self.account_id_label = QLabel("Account ID:")
        self.account_id = QLineEdit()
        layout.addWidget(self.account_id_label)
        layout.addWidget(self.account_id)
        self.account_id.setText("")

        # Event ID
        self.event_id_label = QLabel("Event ID:")
        self.event_id = QLineEdit()
        layout.addWidget(self.event_id_label)
        layout.addWidget(self.event_id)
        self.event_id.setText("")

        # Excel File
        self.excel_file_label = QLabel("Excel File:")
        self.excel_file = QLineEdit()
        self.excel_file.setEnabled(False)
        layout.addWidget(self.excel_file_label)
        layout.addWidget(self.excel_file)

        self.browse_button = QPushButton("Browse", self)
        self.browse_button.setFixedWidth(100)
        self.browse_button.setFixedHeight(30)
        self.browse_button.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_button)

        # Generated Links
        self.links_label = QLabel("Generated Links:")
        self.links_output = QPlainTextEdit()
        self.links_output.setReadOnly(True)
        self.links_output.setMinimumHeight(100)
        self.links_output.setMinimumWidth(300)
        layout.addWidget(self.links_label)
        layout.addWidget(self.links_output)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { margin: 0px; }")
        layout.addStretch(1)
        layout.addWidget(self.progress_bar)
        layout.addStretch(1)
        self.progress_bar.setMinimumWidth(300)
        self.progress_bar.setMinimumHeight(40)

        # Execute button
        self.execute_button = QPushButton("Add registrations", self)
        self.execute_button.clicked.connect(self.execute)
        self.execute_button.setMinimumHeight(50)
        self.execute_button.setMinimumWidth(100)
        layout.addWidget(self.execute_button)

        # Delete registration button
        self.delete_reg_button = QPushButton("Remove registrations", self)
        self.delete_reg_button.clicked.connect(self.delete_registration)
        self.delete_reg_button.setMinimumHeight(50)
        self.delete_reg_button.setMinimumWidth(100)
        layout.addWidget(self.delete_reg_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.cancel)
        self.cancel_button.setMinimumHeight(50)
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.setVisible(False)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)
        self.setWindowTitle('Session Bulk Registration')

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "",
                                                   "Excel Files (*.xlsx *.xls);;All Files (*)")
        if file_name:
            self.excel_file.setText(file_name)

    def execute(self):
        if not self.running:
            if not self.client_id.text() or not self.client_secret.text() or not self.account_id.text() or not self.event_id.text() or not self.excel_file.text():
                QMessageBox.warning(self, "Warning", "Please fill in all fields.")
                return

            access_token = TokenProvider.get_access_token(self.client_id.text(), self.client_secret.text(),
                                                          self.account_id.text())
            if access_token:
                data_processor = DataProcessor(self.event_id.text())
                data_dict = data_processor.process_excel_data(self.excel_file.text())
                url_list = data_processor.generate_links(data_dict)

                self.progress_bar.setVisible(True)
                self.delete_reg_button.setEnabled(False)
                self.progress_bar.setMaximum(len(url_list))

                # Disable execute button and set its text to "Cancel"
                self.execute_button.setText("Cancel")
                self.running = True

                # Run send_requests in a separate thread
                self.request_thread = RequestThread(access_token, url_list)
                self.request_thread.progress_signal.connect(self.update_progress_bar)
                self.request_thread.link_signal.connect(self.update_links)
                self.request_thread.finished.connect(self.on_requests_finished)
                self.request_thread.start()

            else:
                QMessageBox.critical(self, "Error", "Failed to obtain access token.")
        else:
            self.cancel()

    def delete_registration(self):
        if not self.running:
            if not self.client_id.text() or not self.client_secret.text() or not self.account_id.text() or not self.event_id.text() or not self.excel_file.text():
                QMessageBox.warning(self, "Warning", "Please fill in all fields.")
                return

            access_token = TokenProvider.get_access_token(self.client_id.text(), self.client_secret.text(),
                                                          self.account_id.text())
            if access_token:
                data_processor = DataProcessor(self.event_id.text())
                data_dict = data_processor.process_excel_data(self.excel_file.text())
                url_list = data_processor.generate_links(data_dict)

                self.progress_bar.setVisible(True)
                self.execute_button.setEnabled(False)
                self.progress_bar.setMaximum(len(url_list))

                # Disable delete button and set its text to "Cancel"
                self.delete_reg_button.setText("Cancel")
                self.running = True

                # Run send_requests in a separate thread
                self.delete_request_thread = RequestThread(access_token, url_list, request_method="DELETE")
                self.delete_request_thread.progress_signal.connect(self.update_progress_bar)
                self.delete_request_thread.link_signal.connect(self.update_links)
                self.delete_request_thread.finished.connect(self.on_delete_requests_finished)
                self.delete_request_thread.start()

            else:
                QMessageBox.critical(self, "Error", "Failed to obtain access token.")
        else:
            self.cancel_delete()

    def update_links(self, link, response_code, response_text):
        if 200 <= response_code < 300:
            message = f"<span style='color:green;'><br>Success! (Code: {response_code})</span>"
        else:
            message = f"<span style='color:red;'><br>Error: {response_code} - {response_text}</span>"

        document = QTextDocument()
        document.setHtml(f"{link} {message}")
        self.links_output.appendHtml(document.toHtml())

        # Scroll to the bottom of the widget
        scrollbar = self.links_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def on_requests_finished(self):
        QMessageBox.information(self, "Success", "Sending API requests is finished.")
        self.reset_progress_bar()
        self.delete_reg_button.setEnabled(True)
        self.execute_button.setText("Add registrations")
        self.running = False
        self.request_thread.failed_requests.save_to_excel(self)

    def reset_progress_bar(self):
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

    def cancel(self):
        # Disable the cancel button and set its text back to "Execute"
        self.execute_button.setText("Add registrations")
        self.running = False

        # Stop the request thread
        if self.request_thread is not None:
            self.request_thread.cancel()
            self.request_thread.wait()

    def on_delete_requests_finished(self):
        QMessageBox.information(self, "Success", "Sending API requests is finished.")
        self.reset_progress_bar()
        self.delete_reg_button.setText("Remove registrations")
        self.execute_button.setEnabled(True)
        self.running = False
        self.delete_request_thread.failed_requests.save_to_excel(self)

    def cancel_delete(self):
        # Disable the cancel button and set its text back to "Delete registration"
        self.delete_reg_button.setText("Remove registrations")
        self.running = False
        self.execute_button.setEnabled(True)

        # Stop the delete request thread
        if self.delete_request_thread is not None:
            self.delete_request_thread.cancel()
            self.delete_request_thread.wait()


