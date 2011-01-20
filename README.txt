iTunes plugin for XBMC
======================
This plugin imports an iTunes library into XBMC. After importing, you will
see categories that correspond with their iTunes counterparts.

* Artists
* Genres
* Albums
* Ratings
* Playlists

Configuration
=============
The plugin needs to know where your 'iTunes Music Library.xml' file is. If 
you haven't explicitly pointed iTunes to a non-standard library location, 
the default of "~/Music/iTunes/iTunes Music Library.xml" should work fine. 
Otherwise, please enter in the correct path in the plugin's settings dialog.

If you select "Auto update library", the plugin will compare the modification
time of your AlbumData.xml with its current database and update the database
automatically on start. This is disabled by default.

Translations
============
If you'd like to help translate this plugin to another language, please send
a patch to alfred_j_kwack at badsoda dot com.

If possible, patch against the most recent version at:

  https://github.com/AlfredJKwack/plugin.audio.itunes


Known Issues
============
Please log issues at https://github.com/AlfredJKwack/plugin.audio.itunes

Credits
=======
Anoop Menon (original code)
AlfredJKwack (current maintainer)
jingai (for showing the way)
