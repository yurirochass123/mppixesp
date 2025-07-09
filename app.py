from flask import Flask, request, jsonify
import requests
import os
import uuid

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

@app.route("/criar-pix", methods=["POST"])
def criar_pix():
    print("📨 Rota /criar-pix acionada")

    payload = {
        "transaction_amount": 1.00,
        "description": "Compra de água",
        "payment_method_id": "pix",
        "payer": {
            "email": "comprador@email.com"
        }
    }

    idempotency_key = str(uuid.uuid4())  # Gere um ID único

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": idempotency_key
    }

    print("📤 Enviando payload para Mercado Pago:")
    print(payload)

    response = requests.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers)

    print(f"📥 Resposta Mercado Pago: {response.status_code}")
    print("🧾 Conteúdo da resposta:")
    print(response.text)

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

    print("🔔 Webhook recebido:", dados)

    if (
        dados.get("type") == "payment"
        and dados.get("action") == "payment.created"
        and dados.get("data")
    ):
        payment_id = dados["data"]["id"]
        print(f"Pagamento criado: ID {payment_id}")

        pagamento = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        ).json()

        if pagamento.get("status") == "approved":
            print("✅ Pagamento aprovado!")

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    print("🚀 Servidor Flask rodando na porta 8080...")
    app.run(host="0.0.0.0", port=8080)
