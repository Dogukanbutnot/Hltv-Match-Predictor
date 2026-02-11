import telegram.ext
import telegram

with open("token.txt","r") as f:
    TOKEN =f.read()
    
def start(update,source):
    update.message.reply_text("Merhaba")
    
update = telegram.ext.Updater(TOKEN,use_context =True)
disp = update.dispatcher

disp.add_handler(telegram.ext.Commandhandler("start",start))

update.start_polling()
update.idle()        