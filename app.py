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
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
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

@app.route("/webhook", methods=["POST"])
def webhook():
    dados = request.json

    # Aqui você pode imprimir e analisar o conteúdo recebido
    print("🔔 Webhook recebido:", dados)

    # Exemplo: verificar se é um pagamento Pix aprovado
    if (
        dados.get("type") == "payment"
        and dados.get("action") == "payment.created"
        and dados.get("data")
    ):
        payment_id = dados["data"]["id"]
        print(f"Pagamento criado: ID {payment_id}")

        # Você pode fazer um GET para buscar detalhes desse pagamento
        # e verificar o status
        pagamento = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        ).json()

        if pagamento.get("status") == "approved":
            print("✅ Pagamento aprovado!")
            # Aqui você poderá acionar o ESP32 (via polling, MQTT, ou fila)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    print("🚀 Servidor Flask rodando na porta 8080...")
    app.run(host="0.0.0.0", port=8080)

