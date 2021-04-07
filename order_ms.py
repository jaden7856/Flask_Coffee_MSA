from flask import Flask, jsonify, request
from datetime import datetime
from flask_restful import reqparse
from kafka import KafkaProducer
import flask_restful
# import mariadb
import pymysql
import json
import uuid


app = Flask(__name__)
# app.config["DEBUG"] = True
api = flask_restful.Api(app)

config = {
    'host': '172.19.0.2',
    'port': 3306,
    'user': 'root',
    'database': 'mydb'
}

@app.route('/')
def index():
    return "Welcome to ORDER Microservice!"


class Order(flask_restful.Resource):
    def __init__(self):
        self.conn = pymysql.connect(**config)
        self.cursor = self.conn.cursor()

        self.producer = KafkaProducer(bootstrap_servers=['172.19.0.101:9092'])
    
    def get(self, user_id):
        # MariaDB = '?'
        # MySQL = '%s'
        sql = '''SELECT user_id, order_id, coffee_name, coffee_price, coffee_qty, ordered_at
                FROM orders WHERE user_id=%s order by id desc
        '''
        self.cursor.execute(sql, [user_id])
        
        result_set = self.cursor.fetchall()

        row_headers = [x[0] for x in self.cursor.description]

        json_data = []
        for result in result_set:
            json_data.append(dict(zip(row_headers, result)))

        return jsonify(json_data)

    def post(self, user_id):
        json_data = request.get_json()
        json_data['user_id'] = user_id
        json_data['order_id'] = str(uuid.uuid4())
        json_data['ordered_at'] = str(datetime.today())

        # DB INSERT
        sql = '''INSERT INTO orders(user_id, order_id, coffee_name, coffee_price, coffee_qty, ordered_at)
                    VALUES(%s, %s, %s, %s, %s, %s)
        '''
        self.cursor.execute(sql, [user_id, 
                            json_data['order_id'],
                            json_data['coffee_name'],
                            json_data['coffee_price'],
                            json_data['coffee_qty'],
                            json_data['ordered_at']
                            ])
        self.conn.commit()

        # producer 인스턴스의 send() 메소드로 json 데이터 전송
        self.producer.send('new_orders', value=json.dumps(json_data).encode())
        self.producer.flush()


        response = jsonify(json_data)
        response.status_code = 201

        return response


class OrderDetail(flask_restful.Resource):
    def get(self, user_id, order_id):
        return {'payload' : user_id, 'order_id' : order_id}


# GET http://127.0.0.1:5000/order-ms/USER0001/orders
# POST http://127.0.0.1:5000/order-ms/USER0001/orders
# GET http://127.0.0.1:5000/order-ms/USER0001/orders/ORD001
api.add_resource(Order, '/order-ms/<string:user_id>/orders')
api.add_resource(OrderDetail, '/order-ms/<string:user_id>/orders/<string:order_id>')


if __name__ == '__main__':
    app.run()