# -*- coding: utf-8 -*-

import config

import telebot
import urllib2
import json
import random
from telebot import types
from wordnik import *
#from translate import Translator
from googletrans import Translator
from bs4 import BeautifulSoup

#tg
bot = telebot.TeleBot(config.tgApiKey)

# wordlink
wordLinkUrl = 'http://api.wordnik.com/v4'
wordLinkClient = swagger.ApiClient(config.wordLinkKey, wordLinkUrl)

#buttons
randomWordButtonTag = 'randomWordButtonTag'
exampleButtonTag = 'exampleButtonTag'
dictionaryButtonTag = 'dictionaryButtonTag'
imageButtonTag = 'imageButtonTag'
translationButtonTag = 'translationButtonTag'
xkcdComicsButtonTag = 'xkcdComicsButtonTag'

#button actions
optionButtonActions = {
	exampleButtonTag : (lambda chatContext: 
		bot.send_message(chatContext.chatId, getExample(chatContext.word))
	),
	dictionaryButtonTag : (lambda chatContext:
		bot.send_message(chatContext.chatId, getDictionaryDefinition(chatContext.word))
	),
	imageButtonTag : (lambda chatContext: 
		bot.send_photo(chatContext.chatId, getImageURL(chatContext.word))
	),
	translationButtonTag : (lambda chatContext:
		bot.send_message(chatContext.chatId, getTranslation(chatContext.word))
	) }

#data
currentContexts = {}

class ChatContext:
	word = ""
	chatId = 0
	usedButtonTags = []

	def __init__(self, word, chatId):
		self.word = word
		self.chatId = chatId
		self.usedButtonTags = []


def getRandomWord():
	wordsApi = WordsApi.WordsApi(wordLinkClient)
	wordObj = wordsApi.getRandomWord(hasDictionaryDef = 'true', minCorpusCount = 100000)
	return wordObj.word

def getExample(word):
	wordApi = WordApi.WordApi(wordLinkClient)
	example = wordApi.getTopExample(word = word)
	return example.text

def getDictionaryDefinition(word):
	wordApi = WordApi.WordApi(wordLinkClient)
	definitions = wordApi.getDefinitions(word = word, limit = 1)
	return definitions[0].text

def getTranslation(word):
	result = ""
	try:
#		translator= Translator(to_lang="ru")
#		result = translator.translate(word)
		translator = Translator()
		result = translator.translate(word, src='en', dest='ru').text
	except:
		result = "Ooops! Error =("
	return result


def getImageURL(word):
	result = ""
	try:
		url = "https://www.google.co.in/search?q=" + word + "&source=lnms&tbm=isch"
		header={'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}
		soup = BeautifulSoup(urllib2.urlopen(urllib2.Request(url,headers=header)),'html.parser')
		imageURLs = []
		for a in soup.find_all("div",{"class":"rg_meta"}):
		    link = json.loads(a.text)["ou"]
		    imageURLs.append(link)
		result = imageURLs[0]
	except:
		result = "https://blog.sqlauthority.com/wp-content/uploads/2015/10/errorstop.png"
	return result

def getXKCDImage():
	result = ""
	try:
		comicsId = random.randint(1,1862)
		url = "https://xkcd.com/" + str(comicsId) + "/info.0.json"
		resultJSON = urllib2.urlopen(url).read()
		result = json.loads(resultJSON)['img']
	except:
		result = "https://blog.sqlauthority.com/wp-content/uploads/2015/10/errorstop.png"
	return result

def getOptionsKeyboard(excludedButtonTags):
	keyboard = types.InlineKeyboardMarkup()
	if not exampleButtonTag in excludedButtonTags:
		exampleButton = types.InlineKeyboardButton(text="Example", callback_data=exampleButtonTag)
		keyboard.add(exampleButton)
	if not imageButtonTag in excludedButtonTags:
		imgButton = types.InlineKeyboardButton(text="Image", callback_data=imageButtonTag)	
		keyboard.add(imgButton)
	if not translationButtonTag in excludedButtonTags:
		translationButton = types.InlineKeyboardButton(text="Translation", callback_data=translationButtonTag)
		keyboard.add(translationButton)
	if not dictionaryButtonTag in excludedButtonTags:
		dictButton = types.InlineKeyboardButton(text="Dictionary definition", callback_data=dictionaryButtonTag)
		keyboard.add(dictButton)
	return keyboard

def updateOptionsKeyboard(message, chatContext):
	bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=chatContext.word, reply_markup=getOptionsKeyboard(chatContext.usedButtonTags))


@bot.message_handler(content_types=["text"])
def handleMessage(message):
	keyboard = types.InlineKeyboardMarkup()
	randomWordButton = types.InlineKeyboardButton(text="Give me random word", callback_data=randomWordButtonTag)
	xkcdComics = types.InlineKeyboardButton(text="Give me XKCD comics", callback_data=xkcdComicsButtonTag)
	keyboard.add(randomWordButton, xkcdComics)

	bot.send_message(message.chat.id, "Please, select an option", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handleCallback(call):
	if call.message:
		buttonTag = call.data
		if buttonTag == randomWordButtonTag:
			word = getRandomWord()
			context = ChatContext(word, call.message.chat.id)
			currentContexts[call.message.chat.id] = context

			print("selected word: {" + word + "} for chat: " + call.message.chat.first_name)

			updateOptionsKeyboard(call.message, context)
		if buttonTag == xkcdComicsButtonTag:
			print("selected xkcd")
			bot.send_photo(call.message.chat.id, getXKCDImage())
		elif call.message.chat.id in currentContexts:
			chatContext = currentContexts[call.message.chat.id]
			chatContext.usedButtonTags.append(buttonTag)
			updateOptionsKeyboard(call.message, chatContext)

			print("chat id = " + str(call.message.chat.id))
			print("selected option: {" + buttonTag + "} for word: " + chatContext.word)

			action = optionButtonActions[buttonTag]
			action(chatContext)


if __name__ == '__main__':
     bot.polling(none_stop=True)
