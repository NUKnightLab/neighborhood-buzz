from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse
from django.utils import simplejson
from django.contrib.gis.geos import Point
from django.db.models import F
from django.forms.models import model_to_dict
from django.conf import settings
import urllib2
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_UP
import pytz
from models import City, Community, Category, Tweet, Aggregate, Feedback

_hostip_url = 'http://api.hostip.info/get_json.php?ip=%s&position=true'

def get_city_nearest_request_ip(request):
    ip = request.META.get('REMOTE_ADDR')

    if ip:
        d = simplejson.loads(
            urllib2.urlopen(_hostip_url % ip).read()
        )
        p = Point(float(d['lng']), float(d['lat']))
        return City.objects.distance(p).order_by('distance')[0]
    return None

def about(request):
    """About page."""
    data = {}
    
    try:
        data['cities'] = City.objects.values('id', 'name', 'slug').order_by('name')                                
    except Exception as err:
        data['error'] = str(err)
        log.exception(err)
    finally:
        return render_to_response('about.html', 
            data, context_instance=RequestContext(request))


def index(request):
    """Get city list and default city_id"""
    data = {}
    city = None
    try:
        data['cities'] = City.objects.values('id', 'name', 'slug').order_by('name')                                

        # Get default city
        #try:
        #    city = get_city_nearest_request_ip(request)
        #except Exception:
        #    pass            
    except Exception as err:
        data['error'] = str(err)
        log.exception(err)
    finally:
        #if city is None:
        #    city = City.objects.filter(name='Chicago')[0]
        #data['city_slug'] = city.slug            
        return render_to_response('tweets/index.html', 
            data, context_instance=RequestContext(request))

def city(request, city_slug, community_slug=''):
    data = {}
    
    city = get_object_or_404(City, slug=city_slug)
    ext = city.geom.extent
    data['city'] = simplejson.dumps({
        'name': city.name,
        'slug': city.slug,
        'bounds': list(ext),
        'center': [(ext[0] + ext[2])/2, (ext[1] + ext[3])/2]
    })

    data['community_slug'] = community_slug    
    
    data['cities'] = City.objects.values('id', 'name', 'slug').order_by('name')                                
    data['categories'] = Category.objects.exclude(slug='other').order_by('name')
    
    d= {}
    for r in data['categories']:
        d[r.slug] = {'id': r.id, 'name': r.name, 'slug': r.slug}
    data['category_map'] = simplejson.dumps(d)
                    
    return render_to_response('tweets/tweets.html', 
        data, context_instance=RequestContext(request))

def city_summary_json(request, city_slug):
    '''
    Return categorical summary data for city
    
    summary: {<id>: {community: {pct: <float>, n: <integer>}}
    
    pct = % of city tweets in that category from that community
    '''
    data = {}
    
    try:
        # Get city data
        city = City.objects.get(slug=city_slug)
 
        # category => city volume
        cat_volume = defaultdict(float)
        
        # category => community => community volume
        cat_com_volume = defaultdict(lambda: defaultdict(float))  

        params = {'city': city}
        if settings.TWEET_SUMMARY_DAYS:
            params['date__gte'] = datetime.utcnow().date() \
                - relativedelta(days=settings.TWEET_SUMMARY_DAYS)

        #if year and month and day:
        #    params['date'] = date(int(year), int(month), int(day))
        #elif year and month:
        #    params['date__gte'] = date(int(year), int(month), 1)            
        #    params['date__lt'] = params['date__gte'] + relativedelta(months=1)
        #elif year:
        #    params['date__gte'] = date(int(year), 1, 1)            
        #    params['date__lt'] = params['date__gte'] + relativedelta(years=1)
        
        qs = Aggregate.objects.filter(**params)
        for r in qs:
            cat_volume[r.category_id] += r.count
            cat_com_volume[r.category_id][r.community_id] += r.count
        city_volume = sum(cat_volume.itervalues()) 
                                      
        # Compose summary
        summary = {}
        
        for category in Category.objects.exclude(slug='other'):
            category_n = cat_volume[category.id]
            cat_d = {}
            
            if category_n:
                # city
                cat_d[0] = {
                    'pct': str(Decimal(str(category_n / (city_volume or 1))) 
                        .quantize(Decimal('0.1'), ROUND_UP)),
                    'n': category_n
                }
                                  
                # community
                for community_id, n in cat_com_volume[category.id].iteritems():
                    cat_d[community_id] = {
                        'pct': str(Decimal(str(n / (category_n or 1)))
                            .quantize(Decimal('0.1'), ROUND_UP)),
                        'n': n
                    }                    
            
            summary[category.id] = cat_d     
                                                 
        data['summary'] = summary
    except Exception as err:
        print err
        data['error'] = str(err)
        log.exception(err)
    finally:
        return HttpResponse(simplejson.dumps(data), mimetype='application/json')
   
def city_features_json(request, city_slug):
    '''Returns GeoJSON for city features'''
    data = { 
        'type': 'FeatureCollection',
        'features': [],
        'slug_map': {}
    }
    
    try:
        feature_index = 0
        for r in Community.objects.filter(city__slug=city_slug).order_by('id'):
            ext = r.geom.extent
            data['features'].append({
                'type': 'Feature',
                'properties': {
                    'id': r.id, 
                    'name': r.name, 
                    'slug': r.slug,
                    'bounds': list(ext),
                    'center': [(ext[0] + ext[2])/2, (ext[1] + ext[3])/2]
                },
                'geometry': simplejson.loads(r.geom.json),            
            })
            data['slug_map'][r.slug] = feature_index
            feature_index += 1
            
    except Exception as err:
        print err
        data['error'] = str(err)
        log.exception(err)
    finally:
        return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def embed(request, city_slug, community_slug=''):
    '''Display tweets for city, community?, and category.'''
    data = {'tweets': []}
    
    try:    
        category_slug = request.REQUEST.get('category')
        category = Category.objects.get(slug=category_slug)
        data['category'] = category
        
        qs = None
        
        if community_slug:
            qs = Tweet.objects.filter(
                    community__slug=community_slug,
                    category=category
                ).order_by('-score')           
        else:
            qs = Tweet.objects.filter(
                    community__city__slug=city_slug,
                    category=category
                ).order_by('-score')
        
        for r in qs[:20]:
            s = r.text
            
            # wrap user_mentions and hashtags
            entities = simplejson.loads(r.entities)
            
            for d in entities['user_mentions']:
                s = re.sub(
                    '@%(screen_name)s' % d, 
                    '<a href="https://twitter.com/%(screen_name)s">@%(screen_name)s</a>' % d,
                    s)
            for d in entities['hashtags']:
                s = re.sub(
                    '#%(text)s' % d, 
                    '<a href="https://twitter.com/search?%23%(text)s">#%(text)s</a>' % d,
                    s)
            
            d = model_to_dict(r)
            d['text'] = s
            data['tweets'].append(d)
    except Exception as err:
        print err
        log.exception(err)
        data['error'] = str(err)
    finally:
        return render_to_response('tweets/embed.html', 
            data, context_instance=RequestContext(request))


def feedback_miscategorized(request, tweet_id):
    '''Increment tweet miscategorization count.'''
    error = ''
    
    try:
        r, created = Feedback.objects.get_or_create(
            tweet_id=tweet_id,
            defaults={'miscategorized': 1})
        if not created:
            r.miscategorized = F('miscategorized') + 1
            r.save()        
    except Exception as err:
        print err
        log.exception(err)
        error = str(err)
    finally:
        return HttpResponse(simplejson.dumps(error), mimetype='application/json')
      