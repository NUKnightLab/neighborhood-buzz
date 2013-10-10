from django.conf.urls import patterns, include, url
from django.views.generic.simple import redirect_to, direct_to_template

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    #url(r'^about/?$', direct_to_template, { 'template': 'about.html' }),
    url(r'^about/?$', 'tweets.views.about'),
    url(r'^tweets/', include('tweets.urls')),
    url(r'^admin/', include(admin.site.urls)),
    
    url('^/?$', 'tweets.views.index')

    #('^/?$', redirect_to, {'url': '/tweets/'})
)
