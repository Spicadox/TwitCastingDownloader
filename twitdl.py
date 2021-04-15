#!/usr/bin/env python
import argparse
import csv
import json
import os
import re
import signal
import subprocess
import sys
import traceback

import requests
from bs4 import BeautifulSoup


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
                        help="The user's chosen absolute save path for the download video and/or csv file")

    parser.add_argument('-s', '--scrape',
                        action='store_true',
                        help="Only scrape inputted url and saved as the result in csv file(don't download)")

    parser.add_argument('-f', '--file',
                        type=str,
                        nargs='+',
                        help="Location of the text file that contains a list of the secret words. Can not be called along side --passcode")

    parser.add_argument('-p', '--passcode',
                        type=str,
                        nargs='+',
                        help="The secret word to access the locked video. Can not be called along side --file")

    parser.add_argument('-a', '--archive',
                        type=str,
                        nargs='?',
                        help="Location of the archive text file that contains a list of urls pertaining to downloaded videos")

    args = parser.parse_args()
    return args


# Set up the soup and return it while requiring a link as an argument
def soupSetup(cleanLink):
    try:
        url = cleanLink
    except Exception:
        sys.exit("Invalid URL")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
        'Origin': 'https://twitcasting.tv'}
    req = requests.get(url, headers=headers)
    bSoup = BeautifulSoup(req.text, "html.parser")
    return bSoup


# Takes -l argument and "sanitize" url
# If link doesn't end with /show or /showclips then invalid link
# Returns the "sanitized" url
def linkCleanUp(argLink):
    cleanLink = None
    if (argLink is not None):
        url = argLink
    else:
        url = input("URL: ")
    # Download m3u8 link if provided
    downloadM3u8(url)
    # Take a look at this if statement back in master branch
    if ("https://" not in url and "http://" not in url):
        url = "https://" + url
    if ("/showclips" in url):
        cleanLink = url.split("/showclips")[0]
        cleanLink = cleanLink + "/showclips/"
        filterType = "showclips"
        return cleanLink, filterType
    elif ("/show" in url):
        cleanLink = url.split("/show")[0]
        cleanLink = cleanLink + "/show/"
        filterType = "show"
        return cleanLink, filterType
    # pattern is movie/[numbers]
    moviePattern = re.compile(r'movie/\d+')
    if ("twitcasting.tv/" in url and moviePattern.findall(url) is []):
        if (url.rindex("/") == len(url) - 1):
            cleanLink = url + "show/"
            return cleanLink, "show"
        else:
            cleanLink = url + "/show/"
            return cleanLink, "show"
    # pattern example: [('https', '://twitcasting.tv/', 'natsuiromatsuri', '/movie/661406762')]
    moviePattern = re.compile(r'(https|http)(://twitcasting.tv/)(.*?)(/movie/\d+)')
    regMatchList = moviePattern.findall(url)
    try:
        if (len(regMatchList[0]) == 4):
            cleanLink = url
            return cleanLink, None
    except:
        sys.exit("Invalid Link")
    return cleanLink, None


# Function takes index.m3u8 link and downloads it in cwd as {video_id}.mp4 and then exits
def downloadM3u8(m3u8):
    # Check if its an m3u8 link
    # https://dl01.twitcasting.tv/tc.vod/v/674030808.0.2-1618443661-1618472461-4ec6dd13-901d44e31383a107/fmp4/index.m3u8
    moviePattern = re.compile(r'(https|http)(:\/\/.*\.)(twitcasting\.tv\/tc\.vod\/v\/)(\d+)(.*)(\/fmp4\/index\.m3u8)$')
    regMatchList = moviePattern.findall(m3u8)
    if len(regMatchList) > 0:
        video_id = regMatchList[0][3]
        download_dir = os.getcwd()
        # Use -re, -user_agent, and -headers to set x1 read speed and avoid 502 error
        # Use -n to avoid overwriting files and then avoid re-encoding by using copy
        ffmpeg_list = ['ffmpeg', '-re', '-user_agent',
                       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
                       '-headers', "Origin: https://twitcasting.tv"]
        ffmpeg_list += ['-n', '-i', m3u8, '-c:v', 'copy', '-c:a', 'copy']
        ffmpeg_list += [f'{download_dir}\\{video_id}.mp4']
        try:
            print("Downloading from index.m3u8\n")
            subprocess.run(ffmpeg_list, check=True)
        except Exception:
            sys.exit("Error executing ffmpeg")
        print("\nExecuted")
        sys.exit("\nDownloaded Successfully")

# Function takes in two arguments: the base link and page number
# Returns a new link by contacting base link and page number
def updateLink(baseLink, pageNumber):
    baseLink = baseLink
    updatedLink = baseLink + str(pageNumber)
    return updatedLink


# Function takes in a directory path argument
# Returns user specified directory path, else a default path is provided
def getDirectory(argOutput):
    if (argOutput is not None):
        directoryPath = "".join(argOutput)
        print("Directory Path: " + directoryPath)
    else:
        directoryPath = os.getcwd()
    return directoryPath


# Function takes in 3 arguments: soup, sanitized link, and user input file name
# Returns a proper filename for the csv file based on user input
def getFileName(soup, cleanLink, argName):
    # Add special character exception
    if (argName is not None):
        # Check if the argName contains illegal characters
        joinedName = checkFileName(argName)
        # Does nothing
        # if(" " in argName):
        #     joinedName = "_".join(argName)
        if (".csv" not in joinedName and isinstance(joinedName, list)):
            fileName = joinedName.append(".csv")
        if (".csv" not in joinedName):
            fileName = joinedName + ".csv"
        else:
            fileName = joinedName
    else:
        channelName = soup.find(class_="tw-user-nav-name").text
        channelName = checkFileName(channelName)
        if ("/showclips" in cleanLink):
            fileName = channelName.strip() + "_showclips.csv"
            return fileName
        elif ("/show" in cleanLink):
            fileName = channelName.strip() + "_shows.csv"
            return fileName
        else:
            fileName = channelName.strip() + "_urls.csv"
            return fileName
    fileName = "".join(fileName)
    return fileName


def getArchive(archiveArg):
    archiveExist = False
    currentDirectory = os.getcwd()
    try:
        if archiveArg is not None:
            archivePath = "".join(archiveArg)
            if not archiveArg.endswith(".txt"):
                archiveArg = archiveArg + ".txt"
            print("Archive Path: " + archivePath)
        else:
            archivePath = currentDirectory
    except Exception as exception:
        print(str(exception) + "\nError, creating archive.txt file in current working directory")
        archivePath = currentDirectory
    if os.path.isfile(archivePath) or os.path.isfile(str(currentDirectory) + "\\" + archiveArg):
        archiveExist = True
    return archivePath, archiveExist


# Function takes in the file name and check if it exists
# If the file exists, then remove it(replace the file)
def checkFile(fileName):
    if (os.path.isfile(fileName)):
        os.remove(fileName)


# Function takes in the file name and check if it contains illegal characters
# If it contains an illegal character then remove it and return the new file name without the illegal character
def checkFileName(fileName):
    invalidName = re.compile(r"[\\*?<>:\"/\|]")
    newFileName = fileName
    if re.search(invalidName, fileName) is not None:
        newFileName = re.sub(invalidName, "", fileName)
        print("\nInvalid File Name Detected\nNew File Name: " + newFileName)
    return newFileName


# Function that takes in foldername and create dir if it doesn't exist
def createFolder(folderName):
    folderName = checkFileName(folderName)
    if os.path.isdir(folderName) is False:
        os.mkdir(folderName)


# Function that takes in two arguments: soup, and a filter of "show" or "showclips"
# Find the total page and gets the total link available to be scraped
# Returns a list that holds the total pages and total url available to be scraped
def urlCount(soup, filter):
    pagingClass = soup.find(class_="tw-pager")
    pagingChildren = pagingClass.findChildren()
    totalPages = pagingChildren[len(pagingChildren) - 1].text
    print("Total Pages: " + totalPages)

    if ("showclips" in filter):
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
        print(video_tag)
        # Turns the tag string to a dict and then cleans it up
        video_dict = eval(video_tag)
        source_url = video_dict.get("2")[0].get("source").get("url")
        m3u8_url = source_url.replace("\\", "")
        print("m3u8 link: " + m3u8_url)
    except:
        print("Private Video")
    return m3u8_url


# Function takes three arguments: the file name, soup, and boolean value batch
# Scrapes the video title and url and then write it into a csv file
# Returns the number of video url extracted for that page
def linkScrape(fileName, soup, batch, passcode_list):
    video_list = []
    domainName = "https://twitcasting.tv"
    linksExtracted = 0
    with open(fileName, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        # If it's just one link scrape
        if not batch:
            print("Links: " + "1")
            m3u8_link = m3u8_scrape(soup)
            if len(m3u8_link) != 0:
                linksExtracted = linksExtracted + 1
                csv_writer.writerow([m3u8_link])
        # If it's a channel scrape
        else:
            # find all video url
            url_list = soup.find_all("a", class_="tw-movie-thumbnail")
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
                if len(m3u8_link) != 0:
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
                        print("Title: " + title)
                        # csv_writer.writerow([title])
                    linksExtracted = linksExtracted + 1
                    csv_writer.writerow([m3u8_link])
                    csv_writer.writerow(" ")
                else:
                    print("Error can't find m3u8 links")
    return linksExtracted, video_list


# Function takes four arguments: soup, directory path, boolean value batch, and the channel link
# Scrapes for video info
# And then calls ffmpeg to download the stream
# Returns the number of video url extracted for that page
def linkDownload(soup, directoryPath, batch, channelLink, passcode_list, archive_info):
    video_list = []
    m3u8_link = []
    domainName = "https://twitcasting.tv"
    linksExtracted = 0
    curr_dir = directoryPath
    archivePath = archive_info[0]
    archiveExist = archive_info[1]
    m3u8_url = ""
    csv_format = 'w'
    # Batch download
    if batch:
        # Maybe consider separating extractor from downloader
        # find all video url
        url_list = soup.find_all("a", class_="tw-movie-thumbnail")
        # get channel name
        channel_name = soup.find("span", class_="tw-user-nav-name").text.strip()
        # find all tag containing video title
        title_list = soup.find_all("span", class_="tw-movie-thumbnail-title")
        # find all tag containing date/time
        date_list = soup.find_all(class_="tw-movie-thumbnail-date")

        createFolder(channel_name)
        download_dir = curr_dir + "\\" + checkFileName(channel_name)

        # add all video url to video list
        for link in url_list:
            video_list.append(domainName + link["href"])

        # loops through the link and title list in parallel
        for link, title, date in zip(video_list, title_list, date_list):
            try:
                csv_list = []
                if archivePath is not None:
                    if archiveExist:
                        csv_format = 'a'
                        # List index out of range error when theres extra/less space
                        with open(archivePath, 'r', newline="") as csv_file:
                            csv_reader = csv.reader(csv_file)
                            for line in csv_reader:
                                csv_list.append(line[0])
                        if link in csv_list:
                            continue
                    else:
                        csv_format = 'w'
            except Exception as archiveException:
                sys.exit(str(archiveException) + "\n Error occurred creating an archive file")

            # If there is more than 1 password and it's a private video
            if len(passcode_list) > 1 and len(title.contents) == 3:
                # Try importing selenium
                try:
                    from selenium import webdriver
                    from selenium.webdriver.common.keys import Keys
                    from selenium.common.exceptions import NoSuchElementException
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    from selenium.webdriver.common.by import By

                    driver = webdriver.Chrome()
                    driver.get(link)
                except webdriver or Keys as importException:
                    sys.exit(str(importException) + "\nError importing")

                # Find the password field element on the page
                password_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[name='password']")))

                # While the password element field remains and correct password hasn't been entered
                current_passcode = None
                while len(password_element) > 0:
                    password_element = WebDriverWait(driver, 15).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[name='password']")))
                    # Go through all the passcode until the password element field is gone
                    for passcode in passcode_list:
                        current_passcode = passcode
                        password_element = WebDriverWait(driver, 15).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[name='password']")))
                        button_element = WebDriverWait(driver, 15).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, "tw-button-secondary.tw-button-small")))

                        password_element[0].send_keys(passcode)
                        button_element[0].click()
                        # If the password field element remains and there are still more passcodes then try again with another passcode
                        try:
                            password_element = WebDriverWait(driver, 10).until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[name='password']")))
                            if len(password_element) > 0:
                                continue
                        except:
                            break
                    # If after checking all the passcode and it's still locked then break out the while loop and move on to another video
                    if len(password_element) >= 0:
                        break

                # Try to find the video element
                try:
                    m3u8_tag = WebDriverWait(driver, 15).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-movie-playlist]")))
                    # If video element is found then get the m3u8 url
                    if len(m3u8_tag) > 0:
                        m3u8_tag_dic = json.loads(m3u8_tag[0].get_attribute("data-movie-playlist"))
                        source_url = m3u8_tag_dic.get("2")[0].get("source").get("url")
                        m3u8_url = source_url.replace("\\", "")
                        m3u8_link = m3u8_url
                        # If a passcode was used/set then remove it from the passcode_list
                        # Helps speeds up entering the passcode by removing used passcode
                        if current_passcode is not None:
                            passcode_list.remove(current_passcode)
                        driver.quit()
                except Exception as noElement:
                    print(str(noElement) + "\nCan't find private m3u8 tag")
                    driver.quit()

            # Send m3u8 url and ensure it's a valid m3u8 link
            m3u8_link = m3u8_scrape(link)
            if len(m3u8_link) == 0:
                m3u8_link = m3u8_url

            # check to see if there are any m3u8 links
            if len(m3u8_link) != 0:
                # Use regex to get year, month, and day
                try:
                    date = date.text.strip()
                    # Find date of the video in year/month/day
                    video_date = re.search('(\d{4})/(\d{2})/(\d{2})', date)
                    day_date = video_date.group(3)
                    month_date = video_date.group(2)
                    year_date = video_date.group(1)
                except:
                    exit("Error getting dates")
                # Only write title if src isn't in the tag
                # Meaning it's not a private video title
                if not title.has_attr('src'):
                    full_date = year_date + month_date + day_date + " - "
                    title = full_date + "".join(title.text.strip())
                    print("Title: " + str(title))

                linksExtracted = linksExtracted + 1
                # Use -re, -user_agent, and -headers to set x1 read speed and avoid 502 error
                # Use -n to avoid overwriting files and then avoid re-encoding by using copy
                ffmpeg_list = ['ffmpeg', '-re', '-user_agent',
                               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
                               '-headers', "Origin: https://twitcasting.tv"]
                ffmpeg_list += ['-n', '-i', m3u8_link, '-c:v', 'copy', '-c:a', 'copy']
                ffmpeg_list += [f'{download_dir}\\{title}.mp4']
                try:
                    subprocess.run(ffmpeg_list, check=True)
                except Exception:
                    sys.exit("Error executing ffmpeg")
                print("\nExecuted")
                # Reset m3u8 link and url
                m3u8_link = ""
                m3u8_url = ""
                if archivePath is not None:
                    with open(archivePath, csv_format, newline='') as csv_file:
                        archiveExist = True
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow([link])
                        # Set appended to be true so on error this appended link can be tested and removed
                        print("appended\n")
            else:
                print("Error can't find m3u8 links")

    # Single link download
    else:
        try:
            title = soup.find("span", id="movie_title_content").text.strip()
            title = checkFileName(title)
        except:
            title = "temp"
        # find all tag containing date/time
        date = soup.find("time", class_="tw-movie-thumbnail-date").text.strip()
        m3u8_link = m3u8_scrape(channelLink)
        # check to see if there are any m3u8 links
        if len(m3u8_link) != 0:
            # Use regex to get year, month, and day
            try:
                video_date = re.search('(\d{4})/(\d{2})/(\d{2})', date)
                day_date = video_date.group(3)
                month_date = video_date.group(2)
                year_date = video_date.group(1)
            except:
                exit("Error getting dates")

            full_date = year_date + month_date + day_date + " - "
            title = full_date + "".join(title)
            print(title)
            linksExtracted = linksExtracted + 1
            download_dir = curr_dir
            # Use -re, -user_agent, and -headers to set x1 read speed and avoid 502 error
            # Use -n to avoid overwriting files and then avoid re-encoding by using copy
            ffmpeg_list = ['ffmpeg', '-re', '-user_agent',
                           "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
                           '-headers', "Origin: https://twitcasting.tv"]
            ffmpeg_list += ['-n', '-i', m3u8_link, '-c:v', 'copy', '-c:a', 'copy']
            ffmpeg_list += [f'{download_dir}\\{title}.mp4']
            try:
                subprocess.run(ffmpeg_list, check=True)
            except Exception:
                sys.exit("Error executing ffmpeg")
            print("\nExecuted")
        else:
            sys.exit("Error can't find m3u8 links\n")
    return linksExtracted, video_list


# Function that scrapes/download the entire channel or single link
# while printing out various information onto the console
def main():
    # Check for keyboard interrupt
    signal.signal(signal.SIGINT, lambda x, y: sys.exit("\nKeyboard Interrupt"))
    # Links extracted
    linksExtracted = 0
    # Get commandline arguments
    args = arguments()
    # Get the clean twitcast channel link
    try:
        linkCleanedUp = linkCleanUp(args.link)
        channelLink = linkCleanedUp[0]
        channelFilter = linkCleanedUp[1]
    except Exception as linkError:
        sys.exit(linkError + "\nInvalid Link")

    # Check and make sure both --file and --passcode isn't specified at once
    passcode_list = []
    if args.file and args.passcode:
        sys.exit("You can not specify both --file and --passcode at the same time.\nExiting")
    # Check if --file is supplied and if so create a list of the passcode
    if args.file:
        try:
            pass_file = getDirectory(args.file)
            with open(pass_file, 'r', newline='') as csv_file:
                csv_reader = csv.reader(csv_file)
                passcode_list = list(csv_reader)
        except Exception as f:
            sys.exit(f + "\nError occurred when opening passcode file")
    # Check if --passcode is specified and if it is set the passcode to a passcode_list
    if args.passcode:
        passcode_list = args.passcode
    if args.archive:
        archive_info = getArchive(args.archive)
    else:
        archive_info = [None, False]

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
    # If it's a batch download/scrape set to true
    batch = channelFilter is not None
    # Initiate batch download or scrape
    if batch:
        countList = urlCount(soup, channelFilter)
        totalPages = countList[0]
        totalLinks = countList[1]

        if args.scrape:
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
            if not args.scrape:
                linksExtracted += linkDownload(soup, directoryPath, batch, channelLink, passcode_list, archive_info)[0]
                if batch:
                    print("\nTotal Links Extracted: " + str(linksExtracted) + "/" + totalLinks + "\nExiting")
                else:
                    sys.exit("\nTotal Links Extracted: " + str(linksExtracted) + "/" + "1" + "\nExiting")

            else:
                linksExtracted += linkScrape(fileName, soup, batch, passcode_list)[0]
                if batch:
                    print("\nTotal Links Extracted: " + str(linksExtracted) + "/" + totalLinks + "\nExiting")
                else:
                    print("\nTotal Links Extracted: " + str(linksExtracted) + "/" + "1" + "\nExiting")
    # Initiate single download or scrape
    else:
        if not args.scrape:
            linksExtracted += linkDownload(soup, directoryPath, batch, channelLink, passcode_list, archive_info)[0]
            print("\nTotal Links Extracted: " + str(linksExtracted) + "/" + "1" + "\nExiting")
        else:
            linksExtracted += linkScrape(fileName, channelLink, batch, passcode_list)[0]
            print("\nTotal Links Extracted: " + str(linksExtracted) + "/" + "1" + "\nExiting")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        # sys.exit(str(e) + "\nUnexpected Error")
        traceback.print_exc()
