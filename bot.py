# -*- coding: utf-8 -*-

import config

import telebot
import urllib2
import json
import time
import sys
import random
import giphypop
import traceback
from wikiapi import WikiApi
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
randomWordButtonTag = 'Random Word'
randomWikiButtonTag = 'English Wikipedia'
randomSimpleWikiButtonTag = 'Simple English Wikipedia'
xkcdComicsButtonTag = 'Random XKCD Comics'
gifButtonTag = 'Random GIF'
dismissButtonTag = 'Dismiss'

exampleButtonTag = 'Example'
wikiButtonTag = 'Wikipedia'
dictionaryButtonTag = 'Dictionary Definition'
imageButtonTag = 'Image'
audioButtonTag = 'Audio'
translationButtonTag = 'Translation'

#data
currentContexts = {}

#button actions
optionButtonActions = {
	xkcdComicsButtonTag : (lambda chatContext: 
		bot.send_photo(chatContext.chatId, getXKCDImage())
	),
	gifButtonTag : (lambda chatContext: 
		giphyButtonAction(chatContext)
	),
	randomWikiButtonTag : (lambda chatContext: 
		randomWikiButtonAction(chatContext, simplified = False)
	),
	randomSimpleWikiButtonTag : (lambda chatContext: 
		randomWikiButtonAction(chatContext, simplified = True)
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
	wikiButtonTag : (lambda chatContext:
		wikiButtonAction(chatContext)
	),
	imageButtonTag : (lambda chatContext: 
		imageButtonAction(chatContext)
	),
	audioButtonTag : (lambda chatContext: 
		audioButtonAction(chatContext)
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

	def clean(self):
		self.examples = []
		self.imageURLs = []
		self.definitions = []

		self.exampleCounter = 0
		self.imageURLsCounter = 0
		self.definitionsCounter = 0		

	def getNextIndex(self, array, currentIndex):
		if currentIndex + 1 >= len(array):
			return 0
		return currentIndex + 1

	def getNextImageURL(self):
		self.imageURLsCounter = self.getNextIndex(self.imageURLs, self.imageURLsCounter)
		return self.imageURLs[self.imageURLsCounter]

	def getNextExample(self):
		self.exampleCounter = self.getNextIndex(self.examples, self.exampleCounter)
		return self.examples[self.exampleCounter]

	def getNextDefinition(self):
		self.definitionsCounter = self.getNextIndex(self.definitions, self.definitionsCounter)
		return self.definitions[self.definitionsCounter]

# logic
def getRandomWord():
	# This piece of shit - WordsApi has a bug: it encodes CSV params twice! So, we can't use multiple values in includePartOfSpeech
	wordObj = WordsApi.WordsApi(wordLinkClient).getRandomWord(hasDictionaryDef = 'true', minCorpusCount = 100000, includePartOfSpeech = "noun")

	# Also, this piece of shit - Wordnik - returns PLURALS. So, make a hack to avoid them
	canonicalWordObj = WordApi.WordApi(wordLinkClient).getWord(word = wordObj.word, useCanonical = 'true')
	return canonicalWordObj.canonicalForm or canonicalWordObj.word

def getExamples(word):
	example = WordApi.WordApi(wordLinkClient).getExamples(word = word)
	return example.examples

def getDictionaryDefinitions(word):
	definitions = WordApi.WordApi(wordLinkClient).getDefinitions(word = word)
	return definitions

def getTranslation(word):
	result = ""
	try:
		translator = Translator()
		result = translator.translate(word, src='en', dest='ru').text
	except:
		result = "Ooops! Error =("
	return result

def getWikiArticle(word, locale):
	wiki = WikiApi({ 'locale' : locale})
	results = wiki.find(word)
	result = next(iter(results or []), None)
	return wiki.get_article(result) if result else None

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

def getAudioURL(word):
	audios = WordApi.WordApi(wordLinkClient).getAudio(word = word, useCanonical = 'true', limit = 1)
	audio = next(iter(audios or []), None)
	return audio.fileUrl if audio else None

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

def getGiphy():
	giphy = giphypop.Giphy()
	res = giphy.screensaver()
	print(res.url)
	return res.media_url

def getRandomWikiArticle(simplified):
	word = getRandomWord()
	locale = 'simple' if simplified else 'en'
	return getWikiArticle(word, locale) 

# button actions
def giphyButtonAction(chatContext):
	bot.send_chat_action(chatContext.chatId, "upload_photo")
	return bot.send_document(chatContext.chatId, getGiphy())

def imageButtonAction(chatContext):
	bot.send_chat_action(chatContext.chatId, "upload_photo")
	if not chatContext.imageURLs:
		chatContext.imageURLs = getImageURLs(chatContext.word)
	return bot.send_photo(chatContext.chatId, chatContext.getNextImageURL())

def audioButtonAction(chatContext):
	audioURL = getAudioURL(chatContext.word)
	if audioURL:
		return bot.send_voice(chatContext.chatId, audioURL)
	else :
		return bot.send_message(chatContext.chatId, "Sorry, no audio for " + chatContext.word)

def exampleButtonAction(chatContext):
	if not chatContext.examples:
		chatContext.examples = getExamples(chatContext.word)
	example = chatContext.getNextExample()

	formattedWord = "<b>" + chatContext.word + "</b>"
	formattedMessage = example.text
	formattedTitle = "<i>" + example.title + "</i>"
	formattedURL = "<a href=\"" + example.url + "\">" + example.url + "</a>"
	message = formattedWord + "\n" + formattedMessage + "\n" + formattedTitle + "\n" + formattedURL
	return bot.send_message(chatContext.chatId, message, parse_mode = "HTML")

def definitionButtonAction(chatContext):
	if not chatContext.definitions:
		chatContext.definitions = getDictionaryDefinitions(chatContext.word)
	definition = chatContext.getNextDefinition()

	formattedWord = "<b>" + chatContext.word + "</b>"
	formattedMessage = definition.text
	formattedTitle = "<i>" + definition.attributionText + "</i>"
	message = formattedWord + "\n" + formattedMessage + "\n" + formattedTitle
	return bot.send_message(chatContext.chatId, message, parse_mode = "HTML")

def wikiButtonAction(chatContext):
	article = getWikiArticle(chatContext.word, 'simple')
	if article:
		formattedWord = "<b>" + chatContext.word + "</b>"
		formattedMessage = article.summary
		formattedURL = "<a href=\"" + article.url + "\">" + article.url + "</a>"
		message = formattedWord + "\n" + formattedMessage + "\n" + formattedURL
		return bot.send_message(chatContext.chatId, message, parse_mode = "HTML")
	else:
		return bot.send_message(chatContext.chatId, "Sorry, no results for " + chatContext.word)

def randomWikiButtonAction(chatContext, simplified):
	article = getRandomWikiArticle(simplified)
	if article:
		formattedWord = "<b>" + article.heading + "</b>"
		formattedMessage = article.summary
		formattedURL = "<a href=\"" + article.url + "\">" + article.url + "</a>"
		message = formattedWord + "\n" + formattedMessage + "\n" + formattedURL
		return bot.send_message(chatContext.chatId, message, parse_mode = "HTML")
	else:
		return randomWikiButtonAction(chatContext, simplified)

def dismissButtonAction(chatContext):
	msg = bot.send_message(chatContext.chatId, "Dismiss", reply_markup = types.ReplyKeyboardRemove())
	del currentContexts[chatContext.chatId]
	return msg

# stuff
def getOptionsKeyboard():
	keyboard = types.ReplyKeyboardMarkup()
	keyboard.row(dictionaryButtonTag)
	keyboard.row(wikiButtonTag)
	keyboard.row(audioButtonTag)
	keyboard.row(translationButtonTag)
	keyboard.row(imageButtonTag)
	keyboard.row(exampleButtonTag)
	keyboard.row(randomWordButtonTag)
	keyboard.row(dismissButtonTag)
	return keyboard

def handleMenu(message):
	buttonTag = message.text
	chatContext = currentContexts[message.chat.id]
	if buttonTag == randomWordButtonTag:
		word = getRandomWord()
		chatContext.word = word
		chatContext.clean()

		print("selected word: {" + word + "} for chat: " + message.chat.first_name)
		msg = bot.send_message(message.chat.id, "*"+word+"*", parse_mode = "Markdown", reply_markup = getOptionsKeyboard())
		# TODO: USe lambda here do distinguish buttons later!
		bot.register_next_step_handler(msg, handleMenu)
	elif buttonTag in optionButtonActions:
		print("chatId: {" + message.chat.first_name + "} selected option: {" + buttonTag + "} for word: " + chatContext.word)

		action = optionButtonActions[buttonTag]
		msg = action(chatContext)
		# TODO: USe lambda here do distinguish buttons later!
		bot.register_next_step_handler(msg, handleMenu)

@bot.message_handler(commands=['word'])
def handleWordCommand(message):
	word = message.text.split("/word", 1)[1].strip()
	if not word:
		return
	
	print (word)
	chatId = message.chat.id
	context = None
	if not chatId in currentContexts:
		context = ChatContext(chatId)
		currentContexts[chatId] = context
	else:
		context = currentContexts[chatId]
	context.word = word
	context.clean()

	print("selected CUSTOM word: {" + word + "} for chat: " + message.chat.first_name)
	msg = bot.send_message(chatId, "*"+word+"*", parse_mode = "Markdown", reply_markup = getOptionsKeyboard())
	# TODO: USe lambda here do distinguish buttons later!
	bot.register_next_step_handler(msg, handleMenu)

@bot.message_handler(content_types=["text"])
def handleMessage(message):
	chatId = message.chat.id
	if not chatId in currentContexts:
		keyboard = types.ReplyKeyboardMarkup()
		keyboard.row(randomWordButtonTag)
		keyboard.row(randomWikiButtonTag)
		keyboard.row(randomSimpleWikiButtonTag)
		keyboard.row(gifButtonTag)
		keyboard.row(xkcdComicsButtonTag)
		keyboard.row(dismissButtonTag)
		
		context = ChatContext(chatId)
		currentContexts[chatId] = context

		msg = bot.send_message(chatId, "Please, select an option", reply_markup=keyboard)
		# TODO: USe lambda here do distinguish buttons later!
		bot.register_next_step_handler(msg, handleMenu)

if __name__ == '__main__':
	while True:
		try:
			bot.polling(none_stop=True)
		except:
			T, V, TB = sys.exc_info()
  			print(''.join(traceback.format_exception(T,V,TB)))
			time.sleep(5)
