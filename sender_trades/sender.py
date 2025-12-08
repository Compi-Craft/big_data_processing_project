from kafka import KafkaProducer
import logging
import time
from websocket import WebSocketApp
import json

# WAIT FOR KAFKA
time.sleep(10)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def on_message(ws, message):
    data = json.loads(message)

    if "action" in data.keys() and data['action'] == "insert":
        logger.info(f"Sent to Kafka: {data}")
        producer.send('trades', value=data)

def on_error(ws, error):
    logger.error(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    logger.info("WebSocket closed")

def on_open(ws):
    subscribe_message = {
        "op": "subscribe",
        "args": [
            "trade:XBTUSDT",
            "trade:ETHUSDT",
            "trade:SOLUSDT",
            "trade:XRPUSDT",
            "trade:LINKUSDT",
        ]
    }
    ws.send(json.dumps(subscribe_message))
    logger.info("WebSocket connection opened!")

if __name__ == "__main__":
    while True:
        try:
            ws = WebSocketApp(
                "wss://www.bitmex.com/realtime",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            ws.run_forever()
        except Exception:
            print("Connection Lost, restart")
            time.sleep(5)

