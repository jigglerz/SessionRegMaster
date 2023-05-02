from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QPlainTextEdit, QProgressBar


class UIComponents(QWidget):

    def init_ui(self):
        layout = QVBoxLayout()

        self.client_id_label = QLabel("Client ID:")
        self.client_id = QLineEdit()
        layout.addWidget(self.client_id_label)
        layout.addWidget(self.client_id)

        self.client_secret_label = QLabel("Client Secret:")
        self.client_secret = QLineEdit()
        layout.addWidget(self.client_secret_label)
        layout.addWidget(self.client_secret)

        self.account_id_label = QLabel("Account ID:")
        self.account_id = QLineEdit()
        layout.addWidget(self.account_id_label)
        layout.addWidget(self.account_id)

        self.event_id_label = QLabel("Event ID:")
        self.event_id = QLineEdit()
        layout.addWidget(self.event_id_label)
        layout.addWidget(self.event_id)

        self.excel_file_label = QLabel("Excel File:")
        self.excel_file = QLineEdit()
        layout.addWidget(self.excel_file_label)
        layout.addWidget(self.excel_file)

        self.browse_button = QPushButton("Browse")
        layout.addWidget(self.browse_button)

        self.links_label = QLabel("Generated Links:")
        self.links_output = QPlainTextEdit()
        self.links_output.setReadOnly(True)
        layout.addWidget(self.links_label)
        layout.addWidget(self.links_output)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.execute_button = QPushButton("Add registrations")
        layout.addWidget(self.execute_button)

        self.delete_reg_button = QPushButton("Remove registrations")
        layout.addWidget(self.delete_reg_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setVisible(False)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)
