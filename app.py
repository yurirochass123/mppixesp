from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

@app.route("/criar-pix", methods=["POST"])
def criar_pix():
    payload = {
        "transaction_amount": 1.00,
        "description": "Compra de água",
        "payment_method_id": "pix",
        "payer": {
            "email": "comprador@email.com",
            "first_name": "Cliente",
            "last_name": "Teste",
            "identification": {
                "type": "CPF",
                "number": "12345678909"
            },
            "address": {
                "zip_code": "06233200",
                "street_name": "Rua Exemplo",
                "street_number": "123",
                "neighborhood": "Bairro",
                "city": "São Paulo",
                "federal_unit": "SP"
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers)

    if response.status_code == 201:
        dados = response.json()
        return jsonify({
            "id": dados["id"],
            "qr_code": dados["point_of_interaction"]["transaction_data"]["qr_code"],
            "qr_code_base64": dados["point_of_interaction"]["transaction_data"]["qr_code_base64"],
            "status": dados["status"]
        })
    else:
        return jsonify({"erro": response.json()}), response.status_code

@app.route("/", methods=["GET"])
def hello():
    return "Servidor Pix ativo 🚰", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
