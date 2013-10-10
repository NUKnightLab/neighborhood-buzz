from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('tweets.views',
    url(r'^$', 'index'),
    
    # user feedback
    url(r'^feedback/(?P<tweet_id>\d+)/miscategorized/$', 'feedback_miscategorized'),

    # tweets
    url(r'^(?P<city_slug>[-\w]+)/embed/$', 'embed'),
    url(r'^(?P<city_slug>[-\w]+)/(?P<community_slug>[-\w]+)/embed/$', 'embed'),

    # city data
    url(r'^(?P<city_slug>[-\w]+)/summary.json$', 'city_summary_json'),
    url(r'^(?P<city_slug>[-\w]+)/features.json$', 'city_features_json'),
    
    # main views
    url(r'^(?P<city_slug>[-\w]+)/$', 'city'),
    url(r'^(?P<city_slug>[-\w]+)/(?P<community_slug>[-\w]+)/$', 'city'),
)


