# encoding: utf-8

import re
import os
from urllib.parse import quote
import webbrowser
import random

from aqt import mw
from aqt.utils import tooltip, getText
from anki.hooks import addHook
from aqt.reviewer import Reviewer
from aqt.qt import QKeySequence, Qt

OPEN_DICT = "Alt+V"
OPEN_DICT_KANA = "Alt+F"
OPEN_WEB_DICT = "Alt+A"
OPEN_WEB_DICT_AUDIO = "Alt+Z"
EDIT_AUDIO = "Alt+X"
EDIT_SENTENCE_AUDIO = "Alt+S"
OPEN_GOOGLE = "Alt+Q"
ADD_REQ_NOTICE = "Alt+C"
ADD_CHECK_NOTICE = "Alt+D"
CLEAR_NOTICE = "Alt+E"
ARROW_UP = "Up"
ARROW_LEFT = "Left"
ARROW_RIGHT = "Right"
ARROW_DOWN = "Down"
TOGGLE_TITLE_BAR = "Alt+B"
RESCHEDULE = "Alt+R"
RESCHEDULE_LEVEL1 = "Shift+Z"
RESCHEDULE_LEVEL2 = "Shift+X"
RESCHEDULE_LEVEL3 = "Shift+C"
RESCHEDULE_LEVEL4 = "Shift+B"
RESCHEDULE_TOMORROW = "Shift+A"

DICT_URL = "http://localhost:8889/static/dm/index.html#/ja/pc"

AUTOSYNC_IDLE_PERIOD = 20
AUTOSYNC_RETRY_PERIOD = 2

def openDict(note, kana=False):
    if kana and 'kana' in note:
        os.system('open dict:///' + note['kana'])
    elif 'word' in note:
        os.system('open dict:///"' + note['word'] + '"')

def openWebDict(note, only_audio=False):
    if 'word' not in note:
        return
    word = note['word']
    url = DICT_URL + '?word=' + quote(word.encode('utf8'))
    if only_audio:
        url += '&onlyAudio=true'
    if 'audio' in note:
        audio = note['audio']
        match = re.search("\[sound:(.*?)\.mp3\]", audio)
        if match:
            audio_name = match.group(1)
            os.system("echo '%s' | tr -d '\n'| pbcopy" % audio_name)
    webbrowser.open(url)

def editAudio(note, sentence=False):
    if 'audio' not in note:
        return
    audio = note['sentence-audio' if sentence else 'audio']
    match = re.search("\[sound:(.*?)\]", audio)
    if match:
        audio_file = mw.col.media.dir().replace(' ', '\ ') + '/' + match.group(1)
        # print('open -a /Applications/Audacity.app ' + audio_file)
        os.system('open -a /Applications/Audacity.app ' + audio_file)

def openGoogle(note):
    if 'word' not in note:
        return
    word = note['word']
    url = 'https://www.google.co.jp/search?q={}'.format(quote(word))
    webbrowser.open(url)

def setNotice(note, context):
    if 'notice' in note:
        note['notice'] = context
        note.flush()

def menuAction(self, params):
    if not self.card:
        return
    note = self.card.note()
    if params['type'] == 'dict':
        openDict(note, params['kana'])
    elif params['type'] == 'web_dict':
        openWebDict(note, params['only_audio'])
    elif params['type'] == 'audio':
        editAudio(note, params['sentence'])
    elif params['type'] == 'google':
        openGoogle(note)
    elif params['type'] == 'notice':
        setNotice(note, params['context'])

def arrow_handler(self, key):
    cnt = mw.col.sched.answerButtons(mw.reviewer.card)
    if key == 'up':
        if self.state == "answer" and cnt == 4:
            self._answerCard(2)
    elif key == 'left':
        if self.state == "question":
            self.onEnterKey()
        elif self.state == "answer":
            self._answerCard(1)
    elif key == 'right':
        if self.state == "question":
            self.onEnterKey()
        elif self.state == "answer":
            self._answerCard(2 if cnt <= 3 else 3)
    elif key == 'down':
        self.replayAudio()

def toggle_title_bar():
    if mw.windowFlags() & Qt.FramelessWindowHint:
        mw.setWindowFlags(Qt.Window)
    else:
        mw.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
    mw.show()

def reschedule(self, level=None):
    if level is None:
        dayString = getText("Number of days until next review: ")
        try:
            days = int(dayString[0])
        except ValueError:
            return
    elif type(level) == int:
        # level 1 : 5, 35
        # level 2 : 35, 65
        # level 3 : 65, 95
        # level 4 : 95, 125
        days = random.randint(5 + (level - 1) * 30, 5 + level * 30)
    elif level == 'tomorrow':
        days = 1
    else:
        return

    card = self.reviewer.card
    if days > 0:
        self.checkpoint(_("Reschedule card"))
        self.col.sched.reschedCards([card.id], days, days)
        tooltip('Rescheduled for review in ' + str(days) + ' days')
        self.reset()

class AutoSync:

    def syncDecks(self):
        """Force sync if in any of the below states"""
        self.timer = None
        # if mw.state in ["deckBrowser", "overview", "review"]:
        if mw.state in ["overview", "review"]:
            mw.onSync()
        else:
            # Not able to sync. Wait another 2 minutes
            self.startSyncTimer(self.retryPeriod)

    def startSyncTimer(self, minutes):
        """Start/reset the timer to sync deck"""
        if self.timer is not None:
            self.timer.stop()
        self.timer = mw.progress.timer(
            1000 * 60 * minutes, self.syncDecks, False)

    def resetTimer(self, minutes):
        """Only reset timer if the timer exists"""
        if self.timer is not None:
            self.startSyncTimer(minutes)

    def stopTimer(self):
        if self.timer is not None:
            self.timer.stop()
        self.timer = None

    def updatedHook(self, *args):
        """Start/restart timer to trigger if idle for a certain period"""
        self.startSyncTimer(self.idlePeriod)

    def activityHook(self, *args):
        """Reset the timer if there is some kind of activity"""
        self.resetTimer(self.idlePeriod)

    def syncHook(self, state):
        """Stop the timer if synced via other methods"""
        if state == "login":
            self.stopTimer()

    def __init__(self):
        self.idlePeriod = AUTOSYNC_IDLE_PERIOD
        self.retryPeriod = AUTOSYNC_RETRY_PERIOD
        self.timer = None

        updatedHooks = [
            "showQuestion",
            "reviewCleanup",
            "editFocusGained",
            "noteChanged",
            "reset",
            "tagsUpdated"
        ]

        activtyHooks = [
            "showAnswer",
            "newDeck"
        ]

        for hookName in updatedHooks:
            addHook(hookName, self.updatedHook)

        for hookName in activtyHooks:
            addHook(hookName, self.activityHook)

        addHook("sync", self.syncHook)


def onSetupMenus(self):
    menu = self.form.menuEdit
    menu.addSeparator()
    a = menu.addAction('Open Dict')
    a.setShortcut(QKeySequence(OPEN_DICT))
    a.triggered.connect(lambda: menuAction(self, dict(type='dict', kana=False)))
    a = menu.addAction('Open Dict (kana)')
    a.setShortcut(QKeySequence(OPEN_DICT_KANA))
    a.triggered.connect(lambda: menuAction(self, dict(type='dict', kana=True)))
    a = menu.addAction('Open Web Dict')
    a.setShortcut(QKeySequence(OPEN_WEB_DICT))
    a.triggered.connect(lambda: menuAction(self, dict(type='web_dict', only_audio=False)))
    a = menu.addAction('Open Web Dict (Only Audio)')
    a.setShortcut(QKeySequence(OPEN_WEB_DICT_AUDIO))
    a.triggered.connect(lambda: menuAction(self, dict(type='web_dict', only_audio=True)))
    a = menu.addAction('Edit Audio')
    a.setShortcut(QKeySequence(EDIT_AUDIO))
    a.triggered.connect(lambda: menuAction(self, dict(type='audio', sentence=False)))
    a = menu.addAction('Edit Sentence Audio')
    a.setShortcut(QKeySequence(EDIT_SENTENCE_AUDIO))
    a.triggered.connect(lambda: menuAction(self, dict(type='audio', sentence=True)))
    a = menu.addAction('Open Google')
    a.setShortcut(QKeySequence(OPEN_GOOGLE))
    a.triggered.connect(lambda: menuAction(self, dict(type='google')))
    a = menu.addAction('Add requesting to notice')
    a.setShortcut(QKeySequence(ADD_REQ_NOTICE))
    a.triggered.connect(lambda: menuAction(self, dict(type='notice', context='requesting')))
    a = menu.addAction('Add checked to notice')
    a.setShortcut(QKeySequence(ADD_CHECK_NOTICE))
    a.triggered.connect(lambda: menuAction(self, dict(type='notice', context='checked')))
    a = menu.addAction('Clear notice')
    a.setShortcut(QKeySequence(CLEAR_NOTICE))
    a.triggered.connect(lambda: menuAction(self, dict(type='notice', context='')))

def shortcutKeys(self, old_func):
    res = old_func(self)
    mw = self.mw
    reviewer = mw.reviewer
    res.append((OPEN_DICT, lambda: menuAction(reviewer, dict(type='dict', kana=False))))
    res.append(('_', lambda: menuAction(reviewer, dict(type='dict', kana=False))))
    res.append((OPEN_DICT_KANA, lambda: menuAction(reviewer, dict(type='dict', kana=True))))
    res.append((OPEN_WEB_DICT, lambda: menuAction(reviewer, dict(type='web_dict', only_audio=False))))
    res.append((OPEN_WEB_DICT_AUDIO, lambda: menuAction(reviewer, dict(type='web_dict', only_audio=True))))
    res.append((EDIT_AUDIO, lambda: menuAction(reviewer, dict(type='audio', sentence=False))))
    res.append((EDIT_SENTENCE_AUDIO, lambda: menuAction(reviewer, dict(type='audio', sentence=True))))
    res.append((OPEN_GOOGLE, lambda: menuAction(reviewer, dict(type='google'))))
    res.append((ADD_REQ_NOTICE, lambda: menuAction(reviewer, dict(type='notice', context='requesting'))))
    res.append((ADD_CHECK_NOTICE, lambda: menuAction(reviewer, dict(type='notice', context='checked'))))
    res.append((CLEAR_NOTICE, lambda: menuAction(reviewer, dict(type='notice', context=''))))
    res.append((ARROW_UP, lambda: arrow_handler(reviewer, 'up')))
    res.append((ARROW_LEFT, lambda: arrow_handler(reviewer, 'left')))
    res.append((ARROW_RIGHT, lambda: arrow_handler(reviewer, 'right')))
    res.append((ARROW_DOWN, lambda: arrow_handler(reviewer, 'down')))
    res.append((TOGGLE_TITLE_BAR, toggle_title_bar))
    res.append((RESCHEDULE, lambda: reschedule(mw)))
    res.append((RESCHEDULE_LEVEL1, lambda: reschedule(mw, 1)))
    res.append((RESCHEDULE_LEVEL2, lambda: reschedule(mw, 2)))
    res.append((RESCHEDULE_LEVEL3, lambda: reschedule(mw, 3)))
    res.append((RESCHEDULE_LEVEL4, lambda: reschedule(mw, 4)))
    res.append((RESCHEDULE_TOMORROW, lambda: reschedule(mw, 'tomorrow')))
    return res

addHook("browser.setupMenus", onSetupMenus)
old_func = Reviewer._shortcutKeys
Reviewer._shortcutKeys = lambda self: shortcutKeys(self, old_func)
AutoSync()
