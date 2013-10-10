from django.core.management.base import NoArgsCommand, BaseCommand, CommandError
from django.contrib.gis.geos import Point
from django.db.models import Count, Q
from tweets.models import *
from datetime import datetime, timedelta
import dateutil.parser
import pytz


def aggregate(stdout):
    qs = Category.objects.exclude(slug='other')
    other = Category.objects.get(slug='other')
    
    # Build query parameters for categorized tweets
    category_params = None    
    for (id, threshold) in qs.values_list('id', 'threshold'):    
        if category_params:
            category_params |= (Q(category_id=id) & Q(score__gte=threshold))
        else:
            category_params = (Q(category_id=id) & Q(score__gte=threshold))
    
    # Build query parameters for 'other'
    other_params = (Q(category_id=other.id))
    
    for (id, thresh) in qs.values_list('id', 'threshold'):
        other_params |= (Q(category_id=id) & Q(score__lt=thresh))
    
    # Get date bounds
    r = Tweet.objects.order_by('created_at')[0]
    dt_min = r.created_at.replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.utc)

    r = Tweet.objects.order_by('-created_at')[0]
    dt_last = r.created_at.replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.utc)
        
    # Delete old records
    stdout.write('Deleting old aggregate records\n')
    Aggregate.objects.all().delete()
    
    # Add new records   
    while dt_min <= dt_last:
        dt_max = dt_min + timedelta(days=1)
        stdout.write('Aggregating tweets from [%s, %s)\n' % (dt_min, dt_max))
                
        # Categorized...
        qs = Tweet.objects.filter(
                Q(created_at__gte=dt_min), 
                Q(created_at__lt=dt_max),
                category_params
            ).values(
                'community__city_id', 
                'community_id', 
                'category_id'
            ).annotate(n=Count('id'))
        
        Aggregate.objects.bulk_create([
            Aggregate(
                date=dt_min,
                city_id=r['community__city_id'],
                community_id=r['community_id'],
                category_id=r['category_id'],
                count=r['n']
            ) for r in qs
        ])
        
        # Other...
        qs = Tweet.objects.filter(
                Q(created_at__gte=dt_min), 
                Q(created_at__lt=dt_max),
                other_params
            ).values(
                'community__city_id', 
                'community_id'
            ).annotate(n=Count('id'))
            
        Aggregate.objects.bulk_create([
            Aggregate(
                date=dt_min,
                city_id=r['community__city_id'],
                community_id=r['community_id'],
                category_id=other.id,
                count=r['n']
            ) for r in qs
        ])
                    
        dt_min += timedelta(days=1)
        

class Command(NoArgsCommand):
    help = '(Re)generate aggregate tweet records.'
 
    def handle_noargs(self, **options):
        aggregate(self.stdout)
        
