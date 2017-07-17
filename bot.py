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
		exampleButtonAction(chatContext)
	),
	dictionaryButtonTag : (lambda chatContext:
		definitionButtonAction(chatContext)
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
	imageURLs = []
	examples = []
	definitions = []

	imageURLsCounter = 0
	exampleCounter = 0
	definitionsCounter = 0

	def __init__(self, chatId):
		self.word = ""
		self.chatId = chatId

		self.examples = []
		self.imageURLs = []
		self.definitions = []

		self.exampleCounter = 0
		self.imageURLsCounter = 0
		self.definitionsCounter = 0

	def getNextImageURL(self):
		url = self.imageURLs[self.imageURLsCounter]
		if self.imageURLsCounter + 1 >= len(self.imageURLs):
			self.imageURLsCounter = 0
		else:
			self.imageURLsCounter += 1
		return url

	def getNextExample(self):
		example = self.examples[self.exampleCounter]
		if self.exampleCounter + 1 >= len(self.examples):
			self.exampleCounter = 0
		else:
			self.exampleCounter += 1
		return example

	def getNextDefinition(self):
		definition = self.definitions[self.definitionsCounter]
		if self.definitionsCounter + 1 >= len(self.definitions):
			self.definitionsCounter = 0
		else:
			self.definitionsCounter += 1
		return definition

# logic
def getRandomWord():
	wordsApi = WordsApi.WordsApi(wordLinkClient)
	#,adjective,verb,adverb
	wordObj = wordsApi.getRandomWord(hasDictionaryDef = 'true', minCorpusCount = 100000, includePartOfSpeech = 'noun', excludePartOfSpeech = 'noun-plural')
	return wordObj.word

def getExamples(word):
	wordApi = WordApi.WordApi(wordLinkClient)
	example = wordApi.getExamples(word = word)
	return example.examples

def getDictionaryDefinitions(word):
	wordApi = WordApi.WordApi(wordLinkClient)
	definitions = wordApi.getDefinitions(word = word)
	return definitions

def getTranslation(word):
	result = ""
	try:
		translator = Translator()
		result = translator.translate(word, src='en', dest='ru').text
	except:
		result = "Ooops! Error =("
	return result


def getImageURLs(word):
	result = []
	try:
		url = "https://www.google.co.in/search?q=" + word + "&source=lnms&tbm=isch"
		header={'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}
		soup = BeautifulSoup(urllib2.urlopen(urllib2.Request(url,headers=header)),'html.parser')
		imageURLs = []
		for a in soup.find_all("div",{"class":"rg_meta"}):
		    link = json.loads(a.text)["ou"]
		    imageURLs.append(link)
		result = imageURLs
	except:
		result = ["https://blog.sqlauthority.com/wp-content/uploads/2015/10/errorstop.png"]
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
	imageURLs = getImageURLs(chatContext.word)
	if not chatContext.imageURLs:
		chatContext.imageURLs = imageURLs
	return bot.send_photo(chatContext.chatId, chatContext.getNextImageURL())

def exampleButtonAction(chatContext):
	examples = getExamples(chatContext.word)
	if not chatContext.examples:
		chatContext.examples = examples
	example = chatContext.getNextExample()

	formattedWord = "*" + chatContext.word + "*"
	formattedMessage = example.text
	formattedTitle = "_" + example.title + "_"
	formattedURL = "[LINK -> CLICK]" + "(" + example.url + ")"
	message = formattedWord + "\n" + formattedMessage + "\n" + formattedTitle + "\n" + formattedURL
	return bot.send_message(chatContext.chatId, message, parse_mode = "Markdown")

def definitionButtonAction(chatContext):
	definitions = getDictionaryDefinitions(chatContext.word)
	if not chatContext.definitions:
		chatContext.definitions = definitions
	definition = chatContext.getNextDefinition()

	formattedWord = "*" + chatContext.word + "*"
	formattedMessage = definition.text
	formattedTitle = "_" + definition.attributionText + "_"
	message = formattedWord + "\n" + formattedMessage + "\n" + formattedTitle
	return bot.send_message(chatContext.chatId, message, parse_mode = "Markdown")

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
