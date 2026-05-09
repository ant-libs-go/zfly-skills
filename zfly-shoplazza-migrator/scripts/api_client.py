import requests


class ShoplazzaClient:
    def __init__(self, slug, access_token):
        self.base_url = (
            f"https://{slug.strip('/')}.myshoplaza.com/openapi/2025-06/products"
        )
        self.headers = {
            "Content-Type": "application/json",
            "Access-Token": access_token,
        }

    def create_product(self, payload_dict):
        response = requests.post(self.base_url, headers=self.headers, json=payload_dict)
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            print(f"ERROR: 创建失败 {response.status_code} - {response.text}")
            return None
