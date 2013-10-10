Requirements
============
python 2.7.x  
PostgreSQL 9.0.x  
PostGIS 1.5.x  
GDAL  
GEOS  
[virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/install.html)

*See requirements.txt*


Mac Installation
----------------

Install Homebrew (see http://mxcl.github.com/homebrew/).

Install required packages using Homebrew.  (Note: I needed the --without-ossp-uuid flag on OS 10.8.2 to get postgres to compile/link correctly,  but I did not need it on OS 10.6.8.)

    brew tap homebrew/versions
    brew install postgresql9 --without-ossp-uuid  
    brew install postgis15
    brew untap homebrew/versions
    brew install gdal geos

Create your data directory.

    initdb /usr/local/var/postgres9
    
If your socket file is getting created in the wrong place, edit your postgres config to set the socket file 
location (/usr/local/var/postgres9/postgresql.conf):

    unix_socket_directory='/var/pgsql_socket'
    
Make sure '/usr/local/bin' gets searched before '/usr/bin' (edit /etc/paths or do something in your .bash_profile).

Make things easier on yourself and add some aliases for these commands to start/stop the db server:

    pg_ctl -D /usr/local/var/postgres9 -l /usr/local/var/postgres9/server.log start
    pg_ctl -D /usr/local/var/postgres9 stop -s -m fast

Put brew's python packages on the path:

    export PYTHONPATH=/usr/local/lib/python2.7/site-packages:$PYTHONPATH
    
Start the db server (using the pg_ctl command above).   
    

Ubuntu Installation
-------------------

Not exactly sure what goes on here, but I know that I needed to install these packages on the app/work servers 
using apt-get, because they were not yet a part of the provisioning process:

* libpqxx3-dev
* libgeos-3.3.3
* libgeos-c1
* libgdal1


Using Fabric
==========================


Setup:

    # Checkout repositories
    git clone git@github.com:NUKnightLab/secrets.git
    git clone git@github.com:NUKnightLab/fablib.git
    git clone git@github.com:NUKnightLab/buzz.git

    # Change into buzz directory
    cd buzz
    
    # Setup a virtual environment
    mkvirtualenv buzz
    
    # Activate the virtual environment
    workon buzz
    
    # Install requirements
    pip install -r requirements.txt

    # Start the postgres db server.
    # (see above)
    
    # Setup local database:
    fab loc setup:sample=y
    
    # Start the development server
    python manage.py runserver
    
To reset:

    # Destroy local database
    fab loc destroy
    
    # Get latest updates
    git pull 
    
    # Re-setup local database
    fab loc setup:sample=y
    
    
Manual Database Setup
=====================

*These are old, pre-Fabric directions, but I will leave them here for informational purposes.*

Create the template_postgis template database:

    $ createdb template_postgis
    $ psql -f /usr/local/share/postgis/postgis.sql template_postgis
    $ psql -f /usr/local/share/postgis/spatial_ref_sys.sql template_postgis

Create your database named 'buzz' from the database template: 

    $ createdb -T template_postgis buzz
    
Create a 'buzzer' user for your database:

    $ psql buzz
    # CREATE USER buzzer;
    # GRANT ALL PRIVILEGES ON DATABASE buzz TO buzzer;
    
Change the owner of the metadata tables in buzz to buzzer and quit psql:

    # ALTER TABLE geometry_columns OWNER TO <user>;
    # ALTER TABLE spatial_ref_sys OWNER TO <user>;
    # \q
    
Use Django to sync your database:

    python manage.py syncdb
        
    
    
