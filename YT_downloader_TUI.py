# -*- coding: utf8 -*-

from pytube import YouTube
from pytube import Playlist
from pytube import Channel
from pytube import exceptions as pytubeexceptions
import ffmpeg
import csv
import os
import sys
import re
from pathlib import PurePath, Path
import subprocess
import curses
from urllib.error import HTTPError


ytdir = "i:\\YouTube\\"
mylists = {
    "LGR Hardware Videos": "PLFDCFCDFCF7E7ACDD",
    "Уроки Arduino и программирования": "PLkW_wFQyyaEpfrCDA_F_e5vYeZ3WPCZWB",
    "Уроки Arduino и программирования": "PLgAbBhxTglwmVxDDC5TSYUI91oZ0LZQMw",
}

mychannels = {
    "arduinoLab": "@arduinoLab",
    "Электротехника и электроника для программистов": "@Zefar91",
}

resolutions = [
    "4320p",
    "2160p",
    "1440p",
    "1080p",
    "720p",
    "480p",
    "360p",
    "240p"
]

'''
Original idea taken from https://martechwithme.com/how-to-download-youtube-channel-videos-python/
Thanks!
'''


def safe_filename(s: str, max_length: int=255) -> str:
    """Sanitize a string making it safe to use as a filename.

    This function was based off the limitations outlined here:
    https://en.wikipedia.org/wiki/Filename.

    Patched by DIC

    :param str s:
        A string to make safe for use as a file name.
    :param int max_length:
        The maximum filename character length.
    :rtype: str
    :returns:
        A sanitized string.
    """
    # Characters in range 0-31 (0x00-0x1F) are not allowed in ntfs filenames.
    ntfs_characters = [chr(i) for i in range(0, 31)]
    characters = [
        r"\*",
        r'"',
        r"\/",
        r"\:",
        r"\<",
        r"\>",
        r"\?",
        r"\\",
        r"\^",
        r"\|",
        r"\~",
        r"\\\\",
        r"\.$",
    ]
    pattern = "|".join(ntfs_characters + characters)
    regex = re.compile(pattern, re.UNICODE)
    filename = regex.sub("", s).encode('cp1251', 'ignore').decode('cp1251')
    return filename[:max_length].rsplit(" ", 0)[0]


def DownloadVideo(stdscr, video_link, folder, filename,
                  maxres=None, adaptive=False):
    height, width = stdscr.getmaxyx()

    logwin = curses.newwin(height-6, 22, 6, 0)
    logwin.clear()
    logwin.border(' ', ' ', '_', ' ', '_', '_', ' ', ' ')
    logwin.refresh()

    coderwin = curses.newwin(height-6, width-23, 6, 23)
    coderwin.clear()
    coderwin.border(' ', ' ', '_', ' ', '_', '_', ' ', ' ')
    coderwin.refresh()

    fill_line(stdscr, 4, 0, ' ', width, 2)
    fill_line(stdscr, 5, 0, ' ', width, 2)
    stdscr.refresh()

    logwin.addstr(1, 0, f"Video Started. {maxres}\n", curses.color_pair(2))
    logwin.refresh()

    if maxres is None:
        video_file = YouTube(video_link).streams.\
            order_by('resolution').desc().first().download()
    else:
        try:
            video_file = YouTube(video_link).streams.\
                filter(adaptive=adaptive, progressive=True, res=maxres).\
                order_by('resolution').desc().first().download()
        except AttributeError as err:
            maxres = resolutions[resolutions.index(maxres) + 1]
            DownloadVideo(stdscr, video_link, folder, filename,
                          maxres=maxres, adaptive=True)
            return None
        except KeyError as err:
            maxres = resolutions[resolutions.index(maxres) + 1]
            DownloadVideo(stdscr, video_link, folder, filename,
                          maxres=maxres, adaptive=True)
            return None
        except HTTPError as err:
            coderwin.addstr(2, 0, err, curses.color_pair(5))
            coderwin.refresh()
            DownloadVideo(stdscr, video_link, folder, filename, maxres=maxres)
            return None
    logwin.addstr("Video Done\n", curses.color_pair(2))

    source_video = ffmpeg.input(video_file)
    vfdata = ffmpeg.probe(video_file)
    vdur = round(float(vfdata['format']['duration']))
    hours = str(vdur // 3600).zfill(2)
    minutes = str((vdur % 3600) // 60).zfill(2)
    seconds = str(vdur % 60).zfill(2)
    duration = f"Video duration: {hours}:{minutes}:{seconds}"
    fill_line(stdscr, 4, 0, duration, width, 2)
    stdscr.refresh()

    hasaudio = False
    for s in vfdata['streams']:
        if s['codec_type'] == 'audio':
            if s['codec_name'] == 'aac':
                hasaudio = True
                source_audio = ffmpeg.input(video_file)
                audio_file = video_file
                logwin.addstr("Audio Presents\n", curses.color_pair(2))
                logwin.refresh()

    if not hasaudio:
        logwin.addstr("Audio Started\n", curses.color_pair(2))
        logwin.refresh()
        audio_file = YouTube(video_link).streams.filter(only_audio=True).\
            order_by('abr').desc().first().download(filename_prefix="audio_")
        logwin.addstr("Audio Done\n", curses.color_pair(2))
        source_audio = ffmpeg.input(audio_file)

    logwin.addstr("Concatenation Started\n", curses.color_pair(2))
    logwin.refresh()

    cmd = f'ffmpeg -i "{video_file}" -i "{audio_file}" \
        -filter_complex [0][1]concat=a=1:n=1:v=1[s0] -map [s0] \
        "{folder}/{filename}"'

    reg = re.compile(r'(\d\d:\d\d:\d\d).*')

    with subprocess.Popen(cmd,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          # bufsize=1, universal_newlines=True) as process:
                          bufsize=1,
                          encoding='cp1251', errors='ignore') as process:
        for line in process.stderr:
            if 'frame=' in line:
                coderwin.addstr(1, 0, line, curses.color_pair(2))
                coderwin.refresh()

                ret = reg.search(line)
                if ret:
                    tmSplit = ret.group(1).split(':')
                    curDuration = (int(tmSplit[0]) * 3600) \
                        + (int(tmSplit[1]) * 60) \
                        + int(tmSplit[2])
                    perc = round(((curDuration / vdur) * 100), 1)

                    curdurstr = f'Video done    : {ret.group(1)} - {perc}%'
                    fill_line(stdscr, 5, 0, curdurstr, width, 2)
                    stdscr.refresh()

    logwin.addstr(4, 0, "Concatenation Done\n", curses.color_pair(2))
    logwin.refresh()
    os.unlink(video_file)
    if not hasaudio:
        os.unlink(audio_file)
    return None


def DownloadList(stdscr, list_videos, folder, maxres=None):
    height, width = stdscr.getmaxyx()

    video_count = 0
    total_video = len(list_videos)

    totalstr = f'{total_video} Videos Found'
    fill_line(stdscr, 1, 0, totalstr, width, 4)
    stdscr.refresh()

    list_videos_downloaded = []
    with open('youtube_export_history.csv', 'r', newline='') as csvf:
        spamwriter = csv.reader(csvf, quoting=csv.QUOTE_MINIMAL)
        for row in spamwriter:
            list_videos_downloaded.append(row[0])

    for video in list_videos:
        fill_line(stdscr, 2, 0, video, width, 1)
        stdscr.refresh()

        video_count = video_count + 1

        if video in list_videos_downloaded:
            cntstr = f'Video {video_count}/{total_video} already downloaded'
            fill_line(stdscr, 1, 20, cntstr, width, 4)
            stdscr.refresh()

        else:
            cntstr = f'Video {video_count}/{total_video} Started'
            fill_line(stdscr, 1, 20, cntstr, width, 4)

            try:
                video_title = YouTube(video).title
            except pytubeexceptions.PytubeError as err:
                print(err)
                continue

            video_name = safe_filename(video_title) + ".mp4"

            pathstr = Path(folder, video_name)
            fill_line(stdscr, 3, 0, video_name, width, 2)
            stdscr.refresh()

            if not os.path.exists(Path(folder, video_name)):
                DownloadVideo(
                    stdscr=stdscr,
                    video_link=video,
                    folder=folder,
                    filename=video_name,
                    maxres=maxres
                )
            else:
                cntstr = f'Video {video_count}/{total_video} downloaded before'
                fill_line(stdscr, 1, 20, cntstr, width, 4)
                stdscr.refresh()

            with open('youtube_export_history.csv', 'a', newline='') as csvf:
                spamwriter = csv.writer(csvf, quoting=csv.QUOTE_MINIMAL)
                spamwriter.writerow([video])
            local_csv_file = Path(folder, 'youtube_export_history.csv')
            with open(local_csv_file, 'a', newline='') as loccsvf:
                spamwriter = csv.writer(loccsvf, quoting=csv.QUOTE_MINIMAL)
                spamwriter.writerow([video_name, video])

            cntstr = f'Video {video_count}/{total_video} Done'
            fill_line(stdscr, 1, 20, cntstr, width, 4)
            stdscr.refresh()


def DownloadPlaylist(stdscr, palylist_link, folder, maxres=None):
    pure_link = palylist_link.replace("/featured", "/videos")
    list_videos = Playlist(pure_link).video_urls
    DownloadList(stdscr, list_videos, folder, maxres)


def DownloadChannel(stdscr, channel_link, folder, maxres=None):
    list_videos = Channel(channel_link).video_urls
    DownloadList(stdscr, list_videos, folder, maxres)


def fill_line(stdscr, line, col, string, width, pair):
    stdscr.addstr(line, col, string, curses.color_pair(pair))
    stdscr.addstr(line, len(string) + col, " " * (width - len(string) - col),
                  curses.color_pair(pair))


def main(stdscr):

    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_WHITE)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)

    if not os.path.exists('youtube_export_history.csv'):
        open('youtube_export_history.csv', 'w').close()

    total_folders = len(mylists)

    for folder_count, folder in enumerate(mylists):
        height, width = stdscr.getmaxyx()
        stdscr.clear()

        dirpath = Path(ytdir+folder)

        strdirpath = str(dirpath)
        fill_line(stdscr, 0, 0, strdirpath, width, 3)
        strfcnt = f'{folder_count}/{total_folders}'
        stdscr.addstr(0, width-len(strfcnt), strfcnt, curses.color_pair(3))

        maxres = "720p"
        if folder == "LGR Hardware Videos":
            maxres = "480p"

        if Path(dirpath).exists():
            csv_file = Path(dirpath, 'youtube_export_history.csv')
            if not os.path.exists(csv_file):
                open(csv_file, 'w').close()
            DownloadPlaylist(
                stdscr=stdscr,
                palylist_link="https://www.youtube.com/playlist?list="
                + mylists[folder],
                folder=dirpath,
                maxres=maxres)

    # for folder in mychannels:
    #     dirpath = Path(ytdir+folder)
    #     if Path(dirpath).exists():
    #         csv_file = Path(dirpath, 'youtube_export_history.csv')
    #         if not os.path.exists(csv_file):
    #             open(csv_file, 'w').close()
    #         DownloadChannel(
    #             channel_link="https://www.youtube.com/" + mychannels[folder],
    #             folder=dirpath,
    #             maxres="480p")

curses.wrapper(main)
