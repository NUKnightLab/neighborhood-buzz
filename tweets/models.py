from django.contrib.gis.db import models
from autoslug import AutoSlugField

class Country(models.Model):
    name = models.CharField(max_length=256)
    abbr = models.CharField(max_length=2)
    
    geom = models.MultiPolygonField()
    objects = models.GeoManager()

    class Meta:
        verbose_name_plural = 'Countries'
        ordering = ['name']
    
    def __unicode__(self):
        return self.name

class State(models.Model):
    name = models.CharField(max_length=256)
    abbr = models.CharField(max_length=2)
    drawseq = models.IntegerField()
    state_fips = models.CharField(max_length=2)
    sub_region = models.CharField(max_length=20)
    country = models.ForeignKey(Country)
    
    geom = models.MultiPolygonField()
    objects = models.GeoManager()

    class Meta:
        verbose_name_plural = 'States'
        ordering = ['name']
    
    def __unicode__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=256)
    slug = AutoSlugField(max_length=256, populate_from='name', unique=True)
    state = models.ForeignKey(State, null=True, blank=True)
    country = models.ForeignKey(Country)
    
    geom = models.MultiPolygonField()
    objects = models.GeoManager()

    class Meta:
        verbose_name_plural = 'Cities'
        ordering = ['name']
    
    def __unicode__(self):
        return self.name
        
class Community(models.Model):
    name = models.CharField(max_length=256)
    slug = AutoSlugField(max_length=256, populate_from='name', unique=True)
    city = models.ForeignKey(City, null=True)

    geom = models.MultiPolygonField()
    objects = models.GeoManager()    

    class Meta:
        verbose_name_plural = 'Communities'
    
    def __unicode__(self):
        return self.name
 
class Category(models.Model):
    name = models.CharField(max_length=256)
    slug = AutoSlugField(max_length=256, populate_from='name', unique=True)
    threshold = models.FloatField(blank=True, default=0.0)
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __unicode__(self):
        return self.name
                        
class Tweet(models.Model):
    id_str = models.CharField(max_length=256, unique=True)    
    created_at = models.DateTimeField(db_index=True)
    lang = models.CharField(max_length=3)
    text = models.TextField()
    html = models.TextField(blank=True, null=True)
    entities = models.TextField()
    coords = models.PointField()
    user_id_str = models.CharField(max_length=256)
    user_name = models.CharField(max_length=256)
    user_screen_name = models.CharField(max_length=256)
    user_profile_image_url = models.TextField()
    
    community = models.ForeignKey(Community, blank=True, null=True)
    state = models.ForeignKey(State)
    
    category = models.ForeignKey(Category, blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
  
    objects = models.GeoManager()    
     
    def __unicode__(self):
        return self.text
        
class Aggregate(models.Model):
    date = models.DateField()
    city = models.ForeignKey(City)
    community = models.ForeignKey(Community)
    category = models.ForeignKey(Category)
    count = models.IntegerField()
    
    class Meta:
        unique_together = (('date', 'city', 'community', 'category'),)

    def __unicode__(self):
        return '%s:%s:%s' % (self.date.isoformat(), self.city, self.community)
    
class Feedback(models.Model):
    tweet = models.ForeignKey(Tweet)
    miscategorized = models.IntegerField(blank=True, default=0)

    class Meta:
        verbose_name_plural = 'Feedback'
    
    def __unicode__(self):
        return "%d/%s: %d" % (tweet.id, tweet.id_str, miscategorized)