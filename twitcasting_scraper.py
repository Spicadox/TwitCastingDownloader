#!/usr/bin/env python
from bs4 import BeautifulSoup
import csv
import requests
import sys
import os
import argparse
import re
import subprocess

# Adds a link, name, and output argument
# Returns the arguments
def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--link',
                        type=str,
                        metavar='',
                        help="The TwitCasting channel link to scrape and get the video links")

    parser.add_argument('-n', '--name',
                        type=str,
                        nargs='+',
                        metavar='',
                        help="Name of the csv file. If not specified a default name will be used.")

    parser.add_argument('-o', '--output',
                        type=str,
                        nargs='+',
                        help="The user's chosen absolute save path for the csv file")

    parser.add_argument('-s', '--scrape',
                        action='store_true',
                        help="Scrape url and don't download")

    args = parser.parse_args()
    return args


# Set up the soup and return it while requiring a link as an argument
def soupSetup(cleanLink):
    try:
        url = cleanLink
    except Exception:
        sys.exit("Invalid URL")
    req = requests.get(url)
    bSoup = BeautifulSoup(req.text, "html.parser")
    return bSoup


# Takes -l argument and "sanitize" url
# Returns the "sanitized" url
def linkCleanUp(argLink):
    if(argLink is not None):
        url = argLink
    else:
        url = input("URL: ")
    #Take a look at this if statement back in master branch
    if("https://" not in url and "http://" not in url):
        url = "https://" + url
    if ("/showclips" in url):
        cleanLink = url.split("/showclips")[0]
        cleanLink = cleanLink + "/showclips/"
        filterType = "showclips"
        return cleanLink, filterType
    elif("/show" in url):
        cleanLink = url.split("/show")[0]
        cleanLink = cleanLink + "/show/"
        filterType = "show"
        return cleanLink, filterType
    # pattern is movie/[numbers]
    moviePattern = re.compile(r'movie/\d+')
    if("twitcasting.tv/" in url and moviePattern.findall(url) is []):
        if(url.rindex("/") == len(url) - 1):
            cleanLink = url + "show/"
            return cleanLink, "show"
        else:
            cleanLink = url + "/show/"
            return cleanLink, "show"
    # pattern example: [('https', '://twitcasting.tv/', 'natsuiromatsuri', '/movie/661406762')]
    moviePattern = re.compile(r'(https|http)(://twitcasting.tv/)(\w+|\d+)(/movie/\d+)')
    regMatchList = moviePattern.findall(url)
    if(len(regMatchList[0]) == 4):
        cleanLink = url
        return cleanLink, None
    else:
        sys.exit("Invalid Link")
    return cleanLink, None


# Function takes in two arguments: the base link and page number
# Returns a new link by contacting base link and page number
def updateLink(baseLink, pageNumber):
    baseLink = baseLink
    updatedLink = baseLink + str(pageNumber)
    return updatedLink


# Function takes in a directory path argument
# Returns user specified directory path, else a default path is provided
def getDirectory(argOutput):
    if(argOutput is not None):
        # if(" " in argOutput):
        #     directoryPath = " ".join(argOutput)
        # else:
        #     directoryPath = argOutput
        directoryPath = argOutput
    else:
        directoryPath = os.getcwd()
    return directoryPath


# Function takes in 3 arguments: soup, sanitized link, and user input file name
# Returns a proper filename for the csv file based on user input
def getFileName(soup, cleanLink, argName):
    #Add special character exception
    if(argName is not None):
        joinedName = argName
        # Does nothing
        # if(" " in argName):
        #     joinedName = "_".join(argName)
        if (".csv" not in joinedName and isinstance(joinedName, list)):
            fileName = joinedName.append(".csv")
        if(".csv" not in joinedName):
            fileName = joinedName + ".csv"
        else:
            fileName = joinedName
    else:
        channelName = soup.find(class_="tw-user-nav-name").text
        if ("/showclips" in cleanLink):
            fileName = channelName.strip() + "_showclips.csv"
            return fileName
        elif("/show" in cleanLink):
            fileName = channelName.strip() + "_shows.csv"
            return fileName
        else:
            fileName = channelName.strip() + "_urls.csv"
            return fileName
    fileName = "".join(fileName)
    return fileName


# Function takes in the file name and check if it exists
# If the file exists, then remove it(replace the file)
def checkFile(fileName):
    if(os.path.isfile(fileName)):
        os.remove(fileName)


# Function that takes in foldername and create dir if it doesn't exist
def createFolder(folderName):
    if os.path.isdir(folderName) is False:
        os.mkdir(folderName)


# Function that takes in two arguments: soup, and a filter of "show" or "showclips"
# Find the total page and gets the total link available to be scraped
# Returns a list that holds the total pages and total url available to be scraped
def urlCount(soup, filter):
    pagingClass = soup.find(class_="tw-pager")
    pagingChildren = pagingClass.findChildren()
    totalPages = pagingChildren[len(pagingChildren)-1].text
    print("Total Pages: " + totalPages)

    if("showclips" in filter):
        btnFilter = soup.find_all("a", class_="btn")
        clipFilter = btnFilter[1]
        clipBtn = clipFilter.text
        totalUrl = clipBtn.replace("Clip ", "").replace("(", "").replace(")", "")
        print(totalUrl)
        return [totalPages, totalUrl]
    else:
        countLive = soup.find(class_="tw-user-nav-list-count")
        totalUrl = countLive.text
        print("Total Links: " + totalUrl)
        return [totalPages, totalUrl]


# Function that takes in the index.m3u8 url
# Get m3u8 url, cleans it up and then return it
def m3u8_scrape(link):
    soup = soupSetup(link)
    m3u8_url = ""
    try:
        # Finds the tag that contains the url
        video_tag = soup.find(class_="video-js")["data-movie-playlist"]
        # Turns the tag string to a dict and then cleans it up
        video_dict = eval(video_tag)
        source_url = video_dict.get("2")[0].get("source").get("url")
        m3u8_url = source_url.replace("\\", "")
        print(m3u8_url)
    except:
        print("Private Video")
    return m3u8_url


# Function takes two arguments: the file name and soup
# Scrapes the video title and url and then write it into a csv file
# Returns the number of video url extracted for that page
def linkScrape(fileName, soup):
    video_list = []
    domainName = "https://twitcasting.tv"
    linksExtracted = 0
    with open(fileName, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        # find all video url
        url_list = soup.find_all("a", class_="tw-movie-thumbnail")
        # find all tag containing video title
        title_list = soup.find_all("span", class_="tw-movie-thumbnail-title")
        # find all tag containing date/time
        date_list = soup.find_all("time", class_="tw-movie-thumbnail-date")
        date_dict = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                     "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

        print("Links: " + str(len(url_list)))
        # add all video url to video list
        for link in url_list:
            video_list.append(domainName + link["href"])
        # loops through the link and title list in parallel
        for link, title, date in zip(video_list, title_list, date_list):
            m3u8_link = m3u8_scrape(link)
            # check to see if there are any m3u8 links
            if len(m3u8_link) is not 0:
                try:
                    date = date.text.strip()
                    video_date = re.search('(\d{4})/(\d{2})/(\d{2})', date)
                    day_date = video_date.group(3)
                    month_date = video_date.group(2)
                    year_date = video_date.group(1)
                except:
                    exit("Error getting dates")
                # Only write title if src isn't in the tag
                # Meaning it's not a private video title
                if not title.has_attr('src'):
                    full_date = "#" + year_date + month_date + day_date + " - "
                    title = [title.text.strip()]
                    title.insert(0, full_date)
                    title = "".join(title)
                    print(title)
                    csv_writer.writerow([title])
                linksExtracted = linksExtracted + 1
                csv_writer.writerow([m3u8_link])
                csv_writer.writerow(" ")
            else:
                print("Error can't find m3u8 links")
    return linksExtracted, video_list


# Function takes two arguments: the file name and soup
# Scrapes the video title and url and then write it into a csv file
# And then calls ffmpeg to download the stream
# Returns the number of video url extracted for that page
def batchDownloader(fileName, soup):
    video_list = []
    domainName = "https://twitcasting.tv"
    linksExtracted = 0
    with open(fileName, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        # find all video url
        url_list = soup.find_all("a", class_="tw-movie-thumbnail")
        # get channel name
        channel_name = soup.find("span", class_="tw-user-nav-name").text.strip()
        # find all tag containing video title
        title_list = soup.find_all("span", class_="tw-movie-thumbnail-title")
        # find all tag containing date/time
        date_list = soup.find_all("time", class_="tw-movie-thumbnail-date")

        print("Links: " + str(len(url_list)))
        # add all video url to video list
        for link in url_list:
            video_list.append(domainName + link["href"])
        # loops through the link and title list in parallel
        for link, title, date in zip(video_list, title_list, date_list):
            m3u8_link = m3u8_scrape(link)
            # check to see if there are any m3u8 links
            if len(m3u8_link) is not 0:
                # Use regex to get year, month, and day
                try:
                    date = date.text.strip()
                    video_date = re.search('(\d{4})/(\d{2})/(\d{2})', date)
                    day_date = video_date.group(3)
                    month_date = video_date.group(2)
                    year_date = video_date.group(1)
                except:
                    exit("Error getting dates")
                # Only write title if src isn't in the tag
                # Meaning it's not a private video title
                if not title.has_attr('src'):
                    full_date = "#" + year_date + month_date + day_date + " - "
                    title = [title.text.strip()]
                    title.insert(0, full_date)
                    title = "".join(title)
                    print(title)
                    csv_writer.writerow([title])
                linksExtracted = linksExtracted + 1
                csv_writer.writerow([m3u8_link])
                csv_writer.writerow(" ")

                # Download the stream
                video_title = title[1:]
                createFolder(channel_name)
                curr_dir = os.getcwd()
                download_dir = curr_dir + "\\" + channel_name
                ffmpeg_list = ['ffmpeg', '-i', m3u8_link, '-c:v', 'copy', '-c:a', 'copy']
                ffmpeg_list += [f'{download_dir}\\{video_title}.mp4']
                subprocess.run(ffmpeg_list)
                print("\nSuccess\n")
            else:
                print("Error can't find m3u8 links")
    return linksExtracted, video_list


# Function that takes three arguments: the fileName, link, and soup
# It calls the m3u8_scrape and writes the output to a csv file
# And then downloads that stream
def linkDownload(fileName, link, soup):
    linksExtracted = 0
    with open(fileName, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        print("Links: " + "1")
        m3u8_link = m3u8_scrape(link)
        if len(m3u8_link) is not 0:
            linksExtracted = linksExtracted + 1
            csv_writer.writerow([m3u8_link])
    return linksExtracted

# Function that takes two arguments: the filename and link
# It calls the m3u8_scrape and writes the output to a csv file
def singleLinkScrape(fileName, link):
    linksExtracted = 0
    with open(fileName, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        print("Links: " + "1")
        m3u8_link = m3u8_scrape(link)
        if len(m3u8_link) is not 0:
            linksExtracted = linksExtracted + 1
            csv_writer.writerow([m3u8_link])
    return linksExtracted

# Function that scrapes the entire channel while printing out
# various information onto the console
def scrapeChannel():
    # Links extracted
    linksExtracted = 0
    # Get commandline arguments
    args = arguments()
    # Get the clean twitcast channel link
    linkCleanedUp = linkCleanUp(args.link)
    channelLink = linkCleanedUp[0]
    channelFilter = linkCleanedUp[1]
    # Set up beautifulsoup
    soup = soupSetup(channelLink)
    # Get the filename
    fileName = getFileName(soup, channelLink, args.name)
    # Get the directory path
    directoryPath = getDirectory(args.output)
    # Set the directory path
    try:
        if isinstance(directoryPath, list):
            os.chdir(os.path.abspath(directoryPath[0]))
        else:
            os.chdir(os.path.abspath(directoryPath))
    except Exception as e:
        # sys.exit("Error setting output directory")
        sys.exit(e)
    # Check if the file exist and if it does delete it
    checkFile(fileName)
    # Count the total pages and links to be scraped
    if(channelFilter is not None):
        countList = urlCount(soup, channelFilter)
        totalPages = countList[0]
        totalLinks = countList[1]

        print("Filename: " + fileName)
        for currentPage in range(int(totalPages)):
            if (currentPage == int(totalPages)):
                print("\nPage: " + str(currentPage - 1))
            else:
                print("\nPage: " + str(currentPage + 1))
            if (currentPage != 0):
                updatedLink = updateLink(channelLink, currentPage)
                soup = soupSetup(updatedLink)
            # If --scrape is not specified then download video else just scrape
            if not (args.scrape):
                linksExtracted += linkScrape(batchDownloader, soup)[0]
            else:
                linksExtracted += linkScrape(fileName, soup)[0]
        print("\nTotal Links Extracted: " + str(linksExtracted) + "/" + totalLinks + "\nExiting")
    else:
        linksExtracted += singleLinkScrape(fileName, channelLink)
        print("\nTotal Links Extracted: " + str(linksExtracted) + "/" + "1" + "\nExiting")

if __name__ == '__main__':
    scrapeChannel()