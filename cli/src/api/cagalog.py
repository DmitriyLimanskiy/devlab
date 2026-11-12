from httpx import request


class Catalog:
    def get_catalog():
        response = request("GET", "http://127.0.0.1:8080/api/v1/catalog")
        response.raise_for_status()
        return response.json()
