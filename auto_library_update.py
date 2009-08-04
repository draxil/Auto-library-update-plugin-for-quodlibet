# Automatic library update plugin

import os
from pyinotify import WatchManager, ThreadedNotifier, EventsCodes, ProcessEvent

from plugins.events import EventPlugin
import config
import glib

# Set this to True to enable logging
verbose = True

class AutoLibraryUpdate ( EventPlugin ):
    
    # Tell QL about our plugin:
    PLUGIN_ID = "Automatic library update"
    PLUGIN_NAME = "Automatic library update"
    PLUGIN_DESC = "Keep your quodlibet library up-to-date with inotify."
    PLUGIN_VERSION = "0.1"
    
    library = None
    wm = None
    tn = None
    event_handler = None
    running = False

    # Set everything up:
    def __init__( self ):
        from quodlibet.library import library as library

        self.library = library
    
    def enabled( self ):
        if not self.running :
            self.wm = WatchManager()

            self.event_handler = self.ALE( self )

            self.tn = ThreadedNotifier( self.wm, self.event_handler )
            self.tn.daemon = True

            self.tn.start()

            FLAGS=EventsCodes.ALL_FLAGS
            
            # mask for watched events:
            mask = FLAGS['IN_DELETE'] | FLAGS['IN_CLOSE_WRITE']\
                   | FLAGS['IN_MOVED_FROM'] | FLAGS['IN_MOVED_TO']

            # watch paths in scan_list:
            for path in self.scan_list():
                log ( 'Adding watch: for ' + path )
                self.wm.add_watch( path, mask, rec=True )
            self.running = True

    def disabled( self ):
        if self.running:
            self.running = False
            self.tn.stop()

    # find list of directories to scan
    def scan_list( self ):
        return config.get( "settings", "scan").split(":")

    # auto-library-event class, handles the events
    class ALE( ProcessEvent ):
        def __init__( self, alu ):
            self._alu = alu
        
        # process close-write event (  copy, new file etc )
        def process_IN_CLOSE_WRITE(self, event):
            glib.idle_add( self.add_event, event )

        # process moved-to event:
        def process_IN_MOVED_TO( self, event ):
            glib.idle_add( self.add_event, event )

        # general we think we added something callback:
        def add_event ( self, event ):
            item =  self._alu.library.add_filename ( os.path.join(event.path, event.name) )
            if item:
                log( '%s added to library' % item )
            return False

        # process delete event
        def process_IN_DELETE(self, event):
            glib.idle_add( self.process_event, event )

        # process the moved-from event:
        def process_IN_MOVED_FROM( self, event ):
            glib.idle_add( self.process_event, event )
        
        # general "check to see if it's still there" callback:
        def process_event( self, event ):
            item = self._alu.library.__getitem__( os.path.join(event.path, event.name) )
            log( 'removing %s from library' % item )
            if item:
                self._alu.library.reload(item)
            return False

def log(msg):
    if verbose:
        print "[auto_lib]", msg

# fin #
