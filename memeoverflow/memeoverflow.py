from .db import MemeDatabase
from .memes import *

import random
from time import sleep
from io import BytesIO
import html
import urllib.request
import wget

import requests
from twython import Twython, TwythonError
from mastodon import Mastodon   #pip3 install Mastodon.py


class MemeOverflow:
    """
    Class for generating and tweeting memes of questions from a given
    StackExchange site

    :param dict twitter:
        Expected keys: con_key, con_sec, acc_tok, acc_sec (Twitter API keys)

    :param dict imgflip:
        Expected keys: user, pass (imgflip account)

    :param dict stackexchange:
        Expects key: site (StackExchange site name)
        Optional key: key (StackExchange API key)
    """
    def __init__(self, twitter, imgflip, stackexchange):
        self.db = MemeDatabase(stackexchange['site'])
        self.twitter = Twython(
            twitter['con_key'],
            twitter['con_sec'],
            twitter['acc_tok'],
            twitter['acc_sec']
        )
        self.imgflip = imgflip
        self.stackexchange = stackexchange
        self.mastodon = Mastodon(
    access_token = 'ef56dd61cd91fdeb65e90d67a2e650581406d20be83b62cd911dcf20ea7c9792',
    api_base_url = 'https://ubuntu.social'
)

    def __repr__(self):
        return f"<MemeOverflow object for site {self.stackexchange['site']}>"

    def __call__(self):
        """
        Main loop: look up questions, for each question:
        - check database
        - generate meme
        - tweet it
        - add to database
        """
        while True:
            self.update_meme_database()
            questions = self.get_se_questions(100)
            for q in questions:
                question = html.unescape(q['title'])
                question_url = q['link']
                question_id = q['question_id']
                if self.db.question_is_known(question_id):
                    continue
                status = f'{question} {question_url}'
                img_url, meme_id = self.make_meme(question)
                try:
                    #self.tweet(status, img_url)
                    self.toot(status, img_url)
                    print(f'Tweeted: {question} [meme {meme_id}]')
                except Exception as e:
                    print(f'Failed to toot: {e}')
                    sleep(60)
                    continue
                self.db.insert_question(question_id)
                sleep(600*5)
            sleep(600*5)

    def update_meme_database(self):
        """
        Get list of memes from imgflip and add them to the database
        """
        url = 'https://api.imgflip.com/get_memes'
        memes = requests.get(url).json()
        memes = [(m['id'], m['name']) for m in memes['data']['memes']]
        self.db.insert_memes(memes)

    def make_meme(self, text):
        """
        Generate a random meme with the supplied text, and return its URL

        (some logic used to determine a suitable meme for the supplied text,
        see implementation for details)
        """
        url = 'https://api.imgflip.com/caption_image'
        text0 = text
        text1 = None

        if text.lower().startswith("is this "):
            meme_id = IS_THIS
            text0 = "is this"
            text1 = text[8:]
        elif text.count('"') == 2:
            meme_id = DR_EVIL
        else:
            meme_id = self.db.select_random_meme()

        if meme_id == PETER_PARKER_CRY:
            text0 = None
            text1 = text
        elif meme_id == BATMAN_SLAP:
            text0 = text
            text1 = "Install Arch Linux!"
        elif meme_id == KERMIT_BUSINESS:
            if text.endswith('?'):
                # try again
                return self.make_meme(text)
            text0 = text
            text1 = "But that's none of my business"
        elif meme_id == CHANGE_MY_MIND:
            if text.endswith('?'):
                # try again
                return self.make_meme(text)
        elif meme_id == PHILOSORAPTOR:
            if not text.endswith('?'):
                # try again
                return self.make_meme(text)

        data = {
            'username': self.imgflip['user'],
            'password': self.imgflip['pass'],
            'template_id': meme_id,
            'text0': text0,
            'text1': text1,
        }
        r = requests.post(url, data=data)
        try:
            img_url = r.json()['data']['url']
            return (img_url, meme_id)
        except KeyError:
            # blacklist the meme and try another one
            self.db.blacklist_meme(meme_id)
            print(f"Blacklisted meme {meme_id}, trying again")
            return self.make_meme(text)

    def get_se_questions(self, n=1):
        """
        Retrieve n questions from the StackExchange site
        """
        url = 'https://api.stackexchange.com/2.2/questions'
        params = {
            'pagesize': n,
            'site': self.stackexchange['site'],
            'key': self.stackexchange.get('key', None),
        }
        r = requests.get(url, params)
        if r:
            return r.json()['items']
        else:
            print("Failed to reach StackExchange")
            return []

    def tweet(self, status, img_url):
        """
        Tweet status with the image attached
        """
        img = BytesIO(requests.get(img_url).content)
        response = self.twitter.upload_media(media=img)
        media_ids = [response['media_id']]
        self.twitter.update_status(status=status, media_ids=media_ids)
    
    def toot(self, status, img_url):
        """
        Toot status with the image attached
        """
        # This would be a lot easier if mastodon accepted a BytesIO stream
        # or imgflip didn't require headers.
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        # Instead we need to save a jpg to disk :(
        # uses https://stackoverflow.com/a/46511429/1264592
        urllib.request.urlretrieve(img_url, filename="./tmp.jpg")
        media_uploaded_id = (self.mastodon.media_post("./tmp.jpg"))["id"]
        medias = []
        medias.append(media_uploaded_id)
        #media_ids = [response['media_id']]
        self.mastodon.status_post(status=status, media_ids=medias)
