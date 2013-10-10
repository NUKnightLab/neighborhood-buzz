from django.core.management.base import NoArgsCommand, BaseCommand, CommandError
from tweets.models import *
from optparse import make_option
import os
import pytz
from datetime import datetime, timedelta
import subprocess
import zipfile
import boto
    

def save_file(b, bk, filepath):
    '''Save file @ filepath to bucket b under key bk.'''
    k = Key(b)
    k.key = bk
    k.set_contents_from_filename(filepath, cb=progress_cb)
    
    set_contents_from_filename(
        filepath, 
        cb=lambda nsent, ntotal: \
            stdout.write('Wrote %d / %d bytes...\n', nsent, ntotal)
    )
    
def archivetweets(stdout, min_dt):
    from django.conf import settings
 
    DB = settings.DATABASES['default']
     
     # Archive tweets created_at BEFORE this datetime
    stdout.write('Archiving tweets before %s\n' % min_dt)
            
    # Use data directory within project to write files
    datadir = os.path.join(settings.PROJECT_ROOT, 'data')

    filename = 'tweets_%s.copy' % min_dt.date()
    filepath = os.path.join(datadir, filename)

    zipname = filename+'.zip'
    zippath = os.path.join(datadir, zipname)
    
    # Dump tweets
    stdout.write("Writing %s...\n" % filepath)

    with open(filepath,'w') as f:
        subprocess.check_call([
            'psql',
            '-h', DB['HOST'],
            '-U', DB['USER'],
            '-c', "COPY (SELECT * FROM tweets_tweet WHERE created_at < '%s') TO STDOUT" % (min_dt),
            '--set=ON_ERROR_STOP=true', # to be safe
            DB['NAME']
        ], stdout=f)

    stat = os.stat(filepath)
    stdout.write("Wrote %d bytes\n" % stat.st_size)

    if stat.st_size < 1:
        stdout.write('Nothing to archive!\n')
        stdout.write("Deleting %s...\n" % filepath)
        os.remove(filepath)
        return

    # Compress to zip
    stdout.write("Compressing to %s...\n" % zippath)

    with zipfile.ZipFile(zippath, 'w', zipfile.ZIP_DEFLATED) as f:
        f.write(filepath, filename)
    
    stat = os.stat(zippath)
    stdout.write("Wrote %d bytes\n" % stat.st_size)

    # Delete unzipped file
    stdout.write("Deleting %s\n" % filepath)
    os.remove(filepath)
 
    # Upload to S3
    conn = boto.connect_s3()
    bucket = conn.get_bucket(settings.AWS_ARCHIVE_BUCKET_NAME)    
    bucket_path = os.path.join(DB['NAME'], zipname)

    stdout.write('Uploading to %s:%s...\n' \
        % (settings.AWS_ARCHIVE_BUCKET_NAME, bucket_path))
    key = boto.s3.key.Key(bucket)
    key.key = bucket_path
    #key.set_contents_from_filename(zippath)
    key.set_contents_from_filename(
        zippath, 
        cb=lambda x, y: stdout.write('Wrote %d / %d bytes...\n' % (x, y))
    )

    # Delete zipfile
    stdout.write("Deleting %s\n" % zippath)
    os.remove(zippath)

    # Do NOT delete aggregates
    # Delete tweets IN BATCHES
    stdout.write("Deleting tweets before %s\n" % min_dt) 
    total = Tweet.objects.filter(created_at__lt=min_dt).count()
    
    stdout.write('Found %s tweets\n' % total)
    progress = 0
    step = 10000
    for block in range(0, total, step):   
        Tweet.objects.filter(
            pk__in=Tweet.objects.filter(created_at__lt=str(min_dt)) \
            .values_list('pk')[:step]
        ).delete()

        progress += step
        stdout.write('Deleted %d tweets...\n' % min(progress, total))
                  
 
class Command(NoArgsCommand):
    help = '' \
    'Archive tweets.  Specify a time interval in days (tweets over N days\n' \
    'old, whole days only) or a date (process tweets older than a date).\n\n' \
    'Example: if today is 12/02 and N=1, then, regardless of the current\n' \
    'time, it will archive all tweets created before 12/02 00:00:00.' 

    option_list = BaseCommand.option_list + (
        make_option(
            '--days',
            action='store',
            dest='days',
            type='int',
            default=0,
            help='Archive tweets over N days old'
        ),
        make_option(
            '--date',
            action='store',
            dest='date',
            type='string',
            default='',
            help='Archive tweets dated before a UTC date (YYYY-MM-DD)'
        )           
    )
    
    can_import_settings = True
 
    def handle_noargs(self, **options):
        min_dt = None
        
        days = options['days']
        if days:
            if days < 0:
                raise CommandError('days must be a positive integer')
            min_dt = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.utc) \
                - timedelta(days=days-1)
           
        date = options['date']
        if date:
            try:
                min_dt = datetime.strptime(date, '%Y-%m-%d').replace(
                    tzinfo=pytz.utc)                
            except Exception as err:
                raise CommandError('error parsing date [%s]' % str(err))
        
        if not (days or date):
            raise CommandError('you must specify days or a date')
                    
        if days and date:
            raise CommandError('you cannot specify both days and a date')
                             
        archivetweets(self.stdout, min_dt)
        self.stdout.write('Done.\n')
