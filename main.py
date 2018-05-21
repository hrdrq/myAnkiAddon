# encoding: utf-8

import os
import re
import sys
import random
import webbrowser
import urllib

from aqt import mw
from aqt.utils import tooltip, getText
from aqt.reviewer import Reviewer
from aqt.qt import QKeySequence, Qt
from anki.hooks import addHook

reschedule_shortcut = 't'
reschedule_level1 = 'z'
reschedule_level2 = 'x'
reschedule_level3 = 'c'
reschedule_level4 = 'v'
reschedule_tomorrow = '.'
edit_audio = 'o'
edit_sentence_audio = 'i'
view_dict = 'k'
view_dict_only_audio = 'l'
osx_dict = 'j'
osx_dict_kana = 'h'
notice_requesting = '['
notice_checked = ']'
notice_clear = '\''
google = 'g'
hide_title_bar = 'm'

arrow_up_code = 16777235
arrow_down_code = 16777237
arrow_left_code = 16777234
arrow_right_code = 16777236

DICT_URL = "http://localhost:8889/static/dm/index.html#/ja/pc"

AUTOSYNC_IDLE_PERIOD = 20
AUTOSYNC_RETRY_PERIOD = 2


class AutoSync:

    def syncDecks(self):
        """Force sync if in any of the below states"""
        self.timer = None
        if mw.state in ["deckBrowser", "overview", "review"]:
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


def promptNewInterval(self, card):

    dayString = getText("Number of days until next review: ")
    try:
        days = int(dayString[0])
    except ValueError:
        return

    if days > 0:
        mw.col.sched.reschedCards([card.id], days, days)
        tooltip('Rescheduled for review in ' + str(days) + ' days')
        mw.reset()

# replace _keyHandler in reviewer.py to add a keybinding


def newKeyHandler(self, evt):
    key = unicode(evt.text())
    key_code = evt.key()
    # sys.stderr.write("key:"+str(key))
    card = mw.reviewer.card
    cnt = mw.col.sched.answerButtons(mw.reviewer.card)
    if key == reschedule_shortcut:
        mw.checkpoint(_("Reschedule card"))
        promptNewInterval(self, card)

    elif key in [reschedule_level1, reschedule_level2, reschedule_level3, reschedule_level4, reschedule_tomorrow]:
        days = 0
        if key == reschedule_level1:
            # days = random.randint(1,100)
            days = 15
        elif key == reschedule_level2:
            # days = random.randint(101,200)
            days = 30
        elif key == reschedule_level3:
            # days = random.randint(201,300)
            days = 45
        elif key == reschedule_level4:
            # days = random.randint(301,400)
            days = 60
        elif key == reschedule_tomorrow:
            days = 1
        mw.col.sched.reschedCards([card.id], days, days)
        tooltip('Rescheduled for review in ' + str(days) + ' days')
        mw.reset()

    elif key in [edit_audio, edit_sentence_audio]:
        editAudio(card.note(), True if key == edit_sentence_audio else False)
    elif key in [view_dict, view_dict_only_audio]:
        openDict(card.note(), True if key == view_dict_only_audio else False)
    elif key == osx_dict:
        note = self.card.note()
        if 'word' not in note:
            return
        word = note['word']
        os.system('open dict:///' + word.encode('utf8'))
    elif key == osx_dict_kana:
        note = self.card.note()
        if 'kana' not in note:
            return
        kana = note['kana']
        os.system('open dict:///' + kana.encode('utf8'))
    elif key in [notice_requesting, notice_checked, notice_clear]:
        note = card.note()
        setNotice(note, key)
    elif (key_code == arrow_left_code or key_code == arrow_right_code) and self.state == "question":
        self._showAnswerHack()
    elif key_code == arrow_up_code and self.state == "answer" and cnt == 4:
        self._answerCard(2)
    elif key_code == arrow_down_code:
        self.replayAudio()
    elif key_code == arrow_left_code and self.state == "answer":
        self._answerCard(1)
    elif key_code == arrow_right_code and self.state == "answer":
        self._answerCard(2 if cnt <= 3 else 3)
    elif key == google:
        openGoogle(card.note())
    elif key == hide_title_bar:
        if mw.windowFlags() & Qt.FramelessWindowHint:
            mw.setWindowFlags(Qt.Window)
        else:
            mw.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        mw.show()
    else:
        origKeyHandler(self, evt)


def openDict(note, SQ=False):
    if 'word' not in note:
        return
    word = note['word']
    # sys.stderr.write(note['word'])
    url = DICT_URL + '?word=' + urllib.quote(word.encode('utf8'))
    if SQ:
        url += '&onlyAudio=true'
    if 'audio' in note:
        audio = note['audio']
        match = re.search("\[sound:(.*?)\.mp3\]", audio)
        if match:
            audio_name = match.group(1)
        os.system("echo '%s' | tr -d '\n'| pbcopy" % audio_name.encode('utf8'))
    webbrowser.open(url)

def openGoogle(note):
    if 'word' not in note:
        return
    word = note['word']
    # sys.stderr.write(note['word'])
    url = 'https://www.google.co.jp/search?q={}'.format(urllib.quote(word.encode('utf8')))
    webbrowser.open(url)


def editAudio(note, sentence=False):
    if 'audio' not in note:
        return
    audio = note['sentence-audio' if sentence else 'audio']
    match = re.search("\[sound:(.*?)\]", audio)
    if match:
        audio_file = mw.col.media.dir().replace(' ', '\ ') + '/' + match.group(1)
        os.system(
            'open -a /Applications/Audacity.app ' + audio_file.encode('utf8'))


def menuOpenDict(self, SQ):
    if not self.card:
        return
    note = self.card.note()
    openDict(note, SQ)


def menuEditAudio(self, sentence):
    if not self.card:
        return
    note = self.card.note()
    editAudio(note, sentence)

def setNotice(note, key):
    if 'notice' in note:
        notice = note['notice']
        if key == notice_requesting:
            note['notice'] = 'requesting'
        elif key == notice_checked:
            note['notice'] = 'checked'
        elif key == notice_clear:
            note['notice'] = ''
        note.flush()

def menuSetNotice(self, key):
    if not self.card:
        return
    note = self.card.note()
    setNotice(note, key)

def menuOpenGoogle(self):
    if not self.card:
        return
    note = self.card.note()
    openGoogle(note)


def onSetupMenus(self):
    """Create menu entry and set attributes up"""
    menu = self.form.menuEdit
    menu.addSeparator()
    a = menu.addAction('Open Dict')
    a.setShortcut(QKeySequence("Ctrl+K"))
    a.triggered.connect(lambda _, o=self: menuOpenDict(o, False))
    a = menu.addAction('Open Dict (Only Audio)')
    a.setShortcut(QKeySequence("Ctrl+L"))
    a.triggered.connect(lambda _, o=self: menuOpenDict(o, True))
    a = menu.addAction('Edit Audio')
    a.setShortcut(QKeySequence("Ctrl+O"))
    a.triggered.connect(lambda _, o=self: menuEditAudio(o, False))
    a = menu.addAction('Edit Sentence Audio')
    a.setShortcut(QKeySequence("Ctrl+I"))
    a.triggered.connect(lambda _, o=self: menuEditAudio(o, True))
    a = menu.addAction('Add requesting to notice')
    a.setShortcut(QKeySequence("Ctrl+["))
    a.triggered.connect(lambda _, o=self: menuSetNotice(o, '['))
    a = menu.addAction('Add checked to notice')
    a.setShortcut(QKeySequence("Ctrl+]"))
    a.triggered.connect(lambda _, o=self: menuSetNotice(o, ']'))
    a = menu.addAction('Clear notice')
    a.setShortcut(QKeySequence("Ctrl+'"))
    a.triggered.connect(lambda _, o=self: menuSetNotice(o, "'"))
    a = menu.addAction('Open Google')
    a.setShortcut(QKeySequence("Ctrl+G"))
    a.triggered.connect(lambda _, o=self: menuOpenGoogle(o))

# sys.stderr.write("sys.version_info:"+str(sys.version_info))
addHook("browser.setupMenus", onSetupMenus)

origKeyHandler = Reviewer._keyHandler
Reviewer._keyHandler = newKeyHandler
AutoSync()