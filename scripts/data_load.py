'''
Use LayerMapping gid utility to load data from ESRI shapefiles into db

You need to know what spatial reference system (SRS) is used in the data file.
The default SRS for geometry fields is WGS84 (SRID 4326).  

Lookup the srid for the .prj file @ http://prj2epsg.org.

If it is not the default, convert it, e.g. from 3435 to 4326...

    $ ogr2ogr -f "ESRI Shapefile" -s_srs EPSG:3435 -t_srs EPSG:4326 \
        output.shp input.shp 

Use ogrinspect to generate django model and model mapping dictionaries.

    $ python manage.py ogrinspect <path to shp file> <django model name> \
        --mapping --multi
    
Paste the generated model code into your Django models.py and sync the db:
    
    $ python manage.py syncdb
       
Paste the generated mapping dictionary here and import your data using the
django shell:

    $ python manage.py shell
    >>> from scripts import data_load
    >>> data_load.city('chicago.shp', 'Chicago', 'Illinois')
    >>> data_load.community('chicago_communities.shp', 'Chicago')
'''
import os
from django.contrib.gis.utils import LayerMapping
from tweets.models import Country, State, City, Community

#
# shapefiles directory
#
_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

#
# model mapping dictionaries
#
# key =  name of field in django model
# value = name of the shapefile field that data will be loaded from
#

country_mapping = {
    'name' : 'name',
    'abbr' : 'abbr',
    'geom' : 'MULTIPOLYGON',
}

state_mapping = {
    'name' : 'STATE_NAME',
    'abbr' : 'STATE_ABBR',
    'drawseq' : 'DRAWSEQ',
    'state_fips' : 'STATE_FIPS',
    'sub_region' : 'SUB_REGION',
    'geom' : 'MULTIPOLYGON',
}

city_mapping = {
    'name' : 'NAME',
    'geom' : 'MULTIPOLYGON',
}

community_mapping = {
    'name' : 'NAME',
    'geom' : 'MULTIPOLYGON',
}

def get_data_path(filename):
    return os.path.abspath(os.path.join(_data_dir, filename))

class CustomLayerMapping(LayerMapping):
    '''Customized LayerMapping so we can add static attributes on import.'''
    def __init__(self, *args, **kwargs):
        self.custom = kwargs.pop('custom', {})
        super(CustomLayerMapping, self).__init__(*args, **kwargs)
    
    def feature_kwargs(self, feat):
        kwargs = super(CustomLayerMapping, self).feature_kwargs(feat)
        kwargs.update(self.custom)
        return kwargs

#
# Import functions
#

def country(filename, verbose=True):
    '''Import country boundaries.'''
    lm = CustomLayerMapping(
        Country,
        get_data_path(filename),
        country_mapping,
        transform=False,
        encoding='iso-8859-1'
    )
    lm.save(strict=True, verbose=verbose)


def state(filename, verbose=True):
    '''Import US state boundaries.'''
    country = Country.objects.get(name='United States')
    
    lm = CustomLayerMapping(
        State,
        get_data_path(filename),
        state_mapping,
        transform=False,
        encoding='iso-8859-1',
        custom={'country_id': country.id} 
    )
    lm.save(strict=True, verbose=verbose)
    
def city(filename, city_name, state_name, verbose=True):
    '''Import city boundaries.'''
    state = State.objects.get(name=state_name)
        
    lm = CustomLayerMapping(
        City, 
        get_data_path(filename),
        city_mapping, 
        transform=False, 
        encoding='iso-8859-1',
        custom={
            'name': city_name,
            'state_id': state.id,
            'country_id': state.country.id
        }
    )
    lm.save(strict=True, verbose=verbose)

def community(filename, city_name, verbose=True):
    '''Import community boundaries.'''
    city = City.objects.get(name=city_name)

    lm = CustomLayerMapping(
        Community, 
        get_data_path(filename),
        community_mapping, 
        transform=False, 
        encoding='iso-8859-1',
        custom={'city_id': city.id}
    )
    lm.save(strict=True, verbose=verbose)
  
    