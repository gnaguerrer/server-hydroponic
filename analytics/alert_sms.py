import os
from twilio.rest import Client

account_sid = os.environ.get('account_sid')
auth_token = os.environ.get('auth_token')

client = Client(account_sid, auth_token)

def send_alert_sms(message_text):
    message = client.messages.create(
                from_='+15673687109',
                body=message_text,
                to='+573505034166'
    )
    print(message.sid, flush=True)
