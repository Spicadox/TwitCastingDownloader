# TwitCastingDownloader
### Overview

A CLI program that can grab all video links and its respective m3u8 file from a TwitCasting channel. This program only supports VODs, and will not work with live screams. It can grab either videos from "shows" or "showclips".
Based on user specification all videos will either be downloaded(default) or m3u8 link can be scraped to a csv file. TwitCastingDownloader can not only support whole channel
download/scrape, but also single link download/scrape. Twitdl can also download locked videos given a passcode or passcode file is included, though this feature requires users to download selenium and chromedriver. 
The downloading of locked videos only work when trying to download the entire channel. In essence this program is an archiving tool for twitcasting channels.

Update 4/15/2021: ~~Due to recent changes to Twitcasting, downloads of videos are set at 1x speed, meaning the time it takes to download a video is equivalent to the video length. 
This was done to avoid the 502 error(rate limiting) imposed by Twitcasting.~~

Update 4/22/2021: Rate-limiting has been removed a couple days ago

Note: Now that yt-dlp has fixed their extractors for Twitcasting it is recommended to use yt-dlp instead. The only current advantage of this program over yt-dlp is the ability to more or less automate the processes of downloading/archiving all locked videos given a password text file.

### Installation
Requires [FFMPEG](https://ffmpeg.org/download.html) in the current working directory or in PATH.

Requires the non-standard modules: [requests](https://pypi.org/project/requests/), [BeautifulSoup](https://pypi.org/project/beautifulsoup4/), and [Selenium](https://pypi.org/project/selenium/). [ChromeDriver](https://chromedriver.chromium.org/) is also required after installing Selenium(recommended), though other web drivers for Edge, Firefox,and Opera is implemented, its use is not recommended. For other webdrivers see [Selenium](https://pypi.org/project/selenium/).

A requirements text file has been included and the command `pip3 install -r requirements.txt` (or pip) can be used to install the required dependencies(except FFMPEG and ChromeDriver).


### Options and Usages
```
usage: twitdl.py [-h] [-l] [-n  [...]] [-o OUTPUT [OUTPUT ...]]

optional arguments:
  -h, --help        show this help message and exit
  -l, --link        The TwitCasting channel link to operate on
  -n, --name        Name of the text archive file. If not specified a default name will be used. This argument is used to created the archive text file and this file can be used later in the --archive argument. This argument is no longer necessary with the introduction of --archive
  -o, --output      The user's chosen absolute save path for the download video and/or csv file
  -s, --scrape      Only scrape inputted url and saved as the result in csv file(don't download)
  -f, --file	    Location of the text file that contains a list of the secret words. Can not be called along side --passcode
  -p, --passcode    The secret word(passcode) to access the locked video. Can not be called along side --file
  -a, --archive     Location of the archive text file that contains a list of urls pertaining to downloaded videos
 ```
 Examples: 
 
 `python twitdl.py -l <TwitCasting Link>`
 
 `python twitdl.py -l <TwitCasting Link> -n "output.csv" -o <Path> -s`
 
 `python twitdl.py -l <TwitCasting Link> -f "password.txt" -a "archive.txt"`
 
 This example downloads all the videos from this url(going through all the pages), archives it into the specified archive.txt file and outputs all the video into the -o output directory
 `python twitdl.py -l https://twitcasting.tv/natsuiromatsuri/show/ -o "I:\Twitcasting Archive\夏色まつり🏮NatsuiroMatsuri" -a "I:\Hololive\Gen 1\夏色まつり🏮ホロライブ1期生_twitcasting_archive.txt"`
