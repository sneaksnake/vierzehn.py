# standard library
import logging
import os
import sys

# 3rd party modules
try:
    import redis
except ImportError:
    logging.debug('py-redis is not installed.')
import tweepy
import yaml

# own modules
from .listeners import RetweetListener

class VierzehnBot():
    def __init__(self, config_path):
        '''
        Initializes the VierzehnBot class with
        a supplied path to a config file.
        '''
        logging.getLogger('oauthlib').setLevel(logging.WARNING)
        logging.getLogger('tweepy').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('requests_oauthlib').setLevel(logging.WARNING)

        if not os.path.exists(config_path):
            logging.critical('The config file doesn\'t exist!')
            sys.exit(0)

        self.vierzehn_dir = os.path.join(os.path.expanduser('~'), '.vierzehn')
        if not os.path.exists(self.vierzehn_dir):
            logging.debug('Setting up app-folder in %r.' % (self.vierzehn_dir))
            os.makedirs(self.vierzehn_dir)

        with open(config_path) as config_file:
            self.tmp = yaml.load(config_file.read())

        try:
            self.CONSUMER_TOKEN = self.tmp['consumer_token']
            self.CONSUMER_SECRET = self.tmp['consumer_secret']
            self.ACCESS_TOKEN = self.tmp['access_token']
            self.ACCESS_SECRET = self.tmp['access_secret']
            self.REACT_TO_MENTION = self.tmp['react_to_mention']
            self.REDIS_HOST = self.tmp['redis_host']
            self.REDIS_PORT = self.tmp['redis_port']
            self.REDIS_DBNR = self.tmp['redis_dbnr']
            self.RETWEET_WORDS = self.tmp['retweet_words']
            self.FORBIDDEN_WORDS = self.tmp['forbidden_words']
            self.FORBIDDEN_APPS = self.tmp['forbidden_apps']
        except KeyError:
            logging.critical('Invalid config file! (has to be case-sensitive)')
            sys.exit(0)
        else:
            self.tmp = None

        try:
            self.db = redis.StrictRedis(
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                db=self.REDIS_DBNR,
            )
        except NameError:
            logging.warning('Redis is not installed, disabling...')
            self.db = None
        else:
            logging.debug('Successfully connected to redis!')

        self.auth = tweepy.OAuthHandler(self.CONSUMER_TOKEN, self.CONSUMER_SECRET)
        self.auth.set_access_token(self.ACCESS_TOKEN, self.ACCESS_SECRET)
        self.api = tweepy.API(self.auth)

        self.me = self.api.me()
        logging.info('Logged in as @%s' % (self.me.screen_name))

        if self.REACT_TO_MENTION:
            logging.info('React-to-mention enabled.')
            self.RETWEET_WORDS.append('@%s' % self.me.screen_name)
        else:
            logging.info('React-to-mention disabled.')

    def run(self):
        '''
        Sets up the RetweetListener, the Stream object and
        begins retweeting relevant content.
        '''
        self.retweet_listener = RetweetListener(
            api=self.api,
            db=self.db,
            me=self.me,
            retweet_words=self.RETWEET_WORDS,
            forbidden_words=self.FORBIDDEN_WORDS,
            forbidden_apps=self.FORBIDDEN_APPS
        )
        self.stream = tweepy.Stream(auth=self.api.auth,
                                    listener=self.retweet_listener)

        try:
            self.stream.filter(track=self.RETWEET_WORDS)
        except KeyboardInterrupt:
            logging.info('Interrupted by user, shutting down...')
            sys.exit(0)
        except:
            self.stream.filter(track=self.RETWEET_WORDS)