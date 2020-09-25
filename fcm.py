
import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

def sendPush(title, msg, token):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=msg
        ),
        token = token
    )

    response = messaging.send(message)
    print(response)

sendPush("hi", "this is message", "fFVa9HK8R9qz1oAUqR-Mjs:APA91bGJ0DAllWR6mp5s8wb-6hlDNU-JUZnZHRvc_yu0wFkmkCeLC6ojAD2erIfkhBjoQq_2KfLxdCTh-dng3VOpXXUQ7CJYGKifPkJM6SuOZIUEv0_yMCDsgy4ocsKUM0GKgBO8L2QB")