#!/usr/bin/env python3

# From: https://github.com/masnun/fb-bot/blob/master/server.py

from flask import Flask, request
from fbchatbot import FBChatBot, Nlp
import requests
import urllib.parse
import json
import os
from llm import ShoppingLLM

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("TOKEN")
#TODO add in required export for OPENAI_API_KEY



APP_NAME = "ELSA"

class MyChatBot(FBChatBot):
    def __init__(self, access_token, verify_token):
        super().__init__(access_token, verify_token)
        self.shopping_llm = ShoppingLLM()

    def process_text(self, user, text, nlp = Nlp.NONE):
        app.logger.debug("Received text: %s, nlp: %x" % (text, nlp))

        if text == "lol":
            self.reply(user, "")
            return
        elif text == "start over":
            user.response = None
            user.query = None
            user.category = None
            user.store = None
            user.product = None
            user.receipt = None
            self.reply(user, "")
            return
        

        raw_output, structured_output = self.shopping_llm.get_output(text)
        app.logger.debug("structured output of the shopping llm %s" % str(structured_output))
        print("*"*100)
        print(raw_output)
        print("$"*100)
        print(structured_output)
        print("*"*100)
        user.query = structured_output["product"]
        user.store = structured_output["store"]
        user.category = structured_output["category"]
        
        # user.query = "red nike tennis shoes"
        # user.store = "nike"
        # user.category = "shoes"
        # user.category = "shoes"
        user.category = None 
        #TODO whenever category was set to anything besides None, the product results from the query were coming back as length 0
        #TODO that's why it is set to None atm. Fixes not very difficult, just need to inspect API will be added in the next version.
        user.product = None
        user.receipt = None

        if user.store == None:
            self.reply(user, raw_output)
        else:
            user.response = self.query(user)
            if user.response == None:
                app.logger.error("Failed to query: %s", text)
                self.reply(user,
                            "Couldn't find any.  Please try other items.")
                return

            products = []
            for product in user.response["data"]["searchProduct"]["products"]:
                if product["availability"]:
                    products.append({
                        "title": product["title"],
                        "subtitle": product["currency"] + str(product["priceCurrent"] / 100),
                        "item_url": product["imageUrlPrimary"],
                        "image_url": product["imageUrlPrimary"],
                        "buttons": [{
                            "type": "web_url",
                            "url": "https://www.joinhoney.com/shop/" + product["store"]["label"] + "/p/" + product["productId"],
                            "title": "Buy"
                        }]
                    })

            # Truncate the array to 10, a limitation of quick reply.
            del(products[10:])
            app.logger.debug("product size %d" % len(products))
            self.generic_reply(user, "Choose your item, please!", products)


    def query(self, user):
        variables = {
            "query": urllib.parse.quote_plus(user.query),
            "meta": {
                "limit": 10,
                "offset": 0
            }
        }

        if user.category:
            variables["meta"]["categories"] = urllib.parse.quote_plus(user.category)

        # XXX: Need to find out the store API.
        #if user.store:
        #    variables["meta"]["stores"] = urllib.parse.quote_plus(user.store)

        query = "https://d.joinhoney.com/v3?operationName=searchProduct&variables=%s" % str(variables).replace("'", "\"").replace(" ", "")
        app.logger.debug("Query: %s" % query)

        r = requests.get(query)
        if r.status_code != requests.codes.ok:
            return None
        else:
            return r.json()


chatbot = MyChatBot(ACCESS_TOKEN, VERIFY_TOKEN)

# Flask's routing

@app.route('/webhook', methods=['GET'])
def handle_verification():
    return chatbot.verify(request.args)

@app.route('/webhook', methods=['POST'])
def handle_incoming_messages():
    app.logger.debug("Received: %s" % json.dumps(request.json, indent=2))
    chatbot.process(request.json)
    return "OK"

# Main function

if __name__ == '__main__':
    app.run(debug=True, port = 5000)
