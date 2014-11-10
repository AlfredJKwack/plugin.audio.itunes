"""
	Plugin for importing iTunes library
"""

__plugin__ = "iTunes"
__author__  = "AlfredJKwack <alfred_j_kwack at badsoda com>"
__credits__ = "Anoop Menon, jingai"
__url__     = "git://github.com/AlfredJKwack/plugin.audio.itunes.git"



import sys
import time
import os
import os.path

import xbmc
import xbmcgui as gui
import xbmcplugin as plugin
import xbmcaddon

addon = xbmcaddon.Addon(id="plugin.audio.itunes")
BASE_URL = "%s" % (sys.argv[0])
PLUGIN_PATH = addon.getAddonInfo("path")
RESOURCE_PATH = os.path.join(PLUGIN_PATH, "resources")
ICONS_PATH = os.path.join(RESOURCE_PATH, "icons")
LIB_PATH = os.path.join(RESOURCE_PATH, "lib")
sys.path.append(LIB_PATH)

from resources.lib.itunes_parser import *

DB_PATH = xbmc.translatePath(os.path.join(addon.getAddonInfo("Profile"), "xbmcitunesdb.db"))
db = ITunesDB(DB_PATH)

platform = "osx"
    
def render_tracks(tracks):

    plugin.setContent(handle = int(sys.argv[1]), content= 'songs') 

    for track in tracks:
        item = gui.ListItem( track['name'] )
        labels={
            "artist": track['artist'],
            "album": track['album'],
            "title": track['name'],
            "genre": track['genre']
            }
        if track['albumtracknumber']:
            labels['tracknumber'] = int(track['albumtracknumber'])
        if track['playtime']:
            labels['duration'] = int(track['playtime'])/1000.0
        if track['year']:
            labels['year'] = int(track['year'])
        if track['rating']:
            labels['rating'] = str(round((track['rating'] / 20)))
        item.setInfo( type="music", infoLabels=labels )
        plugin.addDirectoryItem(handle = int(sys.argv[1]),
                                url=track['filename'],
                                listitem = item,
                                isFolder = False)

    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_UNSORTED )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_GENRE )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_TITLE )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_TITLE_IGNORE_THE )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_SONG_RATING )
#    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_YEAR)
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_ARTIST )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_ARTIST_IGNORE_THE )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_TRACKNUM )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_ALBUM_IGNORE_THE )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_ALBUM )
								
def list_tracks_by_album(params):
    global db
    albumid = params['albumid']
    tracks = db.GetTracksInAlbum(albumid)
    render_tracks(tracks)
    return

def list_albums(params):
    global db, ICONS_PATH
    artistid = 0
    try:
        # if we have an album id, only list tracks in the album
        albumid = params['albumid']
        return list_tracks_by_album(params)
    except Exception, e:
        print str(e)
        pass
    albums = db.GetAlbums()
    if not albums:
        return
    icon = ICONS_PATH+"/albums.png"
    plugin.setContent(handle = int(sys.argv[1]), content= 'albums') 
    showed_extended_info = 0

    for (albumid, album, artistid, artist) in albums:
        if (artist):
            showed_extended_info = 1
            myStr = album + " ( by " + artist + ")"
            item = gui.ListItem( myStr , thumbnailImage=icon )
            item.setInfo( type="music", infoLabels={ 'artist': artist , 'album': album} )
        else:
            item = gui.ListItem( album, thumbnailImage=icon )
            item.setInfo( type="music", infoLabels={ 'album': album} )
        plugin.addDirectoryItem(handle = int(sys.argv[1]),
                                url=BASE_URL+"?action=albums&albumid=%s" % (albumid),
                                listitem = item,
                                isFolder = True)

    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_UNSORTED )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_ALBUM )    
    if showed_extended_info:
        plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_ARTIST )
    
    return

	
def list_albums_by_artist(params):
    global db
    artistid = params['artistid']
    albums = db.GetAlbumsByArtistId(artistid)
    if len(albums) > 0:
        plugin.setContent(handle = int(sys.argv[1]), content= 'albums') 
        item = gui.ListItem( " << All tracks by this Artist >> " )
        plugin.addDirectoryItem(handle = int(sys.argv[1]),
                                url=BASE_URL+"?action=tracks&artistid=%s" % artistid,
                                listitem = item,
                                isFolder = True)
        for (albumid, album, artistid, artist) in albums:
            item = gui.ListItem( album )
            item.setInfo( type="music", infoLabels={ 'artist': artist , 'album': album} )
            plugin.addDirectoryItem(handle = int(sys.argv[1]),
                                    url=BASE_URL+"?action=albums&albumid=%s" % albumid,
                                    listitem = item,
                                    isFolder = True)
        plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_LABEL )
        plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_UNSORTED )
    else:
        list_tracks(params)
    return

def list_artists(params):
    global db,ICONS_PATH
    artistid = 0
    try:
        artistid = params['artistid']
        return list_albums_by_artist(params)
    except Exception, e:
        print str(e)
        pass
    artists = db.GetArtists()
    icon = ICONS_PATH+"/artist.png"
    for (artistid,artist) in artists:
        item = gui.ListItem( artist, thumbnailImage=icon )
        #item.setInfo( type="Music", infoLabels={ "Artist": artist } )
        plugin.addDirectoryItem(handle = int(sys.argv[1]),
                                url=BASE_URL+"?action=artists&artistid=%s" % artistid,
                                listitem = item,
                                isFolder = True)
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_LABEL )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_UNSORTED )
    return

	
def list_tracks_in_playlist(params):
    global db
    playlistid = params['playlistid']
    tracks = db.GetTracksInPlaylist(playlistid)
    render_tracks(tracks)

def list_playlists(params):
    global db, ICONS_PATH
    playlistid = 0
    try:
        playlistid = params['playlistid']
        return list_tracks_in_playlist(params)
    except Exception, e:
        print str(e)
        pass
    playlists = db.GetPlaylists()
    icon = ICONS_PATH+"/playlist.png"
    for (playlistid, playlist) in playlists:
        item = gui.ListItem( playlist, thumbnailImage=icon )
        # item.setInfo( type="Music" )
        plugin.addDirectoryItem(handle = int(sys.argv[1]),
                                url=BASE_URL+"?action=playlists&playlistid=%s" % playlistid,
                                listitem = item,
                                isFolder = True)
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_LABEL )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_UNSORTED )
    return

	
def list_tracks_in_genre(params):
    global db
    genreid = params['genreid']
    tracks = db.GetTracksInGenre(genreid)
    render_tracks(tracks)
    return

def list_genres(params):
    global ICONS_PATH, db
    genreid = 0
    try:
        # if we have an genre id, only list tracks in that genre
        genreid = params['genreid']
        return list_tracks_in_genre(params)
    except Exception, e:
        print str(e)
        pass
    genres = db.GetGenres()
    if not genres:
        return
    icon = ICONS_PATH+"/genres.png"
    for (genreid, genre) in genres:
        item = gui.ListItem( genre, thumbnailImage=icon )
        plugin.addDirectoryItem(handle = int(sys.argv[1]),
                                url=BASE_URL+"?action=genres&genreid=%s" % (genreid),
                                listitem = item,
                                isFolder = True, totalItems=100)
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_LABEL )
    plugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=plugin.SORT_METHOD_UNSORTED )    
    return


def list_tracks_with_rating(params):
    global db
    tracks = db.GetTracksWithRating(params['rating'])
    render_tracks(tracks)
    return

def list_ratings(params):
    global db,BASE_URL,ICONS_PATH
    albumid = 0
    try:
        # if we have an album id, only list tracks in the album
        rating = params['rating']
        return list_tracks_with_rating(params)
    except Exception, e:
        print str(e)
        pass
    for a in range(1,6):
        rating = "%d star "%a
        item = gui.ListItem( rating, thumbnailImage=ICONS_PATH+"/star%d.png"%a )
        plugin.addDirectoryItem(handle = int(sys.argv[1]),
                                url=BASE_URL+"?action=ratings&rating=%d" % (a),
                                listitem = item,
                                isFolder = True)

	
def list_tracks(params):
    global db
    artistid = params['artistid']
    tracks = db.GetTracksByArtist(artistid)
    render_tracks(tracks)
    return


	
def progress_callback(current, max):
    item = gui.ListItem( ">>" )
    plugin.addDirectoryItem(handle = int(sys.argv[1]),
                            url=BASE_URL,
                            listitem = item,
                            isFolder = False)

def import_library(filename):
    global db
    db.ResetDB()
	
    iparser = ITunesParser(db.AddTrackNew, db.AddPlaylistNew, db.SetConfig, progress_callback)
    try:
        iparser.Parse(filename)
        db.UpdateLastImport()
    except:
        print traceback.print_exc()
    db.Commit()


def get_params(paramstring):
    params = {}
    paramstring = str(paramstring).strip()
    paramstring = paramstring.lstrip("?")
    if not paramstring:
        return params
    paramlist = paramstring.split("&")
    for param in paramlist:
        (k,v) = param.split("=")
        params[k] = v
    print params
    return params
	
def process_params(params):
    try:
        action = params['action']
    except:
        return root_directory()

    if action == "artists":
        return list_artists(params)
    elif action == "albums":
        return list_albums(params)
    elif action == "playlists":
        return list_playlists(params)
    elif action == "tracks":
        return list_tracks(params)
    elif action == "genres":
        return list_genres(params)
    elif action == "ratings":
        return list_ratings(params)
    elif action == "rescan":
        import_library(addon.getSetting('albumdata_xml_path'))
        plugin.endOfDirectory( handle = int(sys.argv[1]), succeeded = False )
        sys.exit(0)

    root_directory()

	
def root_directory():
    global ICONS_PATH
    # add the artists entry
    item = gui.ListItem(addon.getLocalizedString(30100), thumbnailImage=ICONS_PATH+"/artist.png" )
    item.setInfo( type="Music", infoLabels={ "Title": "Artists" } )
    plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=artists", listitem = item,
                            isFolder = True)

    item = gui.ListItem(addon.getLocalizedString(30101), thumbnailImage=ICONS_PATH+"/albums.png" )
    item.setInfo( type="Music", infoLabels={ "Title": "Albums" } )
    plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=albums", listitem = item, 
                            isFolder = True)

    item = gui.ListItem(addon.getLocalizedString(30102), thumbnailImage=ICONS_PATH+"/playlist.png" )
    item.setInfo( type="Music", infoLabels={ "Title": "Playlists" } )
    plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=playlists", listitem = item, 
                            isFolder = True)

    item = gui.ListItem(addon.getLocalizedString(30103), thumbnailImage=ICONS_PATH+"/genres.png" )
    item.setInfo( type="Music", infoLabels={ "Title": "Genres" } )
    plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=genres", listitem = item, 
                            isFolder = True)

    item = gui.ListItem(addon.getLocalizedString(30104), thumbnailImage=ICONS_PATH+"/star.png" )
    item.setInfo( type="Music", infoLabels={ "Title": "Rating" } )
    plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=ratings", listitem = item, 
                            isFolder = True)

    hide_import_lib = addon.getSetting('hide_import_lib')
    if (hide_import_lib == ""):
        addon.setSetting('hide_import_lib', 'false')
        hide_import_lib = "false"
    if (hide_import_lib == "false"):
        item = gui.ListItem(addon.getLocalizedString(30105), thumbnailImage=ICONS_PATH+"/import.png"  )
        plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=rescan", listitem = item, 
                                isFolder = True, totalItems=100)

if __name__=="__main__":
    xmlfile = addon.getSetting('albumdata_xml_path')
    if (xmlfile == ""):
	try:
	    xmlfile = os.getenv("HOME") + "/Music/iTunes/iTunes Library.xml"
	    addon.setSetting('albumdata_xml_path', xmlfile)
	except:
	    pass

    try:
        # auto-update if so configured
        auto_update_lib = addon.getSetting('auto_update_lib')
        if (auto_update_lib == ""): # set default
            addon.setSetting('auto_update_lib', 'false') 
            auto_update_lib = "false"
        if (auto_update_lib == "true"):
            try:
                xml_mtime = os.path.getmtime(xmlfile)
                db_mtime = os.path.getmtime(DB_PATH)
                print "xml_mtime:" + str(xml_mtime) + " db_mtime: " + str(db_mtime)
            except Exception, e:
                print to_str(e)
                pass
            else:
                print "autoupdate check"
                if (xml_mtime > db_mtime):
                    import_library(xmlfile)

        params = sys.argv[2]
        process_params(get_params(params))
        plugin.endOfDirectory( handle = int(sys.argv[1]), succeeded = True )
		
    except Exception, e:
        print str(e)
        print traceback.print_exc()
