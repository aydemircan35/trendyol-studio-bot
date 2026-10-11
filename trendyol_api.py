"""
trendyol_api.py
Trendyol Partner (Supplier) API İstemcisi.
Uçtan uca ürün yükleme, stok/fiyat güncelleme ve müşteri destek (Soru-Cevap) operasyonları.
"""

import base64
import requests
import json
import logging

logger = logging.getLogger(__name__)

class TrendyolClient:
    BASE_URL = "https://api.trendyol.com/sapigw/suppliers"

    def __init__(self, supplier_id: str, api_key: str, api_secret: str):
        self.supplier_id = str(supplier_id)
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Trendyol Basic Auth başlığı
        auth_str = f"{self.api_key}:{self.api_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json",
            "User-Agent": f"{self.supplier_id} - TrendyolManagerBot"
        }

    # ==========================
    # 1. ÜRÜN YÜKLEME & LİSTELEME
    # ==========================
    def create_product(self, product_data: dict) -> dict:
        """
        Yeni bir ürünü doğrudan Trendyol mağazasına yükler ve onaya gönderir.
        Endpoint: POST /suppliers/{supplierId}/v2/products
        """
        url = f"{self.BASE_URL}/{self.supplier_id}/v2/products"
        payload = {"items": [product_data]}
        try:
            res = requests.post(url, headers=self.headers, json=payload, timeout=20)
            return res.json() if res.status_code in [200, 201, 202] else {"error": res.text, "status": res.status_code}
        except Exception as e:
            logger.error(f"Trendyol ürün yükleme hatası: {e}")
            return {"error": str(e)}

    # ==========================
    # 2. MÜŞTERİ SORU-CEVAP (DESTEK)
    # ==========================
    def get_unanswered_questions(self, page: int = 0, size: int = 10) -> list:
        """
        Müşterilerden gelen ve henüz CEVAPLANMAMIŞ soruları çeker.
        Endpoint: GET /suppliers/{supplierId}/questions/filter?status=WAITING_FOR_ANSWER
        """
        url = f"{self.BASE_URL}/{self.supplier_id}/questions/filter"
        params = {
            "status": "WAITING_FOR_ANSWER",
            "page": page,
            "size": size
        }
        try:
            res = requests.get(url, headers=self.headers, params=params, timeout=15)
            if res.status_code == 200:
                data = res.json()
                return data.get("content", [])
            return []
        except Exception as e:
            logger.error(f"Trendyol soruları çekme hatası: {e}")
            return []

    def answer_customer_question(self, question_id: str, answer_text: str) -> dict:
        """
        Müşteri sorusuna Trendyol üzerinden yanıt gönderir.
        Endpoint: POST /suppliers/{supplierId}/questions/{questionId}/answers
        """
        url = f"{self.BASE_URL}/{self.supplier_id}/questions/{question_id}/answers"
        payload = {"text": answer_text}
        try:
            res = requests.post(url, headers=self.headers, json=payload, timeout=15)
            return {"success": True} if res.status_code in [200, 201, 204] else {"error": res.text}
        except Exception as e:
            logger.error(f"Soru yanıtlama hatası: {e}")
            return {"error": str(e)}

    # ==========================
    # 3. FİYAT VE STOK GÜNCELLEME
    # ==========================
    def update_price_and_stock(self, barcode: str, quantity: int, sale_price: float, list_price: float = None) -> dict:
        """
        Belirli bir barkodun stok ve satış fiyatını anında günceller.
        Endpoint: POST /suppliers/{supplierId}/products/price-and-inventory
        """
        url = f"{self.BASE_URL}/{self.supplier_id}/products/price-and-inventory"
        payload = {
            "items": [{
                "barcode": barcode,
                "quantity": quantity,
                "salePrice": sale_price,
                "listPrice": list_price or sale_price
            }]
        }
        try:
            res = requests.post(url, headers=self.headers, json=payload, timeout=15)
            return res.json() if res.status_code in [200, 202] else {"error": res.text}
        except Exception as e:
            logger.error(f"Fiyat/stok güncelleme hatası: {e}")
            return {"error": str(e)}
