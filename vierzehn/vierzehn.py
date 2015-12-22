# standard library
import logging
import os
import sys

# 3rd party modules
import redis
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
            logging.debug('Setting up app-folder in \'{}\'...'
                          .format(self.vierzehn_dir))
            os.makedirs(self.vierzehn_dir)

        with open(config_path) as config_file:
            self.tmp = yaml.load(config_file.read())

        try:
            self.CONSUMER_TOKEN = self.tmp['consumer_token']
            self.CONSUMER_SECRET = self.tmp['consumer_secret']
            self.ACCESS_TOKEN = self.tmp['access_token']
            self.ACCESS_SECRET = self.tmp['access_secret']
            self.REDIS_HOST = self.tmp['redis_host']
            self.REDIS_PORT = self.tmp['redis_port']
            self.REDIS_DBNR = self.tmp['redis_dbnr']
            self.RETWEET_WORDS = self.tmp['retweet_words']
            self.FORBIDDEN_WORDS = self.tmp['forbidden_words']
        except KeyError:
            logging.critical('Invalid config file! (has to be case-sensitive)')
            sys.exit(0)
        else:
            self.tmp = None

        try:
            self.db = redis.StrictRedis(host=self.REDIS_HOST,
                                        port=self.REDIS_PORT,
                                        db=self.REDIS_DBNR)
        except NameError:
            logging.warning('Redis is not installed, disabling...')
            self.db = None
        else:
            logging.debug('Successfully connected to redis!')

        self.auth = tweepy.OAuthHandler(self.CONSUMER_TOKEN, self.CONSUMER_SECRET)
        self.auth.set_access_token(self.ACCESS_TOKEN, self.ACCESS_SECRET)
        self.api = tweepy.API(self.auth)

        self.me = self.api.me()
        logging.info('Logged in as @{}'.format(self.me.screen_name))

    def run(self):
        '''
        Sets up the RetweetListener, the Stream object and
        begins retweeting relevant content.
        '''
        self.retweet_listener = RetweetListener(self.api,
                                                self.db,
                                                self.me,
                                                self.RETWEET_WORDS,
                                                self.FORBIDDEN_WORDS)
        self.stream = tweepy.Stream(auth=self.api.auth,
                                    listener=self.retweet_listener)

        try:
            self.stream.filter(track=self.RETWEET_WORDS)
        except KeyboardInterrupt:
            logging.info('Interrupted by user, shutting down...')
            sys.exit(0)