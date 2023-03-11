from flask import Flask, request
import requests
from dotenv import load_dotenv
import os
from os.path import join, dirname
from liqpay import LiqPay
import json
import time


app = Flask(__name__)


def get_from_env(key):
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    return os.environ.get(key)  # возвращает ключ


def send_message(chat_id, text):
    method = 'sendMessage'
    token = get_from_env('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)


def create_invoice(data):
    liqpay = LiqPay(get_from_env('PUBLIC_KEY'), get_from_env('PRIVATE_KEY'))
    res = liqpay.api("request", {
        "action": "invoice_bot",
        "version": "3",
        "amount": "12",
        "currency": "UAH",
        "order_id": f"order_id_{data['message']['message_id']}",
        "phone": "380950000001",
        "description": data['message']["chat"]["id"]
    })
    print(res)
    if res['status'] == 'invoice_wait':
        return res['href']
    elif res['status'] == 'error':
        print(res['err_description'])
    else:
        print("Somthing wrong")


def send_pay_button(data):
    invoice_url = create_invoice(data)

    token = get_from_env('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    params = {"chat_id": data['message']["chat"]["id"], "text": "Тестовая оплата",
              "reply_markup": json.dumps({"inline_keyboard": [[{
                  "text": "Оплатить!",
                  "url": f"{invoice_url}"
              }]]})}
    requests.post(url, data=params)


def check_if_successful_payment(data):
    liqpay = LiqPay(get_from_env('PUBLIC_KEY'), get_from_env('PRIVATE_KEY'))
    res = liqpay.api("request", {
        "action": "status",
        "version": "3",
        "order_id": f"order_id_{data['message']['message_id']}"
    })
    print(res["status"])
    print(f"Test_order_id_{data['message']['message_id']}")
    return res["status"]


@app.route("/", methods=['POST'])  # localhost:5000 - на этот адрес телеграмм шлёт свои сообщения
def process():
    print(1)
    print(request)
    if request:
        response = request.json
        # check_if_successful_payment(response):
        # send_message(chat_id, "Оплата прошла успешно!")
        send_pay_button(response)
        print(f"Main_order_id_{response['message']['message_id']}")
        for i in range(3):
            if check_if_successful_payment(response) == "success":
                print("Платеж успешно проведен")
                break
            elif check_if_successful_payment(response) == "invoice_wait":
                print('Ожидание платежа')
            elif check_if_successful_payment(response) == "error":
                print('Ошибка платежа')
            else:
                print("Ошибка запроса информации о платеже")
            time.sleep(60)  # ожидание 3 минуты
        print('Время на оплату платежа вышло')
    else:
        print('Ошибка запроса.')
    print(2)
    return {'ok': True}


if __name__ == '__main__':
    app.run()
