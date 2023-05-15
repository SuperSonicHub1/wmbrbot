from dataclasses import dataclass
from typing import List, Tuple
from urllib.parse import urljoin
from httpx import AsyncClient
from icalendar import Calendar, Event
from selectolax.parser import HTMLParser, Node

HOME_PAGE = "https://www.wmbr.org/"

# https://www.wmbr.org/www/sched
# Calendar ATM seems to be broken
ICAL_SCHEDULE = "https://www.wmbr.org/wmbr.ics"

# https://www.wmbr.org/www/listen
LIVE_STREAM = "https://wmbr.org:8002/hi"
# https://wmbr.org/WMBR_live_128.m3u: Invalid data found when processing input
# Works in MPV though...
# LIVE_STREAM = "https://wmbr.org/WMBR_live_128.m3u"

TRACK_BLASTER_HOME = "https://track-blaster.com/wmbr/index.php"

client = AsyncClient()

# async def parse_schedule() -> Calendar:
# 	res = await client.get(ICAL_SCHEDULE)
# 	res.raise_for_status()
# 	cal = Calendar.from_ical(res.text)
# 	return cal

# async def upcoming_and_ongoing_events() -> List[Event]:
# 	calendar = await parse_schedule()
# 	return calendar.subcomponents

async def upcoming_shows() -> str:
	res = await client.get(HOME_PAGE)
	res.raise_for_status()
	tree = HTMLParser(res.text)
	return "\n".join(node.text(strip=True, deep=True, separator=' ') for node in tree.css("div#upcoming_shows div"))

@dataclass
class Song:
	# TODO: Make this a timedelta
	time: str
	artist: str
	song: str
	album: str
	misc: str

	@staticmethod
	def from_row(row: Node) -> 'Song':
		time_div = row.css_first('div.col-Time:not(.hidden-sm)')
		artist_div = row.css_first('div.col-Artist:not(.hidden-sm)')
		song_div = row.css_first('div.col-Song:not(.hidden-sm)')
		album_div = row.css_first('div.col-AlbumFormat')
		misc_div = row.css_first('div.col-Misc')

		assert time_div, "Expected HTML not present"
		assert artist_div, "Expected HTML not present"
		assert song_div, "Expected HTML not present"
		assert album_div, "Expected HTML not present"
		assert misc_div, "Expected HTML not present"

		return Song(
			time_div.text(deep=True, strip=True, separator=' '),
			artist_div.text(deep=True, strip=True, separator=' '),
			song_div.text(deep=True, strip=True, separator=' '),
			album_div.text(deep=True, strip=True, separator=' '),
			misc_div.text(deep=True, strip=True, separator=' ')
		)

@dataclass
class Playlist:
	id: int
	dj: str
	show: str
	description: str
	tracks: List[Song]

	@staticmethod
	async def latest() -> 'Playlist':
		res = await client.get(
			"https://track-blaster.com/wmbr/playlist.php",
			params=dict(date="latest"),
			follow_redirects=True,
		)
		res.raise_for_status()
		tree = HTMLParser(res.text)

		descriptors = tree.css("div.col-xs-10.col-sm-11")
		assert len(descriptors) == 3, "Expected HTML not present"
		dj_div, show_div, description_div = descriptors

		# TODO: Parse show start and end data from here
		playlist_data_div = tree.css_first("div#playlist_data")
		assert playlist_data_div, "Expected HTML not present"

		return Playlist(
			int(res.url.params.get('id')),
			dj_div.text(deep=True, strip=True, separator=' '),
			show_div.text(deep=True, strip=True, separator=' '),
			description_div.text(deep=True, strip=True, separator=' '),
			[Song.from_row(row) for row in playlist_data_div.css("div[id*=row_]")]
		)

async def get_current_song() -> Tuple[Song, Playlist]:
	playlist = await Playlist.latest()
	return playlist.tracks[-1], playlist
