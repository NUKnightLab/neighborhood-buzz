from django.core.management.base import NoArgsCommand, BaseCommand, CommandError
from tweets.models import Category, Tweet
import json
import linear as classifier
from datetime import datetime


_limit = 1000    # limit per batch

def categorize(stdout):
    # Hash categories by name
    categories = {}
    for c in Category.objects.all():
        categories[c.name] = c

    while True:
        tweets = Tweet.objects.filter(category__isnull=True)[:_limit]
        n = len(tweets)
        print 'Categorizing %d tweets' % n
        
        if not n:
            return
            
        start = datetime.now()
       
        for tweet in tweets:
            data = classifier.classify_tweet({
                'text': tweet.text,
                'entities': json.loads(tweet.entities)          
            }) or [['other', 0]]  
          
            tweet.category = categories[data[0][0]]
            tweet.score = data[0][1]
            tweet.save()
                      
        print "Categorized %d tweets in %d seconds" % \
            (n, (datetime.now() - start).seconds)

                   
class Command(NoArgsCommand):
    help = 'Categorize un-categorized tweets' 
    
    def handle_noargs(self, **options):
        categorize(self.stdout)
        self.stdout.write('Done.\n')
