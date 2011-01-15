"""
    Parser for iTunes' iTunes Music Library.xml
"""

__author__  = "AlfredJKwack <alfred_j_kwack at badsoda com>"
__credits__ = "Anoop Menon, jingai"
__url__     = "git://github.com/AlfredJKwack/plugin.audio.itunes.git"

import traceback
import xml.parsers.expat
from pysqlite2 import dbapi2 as sqlite
from urllib import unquote
import sys
import os
import os.path
import locale

TRACK_ID         = 0
TRACK_NAME       = 1
TRACK_PLAY_COUNT = 2
TRACK_RATING     = 3
TRACK_YEAR       = 4
TRACK_BITRATE    = 5
TRACK_NUMBER     = 6
TRACK_FILENAME   = 7
TRACK_ALBUM      = 8
TRACK_ARTIST     = 9

def to_unicode(text):
    if (isinstance(text, unicode)):
        return text

    if (hasattr(text, '__unicode__')):
        return text.__unicode__()

    text = str(text)

    try:
        return unicode(text, 'utf-8')
    except UnicodeError:
        pass

    try:
        return unicode(text, locale.getpreferredencoding())
    except UnicodeError:
        pass

    return unicode(text, 'latin1')

def to_str(text):
    if (isinstance(text, str)):
        return text

    if (hasattr(text, '__unicode__')):
        text = text.__unicode__()

    if (hasattr(text, '__str__')):
        return text.__str__()

    return text.encode('utf-8')

class ITunesDB:
    def __init__(self, dbfile):
        try:
            self.dbconn = sqlite.connect(dbfile)
            self.InitDB()
        except Exception, e:
            print to_str(e)
            pass
        return

    def _cleanup_filename(self, filename):
        if (filename.startswith("file://localhost")):
            return unquote(filename[16:])
        else:
            return unquote(filename)

    def InitDB(self):
        try:
            self.dbconn.execute("PRAGMA synchronous = OFF")
            self.dbconn.execute("PRAGMA default_synchronous = OFF")
            self.dbconn.execute("PRAGMA journal_mode = OFF")
            self.dbconn.execute("PRAGMA temp_store = MEMORY")
            self.dbconn.execute("PRAGMA encoding = \"UTF-8\"")
        except Exception, e:
            print to_str(e)
            pass

        try:
            # config table
            self.dbconn.execute("""
            CREATE TABLE config (
               key varchar primary key,
               value varchar
            )""")
        except:
            pass

        try:
            # tracks table
            self.dbconn.execute("""
            CREATE TABLE tracks (
               id integer primary key,
               name varchar,
               persistent varchar,
               genreid integer,
               playcount integer,
               rating integer,
               year integer,
               bitrate integer,
               samplerate integer,
               artistid integer,
               albumtracknumber integer,
               albumid integer,
               filename varchar,
               filetypeid integer,
               playtime integer,
               protected boolean
            )""")
        except:
            pass

        try:
            # filetypes table
            self.dbconn.execute("""
            CREATE TABLE filetypes (
               id integer primary key,
               name varchar
            )""")
        except:
            pass

        try:
            # genres table
            self.dbconn.execute("""
            CREATE TABLE genres (
               id integer primary key,
               name varchar
            )""")
        except:
            pass

        try:
            # artists table
            self.dbconn.execute("""
            CREATE TABLE artists (
               id integer primary key,
               name varchar
            )""")
        except:
            pass

        try:
            # albums table
            self.dbconn.execute("""
            CREATE TABLE albums (
               id integer primary key,
               name varchar,
               rating integer,
               artistid integer
            )""")
        except:
            pass

        try:
            # playlists
            self.dbconn.execute("""
            CREATE TABLE playlists (
               id integer primary key,
               persistent varchar,
               name varchar,
               master boolean,
               visible boolean,
               allitems boolean
            )""")
        except:
            pass

        try:
            # playlist tracks
            self.dbconn.execute("""
            CREATE TABLE playlisttracks (
               playlistid integer,
               trackid integer,
               playorder integer
            )""")
        except Exception, e:
            pass

    def ResetDB(self):
        for table in ['tracks','albums','artists','playlists','filetypes',
                      'playlisttracks']:
            try:
                self.dbconn.execute("DROP TABLE %s" % table)
            except Exception, e:
                print to_str(e)
                pass
        try:
            self.InitDB()
        except Exception, e:
            print to_str(e)
            raise e

    def Commit(self):
        try:
            self.dbconn.commit()
        except Exception, e:
            print "Commit Error: " + to_str(e)
            pass        
            
    def GetConfig(self, key):
        try:
            cur = self.dbconn.cursor()
            cur.execute("""SELECT value 
                           FROM config 
                           WHERE key = ? LIMIT 1""",
                        (key,))
            row = cur.fetchone()
            if (row):
                return row[0]
            return None
        except:
            return None

    def SetConfig(self, key, value):
        if (self.GetConfig(key)==None):
            cur = self.dbconn.cursor()
            cur.execute("""INSERT INTO config(key,value)
                           VALUES(?,?)""",
                        (key, value))
            self.Commit()    #why did jinga add these?                    
        else:
            cur = self.dbconn.cursor()
            cur.execute("""UPDATE config
                           SET value=?
                           WHERE key=?""",
                        (value, key))
            self.Commit()    #why did jinga add these?                    

    def UpdateLastImport(self):
        self.SetConfig('lastimport', 'dummy')
        self.dbconn.execute("""UPDATE config
                               SET value=datetime('now')
                               WHERE key=?""",
                            ('lastimport',))
        self.Commit()

    def GetTableId(self, table, value, column='name', autoadd=False, autoclean=True):
        try:
            if (autoclean and not value):
                value = "Unknown"
            cur = self.dbconn.cursor()

            # query db for column with specified name
            cur.execute("SELECT id FROM %s WHERE %s = ?" % (table, column),
                        (value,))
            row = cur.fetchone()

            # create named ID if requested
            if not row and autoadd and value and len(value) > 0:
                nextid = cur.execute("SELECT MAX(id) FROM %s" % table).fetchone()[0]
                if not nextid:
                    nextid = 1
                else:
                    nextid += 1
                cur.execute("INSERT INTO %s(id, %s) VALUES (?,?)" % (table, column),
                            (nextid, value))
                return nextid # return new id
            return row[0] # return id
        except Exception, e:
            print to_str(e)
            raise e
            #return None    #jinga removed this

    def GetAlbumsByArtistId(self, id):
        albums = []
        try:
            cur = self.dbconn.cursor()
            cur.execute("SELECT id,name,artistid FROM albums WHERE artistid=?", (id,))
            for tuple in cur:
                albums.append(tuple)
        except Exception, e:
            print to_str(e)
            pass
        return albums

    def GetArtistId(self, artist, autoadd=False):
        return self.GetTableId('artists', artist, 'name', autoadd)
        
    def GetAlbumId(self, album, artist, autoadd=False, rating=None):
        albumid = self.GetTableId('albums', album, 'name', autoadd)
        if artist:
            artistid = self.GetArtistId(artist, autoadd=True)
            if rating:
                self.dbconn.execute("""UPDATE albums SET artistid = ?,
                                    rating=? WHERE id = ? """, 
                                    (artistid, rating, albumid))
            else:
                self.dbconn.execute("""UPDATE albums SET artistid = ?
                                    WHERE id = ? """, (artistid, albumid))
        return albumid

    def GetPlaylistId(self, playlist, autoadd=False):
        return self.GetTableId('playlists', playlist, 'name', autoadd)

    def GetGenreId(self, genre, autoadd=False):
        return self.GetTableId('genres', genre, 'name', autoadd)

    def GetFiletypeId(self, filetype, autoadd=False):
        return self.GetTableId('filetypes', filetype, 'name', autoadd)
            
    def GetNextId(self, tablename):
        cur = self.dbconn.cursor()
        cur.execute("SELECT MAX(id) FROM %s" % tablename)
        row = cur.fetchone()
        if not row:
            return 1
        return row[0]+1
        
    def GetArtists(self):
        artists = []
        try:
            cur = self.dbconn.cursor()
            cur.execute("SELECT id,name FROM artists")
            for tuple in cur:
                artists.append(tuple)
        except:
            pass
        return artists

    def GetPlaylists(self):
        playlists = []
        try:
            cur = self.dbconn.cursor()
            cur.execute("SELECT id,name FROM playlists WHERE visible != 'false'")
            for tuple in cur:
                playlists.append(tuple)
        except Exception, e:
            print to_str(e)
            pass
        return playlists

    def GetGenres(self):
        genres = []
        try:
            cur = self.dbconn.cursor()
            cur.execute("SELECT id,name FROM genres")
            for tuple in cur:
                genres.append(tuple)
        except Exception, e:
            print to_str(e)
            pass
        return genres

     
    def GetAlbums(self):
        albums = []
        try:
            cur = self.dbconn.cursor()
            cur.execute("SELECT id,name,artistid FROM albums")
            for tuple in cur:
                albums.append(tuple)
        except Exception, e:
            print to_str(e)
            pass
        return albums

    def GetTracksByArtist(self, artistid):
        tracks = []
        if not artistid:
            return None
        try:
            cur = self.dbconn.cursor()
            cur.execute("""SELECT T.id, T.name, T.playcount, T.rating, T.year,
                                  T.bitrate, T.albumtracknumber, T.filename,
                                  L.name as album, A.name as artist, T.playtime,
                                  G.name
                           FROM tracks T
                                LEFT JOIN albums L ON T.albumid = L.id
                                LEFT JOIN artists A ON T.artistid = A.id
                                LEFT JOIN genres G ON T.genreid = G.id
                           WHERE T.artistid = ? """, (artistid,))
            for tuple in cur:
                track = self._track_from_tuple(tuple)
                tracks.append(track)
            return tracks
        except Exception, e:
            print to_str(e)
            pass
        return tracks

    def _track_from_tuple(self, tuple):
        track = {}
        track['id'] = tuple[0]
        track['name'] = tuple[1]
        track['playcount'] = tuple[2]
        track['rating'] = tuple[3]
        track['year'] = tuple[4]
        track['bitrate'] = tuple[5]
        track['albumtracknumber'] = tuple[6]
        track['filename'] = tuple[7]
        track['album'] = tuple[8]
        track['artist'] = tuple[9]
        track['playtime'] = tuple[10]
        track['genre'] = tuple[11]
        return track

    def GetTracksInPlaylist(self, playlistid):
        tracks = []
        if not playlistid:
            return None
        try:
            cur = self.dbconn.cursor()
            cur.execute("""SELECT T.id, T.name, T.playcount, T.rating, T.year,
                                  T.bitrate, T.albumtracknumber, T.filename,
                                  L.name as album, A.name as artist, T.playtime,
                                  G.name
                           FROM playlisttracks P
                                LEFT JOIN tracks T ON P.trackid=T.id
                                LEFT JOIN albums L ON T.albumid = L.id
                                LEFT JOIN artists A ON T.artistid = A.id
                                LEFT JOIN genres G ON T.genreid = G.id
                           WHERE P.playlistid = ?
                           ORDER BY P.playorder """, (playlistid,))
            for tuple in cur:
                track = self._track_from_tuple(tuple)
                tracks.append(track)
            return tracks
        except Exception, e:
            print to_str(e)
            pass
        return tracks

    def GetTracksInAlbum(self, albumid):
        tracks = []
        if not albumid:
            return None
        try:
            cur = self.dbconn.cursor()
            cur.execute("""SELECT T.id, T.name, T.playcount, T.rating, T.year,
                                  T.bitrate,T.albumtracknumber, T.filename,
                                  L.name as album, A.name as artist, T.playtime,
                                  G.name
                           FROM tracks T
                                LEFT JOIN albums L ON T.albumid = L.id
                                LEFT JOIN artists A ON T.artistid = A.id
                                LEFT JOIN genres G ON T.genreid = G.id
                           WHERE T.albumid = ? """, (albumid,))
            for tuple in cur:
                track = self._track_from_tuple(tuple)
                tracks.append(track)
            return tracks
        except Exception, e:
            print to_str(e)
            pass
        return tracks

    def GetTracksInGenre(self, genreid):
        tracks = []
        if not genreid:
            return None
        try:
            cur = self.dbconn.cursor()
            cur.execute("""SELECT T.id, T.name, T.playcount, T.rating, T.year,
                                  T.bitrate,T.albumtracknumber, T.filename,
                                  L.name as album, A.name as artist, T.playtime,
                                  G.name
                           FROM tracks T
                                LEFT JOIN albums L ON T.albumid = L.id
                                LEFT JOIN artists A ON T.artistid = A.id
                                LEFT JOIN genres G ON T.genreid = G.id
                           WHERE G.id = ? """, (genreid,))
            for tuple in cur:
                track = self._track_from_tuple(tuple)
                tracks.append(track)
            return tracks
        except Exception, e:
            print to_str(e)
            pass
        return tracks

    def GetTracksWithRating(self, rating):
        tracks = []
        if not rating:
            return None
        maxrating = (int(rating)) * 20
        minrating = maxrating - 19
        print "Min Rating %d , Max Rating %d" % (minrating, maxrating)
        try:
            cur = self.dbconn.cursor()
            cur.execute("""SELECT T.id, T.name, T.playcount, T.rating, T.year,
                                  T.bitrate,T.albumtracknumber, T.filename,
                                  L.name as album, A.name as artist, T.playtime,
                                  G.name
                           FROM tracks T
                                LEFT JOIN albums L ON T.albumid = L.id
                                LEFT JOIN artists A ON T.artistid = A.id
                                LEFT JOIN genres G ON T.genreid = G.id
                           WHERE ( T.rating >= ? AND T.rating <= ? )""",
#                              OR ( L.rating >= ? AND L.rating <= ? )""", 
                        (minrating,maxrating)) #,minrating,maxrating))
            for tuple in cur:
                track = self._track_from_tuple(tuple)
                tracks.append(track)
            return tracks
        except Exception, e:
            print to_str(e)
            pass
        return tracks

    def AddTrackNew(self, track):
        if not track['Track ID']:
            return
        try:
            albumid = self.GetAlbumId(track['Album'], track['Artist'], autoadd=True, rating=track['Album Rating'])
            artistid = self.GetArtistId(track['Artist'], autoadd=True)
            genreid =  self.GetGenreId(track['Genre'], autoadd=True)
            self.dbconn.execute("""
            INSERT INTO tracks (id, name, genreid, artistid, albumid, filename,
                                playtime, persistent, year, rating)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
                                (int(track['Track ID']),
                                 track['Name'],
                                 genreid,
                                 artistid,
                                 albumid,
                                 self._cleanup_filename(track['Location']),
                                 track['Total Time'],
                                 track['Persistent ID'],
                                 track['Year'],
                                 track['Rating']))
        except sqlite.IntegrityError:
            pass
        except Exception, e:
            raise e

    def AddPlaylistNew(self, playlist):
        if not playlist['Playlist ID']:
            return
        try:
            self.dbconn.execute("""
            INSERT INTO playlists
              (id, persistent, name, master, visible, allitems)
            VALUES (?,?,?,?,?,?)""",
                                (playlist['Playlist ID'],
                                 playlist['Playlist Persistent ID'],
                                 playlist['Name'],
                                 playlist['Master'],
                                 playlist['Visible'],
                                 playlist['All Items']))
        except Exception, e:
            print to_str(e)
        try:
            order = 1
            playlistid = playlist['Playlist ID']
            for track in playlist['tracklist']:
                self.AddTrackToPlaylist(playlistid, track, order)
                order += 1
        except Exception, e:
            print to_str(e)

    def AddTrackToPlaylist(self, playlistid, trackid, order):
        if not playlistid or not trackid:
            return
        try:
            self.dbconn.execute("""
            INSERT INTO playlisttracks ( playlistid, trackid, playorder )
            VALUES (?,?,?)""", (playlistid, trackid, order))
        except Exception, e:
            print to_str(e)

class ParseCanceled(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class ITunesParserState:
    def __init__(self):
        self.level = 0
        self.tracks = False
        self.intrack = 0
        self.playlists = False
        self.inplaylist = False
        self.root = False
        self.key = False
        self.keyValue = ""
        self.value = ""
        self.valueType = ""

class ITunesParser:
    def __init__(self, track_callback=None, playlist_callback=None, config_callback=None, progress_callback=None):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.StartElement
        self.parser.EndElementHandler = self.EndElement
        self.parser.CharacterDataHandler = self.CharData
        self.state = ITunesParserState()
        self.ele = ""
        self.lastdata = False
        self.currentTrack = {}
        self.currentPlaylist = {}
        self.currentPlaylist['tracklist'] = []
        self.TrackCallback = track_callback
        self.PlaylistCallback = playlist_callback
        self.ProgressCallback = progress_callback
        self.ConfigCallback = config_callback
        for a in ['Album','Artist','Genre','Track ID','Location','Total Time',
                  'Persistent ID','Year','Rating','Album Rating']:
            self.currentTrack[a] = ""
        for a in ['Playlist ID','Playlist Persistent ID','Name',
                  'Master','Visible','All Items']:
            self.currentPlaylist[a] = ""
        self.currentPlaylist['tracklist'] = []

    def _reset_track(self):
        for a in self.currentTrack.keys():
            self.currentTrack[a] = ""

    def _reset_playlist(self):
        for a in self.currentPlaylist.keys():
            self.currentPlaylist[a] = ""
        self.currentPlaylist['tracklist'] = []

    def Parse(self, filename):
        try:
            #totalsize = os.path.getsize(filename)
            #readsize = 8192
            f = open(filename, "r")
            buf = f.read(8192)
            while buf:
                self.parser.Parse(buf, False)
                #readsize += 8192
                buf = f.read(8192)
            self.parser.Parse(buf, True)
            f.close()
        except Exception, e:
            print to_str(e)
            raise e

    def StartElement(self, name, attrs):
        state = self.state
        self.lastdata = False
        if state.tracks:
            state.intrack += 1
            state.key = name
        elif state.playlists:
            state.inplaylist += 1
            state.key = name

        if name == "key":
            state.key = True
        else:
            if state.key:
                state.valueType = name
            else:
                state.valueType = ""
            state.key = False
        state.level += 1

    def EndElement(self, name):
        self.lastdata = False
        state = self.state

        if state.tracks:
            # Handle updating a track
            if state.intrack == 2:
                self.currentTrack[state.keyValue] = state.value
            state.intrack -= 1
            if state.intrack == 0 and self.currentTrack.has_key('Track ID'):
                # Finished reading track, process it now
                try:
                    self.TrackCallback(self.currentTrack)
                except:
                    pass               
                try:
                    self.ProgressCallback(-1, -1)
                except:
                    pass
                #print self.currentTrack
                self._reset_track()

        elif state.playlists:
            # Handle updating a playlist
            if state.inplaylist == 2:
                if name == "true" or name == "false":
                    state.value = name
                self.currentPlaylist[state.keyValue] = state.value
            elif state.inplaylist == 4 and state.value:
                self.currentPlaylist['tracklist'].append(state.value)
            state.inplaylist -= 1
            if state.inplaylist == 0 and self.currentPlaylist.has_key('Playlist ID'):
                # Finished reading playlist, process it now
                try:
                    self.PlaylistCallback(self.currentPlaylist)
                except:
                    pass
                try:
                    self.ProgressCallback(-1, -1)
                except:
                    pass
                #print self.currentPlaylist
                self._reset_playlist()

        else:
            if state.level == 3 and state.value:
                try:
                    self.ConfigCallback(state.keyValue, state.value)
                except:
                    pass
        state.level -= 1

    def CharData(self, data):
        state = self.state
        if self.lastdata:
            data = self.lastdata + data
        self.lastdata = data

        #if state.tracks or state.playlists:
        # store key => value pairs
        if state.key:
            state.keyValue = data
        else:
            state.value = data.strip()

        # determine which section we are in
        if state.key:
            if data=="Tracks":
                state.tracks = True
                state.playlists = False
            elif data=="Playlists":
                state.tracks = False
                state.playlists = True
        return

def main():
    xmlfile = ""
    try:
        xmlfile = sys.argv[1]
    except:
        print "Usage itunes_parser.py <xmlfile>"
        sys.exit(1)

    db = ITunesDB("itunes.db")
    db.ResetDB()
    iparser = ITunesParser(db.AddTrackNew, db.AddPlaylistNew, db.SetConfig)
    try:
        iparser.Parse(xmlfile)
    except:
        print traceback.print_exc()
    db.Commit()

#def profile_main():
#    import hotshot, hotshot.stats
#    prof = hotshot.Profile("itunes.prof")
#    prof.runcall(main)
#    prof.close()
#    stats = hotshot.stats.load("itunes.prof")
#    stats.strip_dirs()
#    stats.sort_stats('time', 'calls')
#    stats.print_stats(20)

if __name__=="__main__":
    #profile_main()
    main()

