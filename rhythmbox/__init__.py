# Mode: python; coding: utf-8; tab-width: 2;
#
# Copyright (C) 2010 - Fabio PhMS
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

import os
import rb
import rhythmdb
from ga import track_page_view
from re import sub
from thread import start_new_thread


def sanitize(text):
  if text and isinstance(text, str):
    text = sub("\s+", " ", text)
    text = sub("^\s", "", text)
    text = sub("\s$", "", text)

    text = sub("[áàâãäª]", "a", text.lower())
    text = sub("[éèêëЄ]",  "e", text)
    text = sub("[íìîï]",   "i", text)
    text = sub("[óòôõöº]", "o", text)
    text = sub("[úùûü]",   "u", text)
    text = sub("ç",        "c", text)

    #text = re.sub("[^\w\s\-]", "_", text)
    #text = re.sub("_+", "_", text)
    return text

  return ""


class MusicPlayerMetrics (rb.Plugin):
  def __init__(self):
    rb.Plugin.__init__(self)

  # What to do on activation
  def activate(self, shell):
    self.shell = shell
    self.db = shell.props.db
    self.current_entry = None

    # Reference the shell player
    sp = shell.props.shell_player

    # bind to "playing-song-changed" signal
    self.psc_id = sp.connect(
      'playing-song-changed',
      self.playing_song_changed
    )

  # What to do on deactivation
  def deactivate(self, shell):
    # Disconnect signals
    sp = shell.props.shell_player
    sp.disconnect(self.psc_id)

    # Remove references
    del self.db
    del self.shell
    del self.current_entry

  # The playing song has changed
  def playing_song_changed(self, sp, entry):
    if sp.get_playing(): self.set_entry(entry)

  # Sets our current RythmDB entry
  def set_entry(self, entry):
    if entry == self.current_entry: return
    if entry is None: return

    self.current_entry = entry

    # Extract songinfo from the current entry
    self.get_songinfo_from_entry()

  # Gets current songinfo from a rhythmdb entry
  def get_songinfo_from_entry(self):
    # Set properties list
    properties = {
      "title":rhythmdb.PROP_TITLE,
      "genre":rhythmdb.PROP_GENRE,
      "artist":rhythmdb.PROP_ARTIST,
      "album":rhythmdb.PROP_ALBUM,
      "track-number":rhythmdb.PROP_TRACK_NUMBER,
      "duration":rhythmdb.PROP_DURATION,
      "bitrate":rhythmdb.PROP_BITRATE
    }

    # Get song info from the current rhythmdb entry
    properties = dict(
      (k, self.db.entry_get(self.current_entry, v))
      for k, v in properties.items()
    )

    # Pass songinfo properties to XML write function
    self.track_music(properties)

  # Track music to GA
  def track_music(self, properties):
    artist = properties.get("artist")
    title =  properties.get("title")
    album =  properties.get("album")
    
    track = properties.get("track-number")
    track = ("%02d" % track) if (track) else None
    
    seconds = properties.get("duration")
    minutes = seconds / 60
    seconds = seconds % 60
    time = (" (%02d:%02d)" % (minutes, seconds))

    pageview = "/%s/%s/" % (artist.replace("/", "-"), album.replace("/", "-"))
    if track : pageview += track + "-"
    pageview += title
    pageview = sub("\s+", "_", pageview.lower())

    music = artist
    if (album != "Unknown") : music += " - " + album
    if track : music += " - " + track
    music += " - " + title + time

    time = ("%02d-%02d" % (minutes, seconds))

    bitrate = "%dkbps" % properties.get("bitrate")

    properties = {
       "Genre"   : sanitize(properties.get("genre")).title(),
       "Bitrate" : bitrate,
       "Time"    : time
    }

    start_new_thread(track_page_view, (pageview, music, properties))

