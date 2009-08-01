# Automatic library update plugin

import os
from pyinotify import WatchManager, ThreadedNotifier, EventsCodes, ProcessEvent

from plugins.events import EventPlugin
import config
import library

# Set this to True to enable logging
verbose = True

class AutoLibraryUpdate ( EventPlugin ):
    
    # tell QL about our plugin:
    PLUGIN_ID = "Automatic library update"
    PLUGIN_NAME = "Automatic library update"
    PLUGIN_DESC = "Keep your quodlibet library up-to-date with inotify"
    PLUGIN_VERSION = "0.1"
    
    def __init__( self ):
        log( 'Init' )

        wm = WatchManager()

        tn = ThreadedNotifier( wm, self.ALE())
        tn.daemon = True

        tn.start()

        FLAGS=EventsCodes.ALL_FLAGS
        mask = FLAGS['IN_DELETE'] | FLAGS['IN_CREATE']  # watched events

        # watch paths in scan_list:
        for path in self.scan_list():
            log ( 'Adding watch: for ' + path )
            wm.add_watch( path, mask, rec=True )


    def scan_list(self):
        return config.get( "settings", "scan").split(":")

    class ALE( ProcessEvent ):
        def process_IN_CREATE(self, event):
            log( 'Create file event' )
            library.scan( [ os.path.join( event.path, event.name ) ] )
        
        def process_IN_DELETE(self, event):
            log( 'Delete file event' )
            print "Remove: %s" %  os.path.join(event.path, event.name)    


def log(msg):
    if verbose:
        print "[auto_lib]", msg

# fin #
