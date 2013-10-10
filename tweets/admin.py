from django.core import urlresolvers
from django.contrib.admin import ModelAdmin
from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.contrib.gis.db import models
from models import *
  
                  
#
# ModelAdmin -> OSMGeoAdmin
# Note: OSMGeoAdmin uses Open Street Map layer, but GeoModelAdmin does not
#
  
class CountryAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'abbr',)
    ordering = ('name',)
    search_fields = ('name','abbr',)
    
admin.site.register(Country, CountryAdmin)
 
class StateAdmin(admin.OSMGeoAdmin):
    list_display = ('country', 'name', 'abbr')
    list_display_links = ('name', 'abbr',)
    ordering = ('name',)
    search_fields = ('name','abbr',)
    
admin.site.register(State, StateAdmin)

class CityAdmin(admin.OSMGeoAdmin):
    ordering = ('country', 'state', 'name',)
    list_display = ('country', 'state', 'name')
    list_display_links = ('name',)
    search_fields = ('name',)
    
admin.site.register(City, CityAdmin)

class CommunityAdmin(admin.OSMGeoAdmin):
    list_display = ('city', 'name') #, 'tweet_count',)
    list_display_links = ('name',)
    list_filter = ('city',)
    ordering = ('city', 'name',)
    search_fields = ('name',)
    
    # Commented out because way too slow
    #def queryset(self, request):
    #    '''Annotate with tweet count to allow sorting'''
    #    qs = super(CommunityAdmin, self).queryset(request)
    #    qs = qs.annotate(models.Count('tweet'))
    #    return qs
        
    #def tweet_count(self, obj):
    #    '''Return tweet count as link to tweet admin with filter by community'''
    #    url = urlresolvers.reverse('admin:tweets_tweet_changelist') \
    #        + '?community__id__exact=%d' % (obj.id)
    #    return '<a href="%s">%d</a>' % (url, obj.tweet_set.count())
    #tweet_count.admin_order_field = 'tweet__count'
    #tweet_count.allow_tags = True
    
admin.site.register(Community, CommunityAdmin)

class CategoryAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'slug', 'tweet_count', 'threshold')
    list_display_links = ('name', 'slug',)
    ordering = ('name',)

    def queryset(self, request):
        '''Annotate with tweet count to allow sorting'''
        qs = super(CategoryAdmin, self).queryset(request)
        qs = qs.annotate(models.Count('tweet'))
        return qs

    def tweet_count(self, obj):
        '''Return tweet count as link to tweet admin with filter by category'''
        url = urlresolvers.reverse('admin:tweets_tweet_changelist') \
            + '?category__id__exact=%d' % (obj.id)
        return '<a href="%s">%d</a>' % (url, obj.tweet_set.count())
    tweet_count.admin_order_field = 'tweet__count'
    tweet_count.allow_tags = True
    
admin.site.register(Category, CategoryAdmin)

class TweetAdmin(admin.OSMGeoAdmin):
    list_display = ('created_at',  'City', 'Community', 'Category', 'relevance', 'text',)
    list_display_links = ('created_at', 'text',)
    list_filter = ('category', 'community__city',)
    search_fields = ('id_str', 'text')
    ordering = ('created_at',)
    #date_hierarchy = 'created_at'
  
    list_select_related = False
 
    #   
    # Pre-querying for these attributes individually as needed because it is 
    # MUCH faster than doing a massive JOIN with the tweet table.
    #
    _city_map = None
    _community_map = None
    _category_map = None
    
    def __init__(self, *args, **kwargs):
        super(TweetAdmin,self).__init__(*args, **kwargs)           

    def queryset(self, request):
        self._city_map = dict(City.objects.values_list('id', 'name'))
        self._community_map = dict(Community.objects.values_list('id', 'name'))
        self._category_map = dict(Category.objects.values_list('id', 'name'))       
        return super(TweetAdmin, self).queryset(request)
              
    def City(self, obj):
        return self._city_map.get(obj.community.city_id, '')

    def Community(self, obj):
        return self._community_map.get(obj.community_id, '')     
      
    def Category(self, obj):
        return self._category_map.get(obj.category_id, '')     
        
    def relevance(self, obj):
        '''Return formatted score'''
        return "{0:.10f}".format(obj.score or 0)
    relevance.admin_order_field = 'score'
    
    
admin.site.register(Tweet, TweetAdmin)

class AggregateAdmin(ModelAdmin):
    list_display = ('date',  'city', 'community', 'category', 'count')
    list_display_links = ('city', 'community', 'count')
    list_filter = ('city', 'community',)
    ordering = ('date', 'city', 'community', 'category',)

admin.site.register(Aggregate, AggregateAdmin)

class FeedbackAdmin(ModelAdmin):
    list_display = ('tweet', 'miscategorized',)
    
admin.site.register(Feedback, FeedbackAdmin)
    
    