# -*- coding: utf-8 -*-

import config
import telebot

import sys
import traceback

#tg bot. Note: by default it runs with threaded = True. This doesn't work with Flask for some reason
bot = telebot.TeleBot(config.tgApiKey, threaded = False)

def start():
    if config.useWebHooks:
        import flask

        WEBHOOK_URL_BASE = "https://%s" % (config.webHookHost)
        WEBHOOK_URL_PATH = "/%s/" % (config.tgApiKey)

        app = flask.Flask(__name__)

        # Empty webserver index, return nothing, just http 200
        @app.route('/', methods=['GET', 'HEAD'])
        def index():
            return 'Hi!'

        # Process webhook calls
        @app.route(WEBHOOK_URL_PATH, methods=['POST'])
        def webhook():
            if flask.request.headers.get('content-type') == 'application/json':
                json_string = flask.request.get_data().decode('utf-8')
                update = telebot.types.Update.de_json(json_string)
                bot.process_new_updates([update])
                return ''
            else:
                flask.abort(403)

        # Remove webhook, it fails sometimes the set if there is a previous webhook
        bot.remove_webhook()

        # Set webhook
        bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)

    else:
        while True:
            try:
                bot.polling(none_stop=True)
            except:
                T, V, TB = sys.exc_info()
                print(''.join(traceback.format_exception(T,V,TB)))
                time.sleep(5)    
