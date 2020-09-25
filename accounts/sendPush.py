import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging

cred = credentials.Certificate('serviceAccountKey.json')
default_app = firebase_admin.initialize_app(cred)

def sendPush(title, msg, token, name):
    message = messaging.Message(
        android=messaging.AndroidConfig(
            notification=messaging.AndroidNotification(
                title=title,
                body=msg,
                tag=name,
            ),
        ),
        #topic=topic,
        token=token
    )
    messaging.send(message)
