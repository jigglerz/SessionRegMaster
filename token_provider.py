import requests


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
