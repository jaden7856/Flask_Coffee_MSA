from kafka import KafkaConsumer
from datetime import datetime
import threading
import pymysql
import time
import json
import uuid


consumer = KafkaConsumer('new_orders', 
                        bootstrap_servers=["172.19.0.101:9092"], 
                        auto_offset_reset='earliest', 
                        enable_auto_commit=True, 
                        auto_commit_interval_ms=1000, 
                        consumer_timeout_ms=1000)

config = {
    'host': '172.19.0.2',
    'port': 3306,
    'user': 'root',
    'database': 'mydb'
}

conn = pymysql.connect(**config)
cursor = conn.cursor()
sql = '''INSERT INTO delivery_status(delivery_id, order_json, status) VALUES(%s, %s, %s)'''


def fetch_latest_orders(next_call_in):
    next_call_in += 30

    batch = consumer.poll(timeout_ms=100)
    
    if len(batch) > 0:
        for message in list(batch.values())[0]:
            value = message.value.decode()

            delivery_id = str(uuid.uuid4())
            status = 'CONFIRMED'
            
            # db insert
            cursor.execute(sql, [delivery_id, value, status])
            conn.commit()


    threading.Timer(next_call_in - time.time(), 
                    fetch_latest_orders, 
                    [next_call_in]).start()


next_call_in = time.time()
fetch_latest_orders(next_call_in)