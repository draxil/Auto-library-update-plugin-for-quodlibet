# Automatic library update plugin

import os
from pyinotify import WatchManager, ThreadedNotifier, EventsCodes, ProcessEvent

from plugins.events import EventPlugin
import config
import glib

# Set this to True to enable logging
verbose = False

class AutoLibraryUpdate ( EventPlugin ):
    
    # Tell QL about our plugin:
    PLUGIN_ID = "Automatic library update"
    PLUGIN_NAME = "Automatic library update"
    PLUGIN_DESC = "Keep your quodlibet library up-to-date with inotify"
    PLUGIN_VERSION = "0.1"
    
    # Set everything up:
    def __init__( self ):
        from player import playlist as player
        from quodlibet.library import library as library
        print library
        self.library = library

        wm = WatchManager()

        event_handler = self.ALE( self )

        tn = ThreadedNotifier( wm, event_handler )
        tn.daemon = True

        tn.start()

        FLAGS=EventsCodes.ALL_FLAGS
        mask = FLAGS['IN_DELETE'] | FLAGS['IN_CLOSE_WRITE']  # watched events

        # watch paths in scan_list:
        for path in self.scan_list():
            log ( 'Adding watch: for ' + path )
            wm.add_watch( path, mask, rec=True )
    
    # find list of directories to scan
    def scan_list(self):
        return config.get( "settings", "scan").split(":")

    # auto-library-event class, handles the events
    class ALE( ProcessEvent ):
        def __init__( self, alu ):
            self._alu = alu
        
        # process close-write event
        def process_IN_CLOSE_WRITE(self, event):
            glib.idle_add( self.add_event, event )

        def add_event ( self, event ):
            item =  self._alu.library.add_filename ( os.path.join(event.path, event.name) )
            if item:
                log( '%s added to library' % item )
            return False

        # process delete event
        def process_IN_DELETE(self, event):
            glib.idle_add( self.process_event, event )
        
        def process_event( self, event ):
            item = self._alu.library.__getitem__( os.path.join(event.path, event.name) )
            log( 'removing %s from library' % item )
            if item:
                self._alu.library.reload(item)


def log(msg):
    if verbose:
        print "[auto_lib]", msg

# fin #
