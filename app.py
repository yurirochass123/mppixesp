from flask import Flask, request, jsonify
import requests
import os
import uuid
import time
import paho.mqtt.client as mqtt
import ssl

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
MQTT_BROKER = "0ea2697a3d79439dbfd101a6f7896593.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "esp32_user"
MQTT_PASS = "Esp32_pass"
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
        and dados.get("action") in ["payment.created", "payment.updated"]
        and dados.get("data")
    ):
        payment_id = dados["data"]["id"]
        print(f"💳 Pagamento recebido: ID {payment_id}")

        try:
            pagamento = requests.get(
                f"https://api.mercadopago.com/v1/payments/{payment_id}",
                headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
            ).json()

            status = pagamento.get("status")
            print(f"📦 Status atual: {status}")

            if status == "approved":
                print("✅ Pagamento aprovado! Enviando via MQTT...")
                try:
                    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                    client.username_pw_set(MQTT_USER, MQTT_PASS)
                    client.tls_set(cert_reqs=ssl.CERT_NONE)  # Para teste, use CERT_REQUIRED em produção
                    client.connect(MQTT_BROKER, MQTT_PORT, 60)

                    client.loop_start()
                    result = client.publish(MQTT_TOPIC, "LIBERAR_AGUA")
                    print("📤 Resultado do publish:", result)

                    time.sleep(1)  # Garante que a mensagem seja enviada antes do disconnect
                    client.loop_stop()
                    client.disconnect()
                    print("🚰 Mensagem MQTT enviada com sucesso!")

                except Exception as e:
                    print("❌ Erro ao enviar MQTT:", e)

        except Exception as e:
            print("❌ Erro ao consultar pagamento:", e)

    return jsonify({"status": "ok"}), 200


@app.route("/", methods=["GET"])
def hello():
    return "Servidor Pix com MQTT ativo 🚰", 200

if __name__ == "__main__":
    print("🚀 Servidor Flask rodando na porta 8080...")
    app.run(host="0.0.0.0", port=8080)
