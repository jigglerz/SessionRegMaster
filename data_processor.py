import openpyxl
from typing import List


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
                    value_str = format(cell.value, '.0f') if cell.value.is_integer() else format(cell.value, '.{}g'.format(cell.number_format.count('0')))
                    values.append(value_str)
            data_dict[key_int] = values
        return data_dict
