from django.core.management.base import NoArgsCommand, BaseCommand, CommandError
from django.contrib.gis.geos import Point
from django.db.models import F
from tweets.models import *
import sys
import time
from datetime import datetime
import pytz
import json
import tweepy
import tweepy.streaming
import linear as classifier


class Listener(tweepy.streaming.StreamListener): 
    """Listen to the twitter stream"""
    def __init__(self, *args, **kwargs):
        super(Listener, self).__init__(*args, **kwargs)
        self.category_ids = dict(
            Category.objects.values_list('slug', 'id'))
        self.category_thresholds = dict(
            Category.objects.values_list('id', 'threshold'))

    def on_status(self, status):
        """Categorize and save tweets with coords in a state and community."""
        if status.coordinates and not Tweet.objects.filter(id_str=status.id_str):
            coords = Point(
                status.coordinates['coordinates'][0], 
                status.coordinates['coordinates'][1]
            )            
            states = State.objects.filter(geom__contains=coords)            
            communities = Community.objects.filter(geom__contains=coords)
            
            if states and communities:                                                            
                created_at = status.created_at
                if not created_at.tzinfo:
                    created_at = created_at.replace(tzinfo=pytz.utc)
                
                lang = 'en'    
                if hasattr(status, 'lang'):
                    lang = status.lang
                    
                data = classifier.classify_tweet({
                        'text': status.text,
                        'entities': status.entities        
                    }) or [['other', 0]]  
                              
                tweet = Tweet(
                    id_str=status.id_str,
                    created_at=created_at,
                    lang=lang,
                    text=status.text,
                    entities=json.dumps(status.entities),
                    coords=coords,
                    user_id_str=status.user.id_str,
                    user_name=status.user.name,
                    user_screen_name=status.user.screen_name,
                    user_profile_image_url=status.user.profile_image_url,
                    state=states[0],
                    community=communities[0],
                    category_id=self.category_ids[data[0][0]],
                    score=data[0][1]
                 )                                                 
                tweet.save()
                
                # Update aggregate stats
                category_id = self.category_ids['other']                
                if tweet.score >= self.category_thresholds[tweet.category_id]:
                    category_id = tweet.category_id                
                    
                r, created = Aggregate.objects.get_or_create(
                    date=tweet.created_at.date(),
                    city=tweet.community.city,
                    community=tweet.community,
                    category_id=category_id,
                    defaults={'count': 1})
                if not created:
                    r.count = F('count') + 1
                    r.save()

    def on_error(self, code):
        '''Called when a non-200 status code is returned.'''
        raise Exception('Error (%s)' % self.convertStatusCode(code))
    
    def on_timeout(self):
        '''Called when the stream comection times out.'''
        return True

    def convertStatusCode(self, code):
        '''Convert an HTTP status code to message.'''
        if code == 200:
            return 'OK'
        if code == 304:
            return 'Not Modified'
        if code == 400:
            return 'Bad Request'
        if code == 401:
            return 'Unauthorized: Authentication credentials are missing or incorrect.'
        if code == 403:
            return 'Forbidden: The request was understood but refused.'
        if code == 404:
            return 'Not Found: The URI requested is invalid or the resource requested does not exist.'
        if code == 406:
            return 'Not Acceptable: An invalid format was specified in the request.'
        if code == 420:
            return 'You are being rate limited.'
        if code == 500:
            return 'Internal Server Error: Something is broken on Twitter.'
        if code == 502:
            return 'Bad Gateway: Twitter is down or being upgraded.'
        if code == 503:
            return 'Service Unavailable: The Twitter servers are up, but overloaded with requests. Try again later.'
    
        return 'Unknown HTTP status code.'


def listen(stdout):
    from django.conf import settings
    
    r = Country.objects.get(name__iexact='United States')    
    locations = r.geom.extent    
    stdout.write('Searching %s with locations %s\n' % (r.name, locations))
        
    stream = None   
    try:
        auth = tweepy.OAuthHandler(
            settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
        auth.set_access_token(
            settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_TOKEN_SECRET)
        
        while True:    
            stream = tweepy.streaming.Stream(
                auth, Listener(), timeout=None, secure=True)

            # Connect to stream
            stdout.write('Initializing connection...\n')          
            stream.filter(locations=locations, async=True)
            connection_dt = datetime.now()
            
            # Reset connection
            while((datetime.now() - connection_dt).seconds \
                < settings.TWITTER_RESET_SECS):
                time.sleep(60)
                
            # Disconnect
            stdout.write('Disconnecting...\n')
            stream.disconnect()  
            stream = None  
    except NameError:
        raise CommandError('Possible missing twitter account configurations.')
    except KeyboardInterrupt:
        stdout.write('Keyboard interrupt!\n')
        pass
    except Exception:
        raise
    finally:
        if stream and stream.running:
            stream.disconnect()
    

class Command(NoArgsCommand):
    help = 'Connect to the twitter stream'
    can_import_settings = True

    def handle_noargs(self, **options):
        listen(self.stdout)
        
