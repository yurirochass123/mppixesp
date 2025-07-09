from flask import Flask, request, jsonify
import requests
import os
import uuid
import paho.mqtt.client as mqtt

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "solidus/pix/confirmado"

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

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4())
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
        print(f"💳 Pagamento criado: ID {payment_id}")

        pagamento = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        ).json()

        if pagamento.get("status") == "approved":
            print("✅ Pagamento aprovado! Enviando via MQTT...")
            try:
                client = mqtt.Client()
                client.connect(MQTT_BROKER, MQTT_PORT, 60)
                client.publish(MQTT_TOPIC, "LIBERAR_AGUA")
                client.disconnect()
                print("🚰 Mensagem MQTT enviada com sucesso!")
            except Exception as e:
                print("❌ Erro ao enviar MQTT:", e)

    return jsonify({"status": "ok"}), 200


@app.route("/", methods=["GET"])
def hello():
    return "Servidor Pix com MQTT ativo 🚰", 200

if __name__ == "__main__":
    print("🚀 Servidor Flask rodando na porta 8080...")
    app.run(host="0.0.0.0", port=8080)
