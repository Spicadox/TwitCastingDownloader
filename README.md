# TwitCastingScraper_m3u8
A script that scrapes all videos on a channel and writes all the index.m3u8 uri to a csv file
# TwitCastingDownloader
### Overview

A CLI script that can grab all video links and its respective m3u8 file from a TwitCasting channel. It can grab either videos from "shows" or "showclips".
Based on user specification all videos will either be downloaded(default) or information can be scraped to a csv file. TwitCastingDownloader can not only support whole channel
download/scrape, but also single link download/scrape.


### Installation

Requires the nonbinary library [BeautifulSoup](https://pypi.org/project/beautifulsoup4/)

A requirements text file has been included and the command `pip3 install -r requirements.txt` (or pip) can be used to install BeautifulSoup.

Note: The installation of BeautifulSoup is not required for the executable file.


### Options and Usages
```
usage: twitscrape.py [-h] [-l] [-n  [...]] [-o OUTPUT [OUTPUT ...]]

optional arguments:
  -h, --help        show this help message and exit
  -l, --link        The TwitCasting channel link to scrape and get the video links
  -n, --name        Name of the csv file. If not specified a default name will be used.
  -o, --output      The user's chosen absolute save path for the csv file
  -s, --scrape      Only scrape inputted url and saved as a csv file(don't download)
 ```
 Examples: 
 
 `python twitscape.py -l <TwitCasting Link>`
 
 `python twitscape.py -l <TwitCasting Link> -n "output.csv" -o <Path> -s`
