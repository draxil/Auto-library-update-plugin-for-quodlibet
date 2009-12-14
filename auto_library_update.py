# Automatic library update plugin
#
# (c) 2009 joe higton
#
# Licensed under GPLv2. See Quod Libet's COPYING for more information.
#

import os
from pyinotify import WatchManager, ThreadedNotifier, EventsCodes, ProcessEvent

from plugins.events import EventPlugin
import config
import glib
import re

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

    # enabled hook, get everything cooking:
    def enabled( self ):
        if not self.running :
            self.wm = WatchManager()
            
            # the event handler will do the actual event processing,
            # see the ALE class below for details
            self.event_handler = self.ALE( self )
            
            # we'll use a threaded notifier flagged as a daemon thread
            # so that it will stop when QL does
            self.tn = ThreadedNotifier( self.wm, self.event_handler )
            self.tn.daemon = True
            self.tn.start()

            # mask for watched events:
            FLAGS=EventsCodes.ALL_FLAGS
            mask = FLAGS['IN_DELETE'] | FLAGS['IN_CLOSE_WRITE']\
                | FLAGS['IN_MOVED_FROM'] | FLAGS['IN_MOVED_TO']

            # watch paths in scan_list:
            for path in self.scan_list():
                log ( 'Adding watch: for ' + path )
                self.wm.add_watch( path, mask, rec=True )

            self.running = True
    
    # disable hook, stop the notifier:
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
            log("alu : %s" % alu )
        # process close-write event (  copy, new file etc )
        def process_IN_CLOSE_WRITE(self, event):
            glib.idle_add( self.add_event, event )

        # process moved-to event:
        def process_IN_MOVED_TO( self, event ):
            log( 'moved event' )
            glib.idle_add( self.add_event, event )

        # general we think we added something callback:
        def add_event ( self, event ):
            lib = self._alu.library
            path = os.path.join(event.path, event.name)
            if event.dir:
                for path, dnames, fnames in os.walk(path):
                    for filename in fnames:
                        fullfilename = os.path.join(path, filename)
                        lib.add_filename(fullfilename)
            else:
                item =  lib.add_filename ( path )
                log( '%s added to library' % item )
            return False

        # process delete event
        def process_IN_DELETE(self, event):
            glib.idle_add( self.check_event, event )

        # process the moved-from event:
        def process_IN_MOVED_FROM( self, event ):
            glib.idle_add( self.check_event, event )
        
        # general "check to see if it's still there" callback:
        def check_event( self, event ):
            lib = self._alu.library
            path = os.path.join(event.path, event.name)

            log( 'check (%s) event for %s' %  (event.path, path) )

            if event.dir:
                log( 'scan? %s ' % path )
                path_re = re.compile('^' + path)
                to_reload = []
                for i in lib._contents:
                    if path_re.match( i ):
                        try:
                            item = lib.__getitem__( i )
                        except:
                            pass
                        if item:
                            to_reload.append(item)
                for item in to_reload:
                    lib.reload( item )
            else:
                item = lib.__getitem__( path )
                log( 'removing %s from library' % item )
                if item:
                    lib.reload(item)
            return False

def log(msg):
    if verbose:
        print "[auto_lib]", msg

# fin #
