# -*- coding: utf-8 -*-

import config

import telebot
import urllib2
import json
import random
from telebot import types
from wordnik import *
from googletrans import Translator
from bs4 import BeautifulSoup

#tg
bot = telebot.TeleBot(config.tgApiKey)

# wordlink
wordLinkUrl = 'http://api.wordnik.com/v4'
wordLinkClient = swagger.ApiClient(config.wordLinkKey, wordLinkUrl)

#buttons
randomWordButtonTag = 'Give me random word'
xkcdComicsButtonTag = 'Give me XKCD comics'
dismissButtonTag = 'Dismiss'

exampleButtonTag = 'Example'
dictionaryButtonTag = 'Dictionary Definition'
imageButtonTag = 'Image'
translationButtonTag = 'Translation'

#data
currentContexts = {}

#button actions
optionButtonActions = {
	xkcdComicsButtonTag : (lambda chatContext: 
		bot.send_photo(chatContext.chatId, getXKCDImage())
	),
	dismissButtonTag : (lambda chatContext: 
		dismissButtonAction(chatContext)
	),
	exampleButtonTag : (lambda chatContext: 
		bot.send_message(chatContext.chatId, getExample(chatContext.word))
	),
	dictionaryButtonTag : (lambda chatContext:
		bot.send_message(chatContext.chatId, getDictionaryDefinition(chatContext.word))
	),
	imageButtonTag : (lambda chatContext: 
		imageButtonAction(chatContext)
	),
	translationButtonTag : (lambda chatContext:
		bot.send_message(chatContext.chatId, getTranslation(chatContext.word))
	) }


class ChatContext:
	word = ""
	chatId = 0

	def __init__(self, chatId):
		self.word = ""
		self.chatId = chatId

# logic
def getRandomWord():
	wordsApi = WordsApi.WordsApi(wordLinkClient)
	wordObj = wordsApi.getRandomWord(hasDictionaryDef = 'true', minCorpusCount = 100000, includePartOfSpeech = 'noun,adjective,')
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

# button actions
def imageButtonAction(chatContext):
	bot.send_chat_action(chatContext.chatId, "upload_photo")
	return bot.send_photo(chatContext.chatId, getImageURL(chatContext.word))

def dismissButtonAction(chatContext):
	msg = bot.send_message(chatContext.chatId, "Dismiss", reply_markup = types.ReplyKeyboardRemove())
	del currentContexts[chatContext.chatId]
	return msg

# stuff
def getOptionsKeyboard():
	keyboard = types.ReplyKeyboardMarkup()
	keyboard.row(exampleButtonTag)
	keyboard.row(imageButtonTag)
	keyboard.row(translationButtonTag)
	keyboard.row(dictionaryButtonTag)
	keyboard.row(dismissButtonTag)
	return keyboard

def handleMenu(message):
	buttonTag = message.text
	if buttonTag == randomWordButtonTag:
		word = getRandomWord()
		currentContexts[message.chat.id].word = word

		print("selected word: {" + word + "} for chat: " + message.chat.first_name)
		msg = bot.send_message(message.chat.id, "*"+word+"*", parse_mode = "Markdown", reply_markup = getOptionsKeyboard())
		# TODO: USe lambda here do distinguish buttons later!
		bot.register_next_step_handler(msg, handleMenu)
	elif buttonTag in optionButtonActions:
		chatContext = currentContexts[message.chat.id]
		print("chatId: {" + message.chat.first_name + "} selected option: {" + buttonTag + "} for word: " + chatContext.word)

		action = optionButtonActions[buttonTag]
		msg = action(chatContext)
		# TODO: USe lambda here do distinguish buttons later!
		bot.register_next_step_handler(msg, handleMenu)

@bot.message_handler(content_types=["text"])
def handleMessage(message):
	chatId = message.chat.id
	if not chatId in currentContexts:
		keyboard = types.ReplyKeyboardMarkup()
		keyboard.row(randomWordButtonTag)
		keyboard.row(xkcdComicsButtonTag)
		keyboard.row(dismissButtonTag)
		
		context = ChatContext(chatId)
		currentContexts[chatId] = context

		msg = bot.send_message(chatId, "Please, select an option", reply_markup=keyboard)
		# TODO: USe lambda here do distinguish buttons later!
		bot.register_next_step_handler(msg, handleMenu)

if __name__ == '__main__':
     bot.polling(none_stop=True)
