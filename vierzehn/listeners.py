# standard library
import logging
import os

# 3rd party modules
import tweepy
import yaml

class RetweetListener(tweepy.StreamListener):
    def __init__(self, api, db, me, retweet_words, forbidden_words, forbidden_apps):
        logging.debug('Setting up RetweetListener...')
        self.api = api
        self.db = db
        self.me = me
        self.RETWEET_WORDS = retweet_words
        self.FORBIDDEN_WORDS = forbidden_words
        self.FORBIDDEN_APPS = forbidden_apps

        self.ignore_path = os.path.join(os.path.expanduser('~'),
                                        '.vierzehn',
                                        'ignore.yaml')
        if not os.path.exists(self.ignore_path):
            logging.debug('Setting up ignore-file in %r.' % (self.ignore_path))
            ignore_file = open(self.ignore_path, 'w')
            ignore_file.close()
        
        self.load_ignored_users()
        logging.debug('Everything OK.')

    def load_ignored_users(self):
        '''
        Loads the list of ignored screen_names
        (users in short) from self.ignore_path
        into self.ignored_users and logs it into
        the info-stream.
        '''

        with open(self.ignore_path) as ignore_file:
            self.ignored_users = yaml.load(ignore_file.read())
            if self.ignored_users is None:
                self.ignored_users = []
        logging.info('Ignoring users %r.' % (self.ignored_users))

    def update_ignored_users(self, screen_name):
        '''
        Appends the given screen_name (user in short)
        to self.ignored_users and refreshes the file
        specified by self.ignore_path.
        '''
        self.ignored_users.append(screen_name)
        with open(self.ignore_path, 'w') as ignore_file:
            ignore_file.write(yaml.dump(self.ignored_users))

    def on_status(self, status):
        '''
        Overrides the on_status() inherited from 
        tweepy.StreamListener class.
        '''
        self.status = status
        self.react()

    def is_in_status(self, *args):
        '''
        Shortcut: Returns true if 'something'.lower()
        is in self.status.text.lower()
        '''
        for arg in args:
            if not arg.lower() in self.status.text.lower():
                return False
        return True


    def react(self):
        '''
        Called when self.status is set by self.on_status()
        in order to react to a tweet.
        '''
        if self.status.user.screen_name == self.me.screen_name:
            return # prevent bot from rt'ing itself

        if self.is_in_status('RT'):
            return # prevent bot from rt'ing "hardcoded" retweets
            
        for forbidden_word in self.FORBIDDEN_WORDS:
            if self.is_in_status(forbidden_word):
                logging.info('Would retweet %r, but forbidden word.' %
                             (forbidden_word))
                if self.db is not None:
                    self.db.incr('bot:trigger')
                return

        if self.status.source in self.FORBIDDEN_APPS:
            logging.info('Ignoring tweet sent via %s.' % (self.status.source))
            return

        if self.status.user.screen_name in self.ignored_users:
            logging.info('Would retweet from @%s, but ignored.' %
                         (self.status.user.screen_name))
            return

        if self.is_in_status('@ichbinvierzehn', 'du nervst'):
            logging.info('@%s wants to be ignored.' %
                         (self.status.user.screen_name))
            self.update_ignored_users(self.status.user.screen_name)
            if self.db is not None:
                self.db.incr('bot:annoyed')
            self.response_status = 'Ich höre ja schon auf, @%s :(' % \
                                    (self.status.user.screen_name)
            self.api.update_status(status=self.response_status,
                                   in_reply_to_status_id=self.status.id)
            return

        if self.is_in_status('@ichbinvierzehn', 'liebe dich'):
            logging.info('@%s loves the bot.' % (self.status.user.screen_name))
            if self.db is not None:
                self.db.incr('bot:ily')
            self.response_status = 'Das ist wunderbar, @%s :)' % \
                                    (self.status.user.screen_name)
            self.api.update_status(status=self.response_status,
                                   in_reply_to_status_id=self.status.id)
            return

        if self.is_in_status('@ichbinvierzehn'):
            # damit der Bot nicht für blanke RTs missbraucht wird
            return


        try:
            self.api.retweet(self.status.id)
            logging.info('Retweeting @%s: %r' %
                         (self.status.user.screen_name, self.status.text))
            if self.db is not None:
                self.db.incr('bot:rt')
        except tweepy.TweepError:
            # Laufen lassen -> fixen? o.O
            pass
