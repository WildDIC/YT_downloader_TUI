#!/usr/bin/env python3
# -*- coding: utf8 -*-

from pytube import YouTube, Playlist, Channel
from pytube import exceptions as pytubeexceptions
import ffmpeg
import json
import csv
import os
import sys
import re
import pickle
from deepdiff import DeepDiff
from pathlib import Path
import subprocess
import curses
import requests
from urllib.error import HTTPError
import http.client as HTTPClient
from datetime import datetime
import urllib.parse
import sqlite3
import CRC
import shutil
from time import sleep

image = "e:\\Data\\cover.jpg"

export_file = 'youtube_export_history.csv'

problem_file = 'youtube_problem_links.csv'

working_file = 'yt.working'

resolutions = [
    "4320p",
    "2160p",
    "1440p",
    "1080p",
    "720p",
    "480p",
    "360p",
    "240p",
    "144p"
]

'''
Original idea taken from
https://martechwithme.com/how-to-download-youtube-channel-videos-python/
Thanks!
'''


class YT_downloader():

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = self.stdscr.getmaxyx()

        self.stdscr.clear()
        self.stdscr.refresh()

        # Start colors in curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE,  curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK,  curses.COLOR_WHITE)
        curses.init_pair(4, curses.COLOR_GREEN,  curses.COLOR_WHITE)
        curses.init_pair(5, curses.COLOR_RED,    curses.COLOR_BLACK)

        self.clr = [
            0,
            curses.color_pair(1),
            curses.color_pair(2),
            curses.color_pair(3),
            curses.color_pair(4),
            curses.color_pair(5),
        ]

    def main(self):
        if not os.path.exists(export_file):
            open(export_file, 'w').close()

        with open('YT_downloader.json', encoding="utf8") as file:
            data = json.load(file)

            if len(sys.argv) > 1:
                if sys.argv[1] == "-update":
                    olddata = pickle.load(open("YT_downloader.pkl", "rb"))
                    diff = DeepDiff(olddata, data, view='tree')
                    mylists = {}
                    mychannels = {}
                    myvideos = {}
                    myshorts = {}
                    if 'dictionary_item_added' in diff:
                        for d in diff['dictionary_item_added']:
                            path = d.path(output_format='list')
                            if len(path) > 1:
                                if path[0] == 'mylists':
                                    mylists[path[1]] = d.t2
                                elif path[0] == 'mychannels':
                                    mychannels[path[1]] = d.t2
                                elif path[0] == 'myshorts':
                                    myshorts[path[1]] = d.t2
                                elif path[0] == 'myvideos':
                                    myvideos[path[1]] = []
                                    for i in d.t2:
                                        myvideos[path[1]].extend([i])
                    if 'iterable_item_added' in diff:
                        for i in diff['iterable_item_added']:
                            path = i.path(output_format='list')
                            if path[1] not in myvideos:
                                myvideos[path[1]] = []
                            myvideos[path[1]].extend([i.t2])
            else:
                mylists = data['mylists']
                mychannels = data['mychannels']
                myvideos = data['myvideos']
                myshorts = data['myshorts']

            ytdir = data['ytdir']
            defaultres = data['defaultres']

        total_folders = len(mylists)
        folder_count = 0

        for plid in mylists:
            folder_count += 1
            folder = mylists[plid]

            self.stdscr.clear()

            dirpath = Path(ytdir+folder)
            strdirpath = str(dirpath)
            self.fill_line(0, 0, strdirpath, 3)
            strfcnt = f" {folder_count}/{total_folders}"
            row = self.width-len(strfcnt)
            self.stdscr.addstr(0, row, strfcnt, self.clr[3])

            maxres = self.get_maxres(folder, defaultres)

            if Path(dirpath).exists():
                csv_file = Path(dirpath, export_file)
                if not os.path.exists(csv_file):
                    open(csv_file, 'w').close()
                self.DownloadPlaylist(
                    palylist_link="https://www.youtube.com/playlist?list="
                    + plid,
                    folder=dirpath,
                    maxres=maxres)

        total_folders = len(mychannels)
        folder_count = 0

        for folder in mychannels:
            folder_count += 1

            dirpath = Path(ytdir+folder)
            strdirpath = str(dirpath)
            self.fill_line(0, 0, strdirpath, 3)
            strfcnt = f'{folder_count}/{total_folders}'
            row = self.width-len(strfcnt)
            self.stdscr.addstr(0, row, strfcnt, self.clr[3])

            maxres = self.get_maxres(folder, defaultres)

            if Path(dirpath).exists():
                csv_file = Path(dirpath, export_file)
                if not os.path.exists(csv_file):
                    open(csv_file, 'w').close()
                self.DownloadChannel(
                    channel_link="https://www.youtube.com/@" +
                                 mychannels[folder] + "/videos",
                    folder=dirpath,
                    maxres=maxres)

        total_folders = len(myvideos)
        folder_count = 0

        for folder in myvideos:
            folder_count += 1

            dirpath = Path(ytdir+folder)
            strdirpath = str(dirpath)
            self.fill_line(0, 0, strdirpath, 3)
            strfcnt = f'{folder_count}/{total_folders}'
            row = self.width-len(strfcnt)
            self.stdscr.addstr(0, row, strfcnt, self.clr[3])

            maxres = self.get_maxres(folder, defaultres)

            if Path(dirpath).exists():
                csv_file = Path(dirpath, export_file)
                if not os.path.exists(csv_file):
                    open(csv_file, 'w').close()

                v_urls = list(map(lambda x: "https://www.youtube.com/watch?v="
                                            + x, myvideos[folder]))
                self.DownloadList(
                    list_videos=v_urls,
                    folder=dirpath,
                    maxres=maxres)

        total_folders = len(myshorts)
        folder_count = 0

        for folder in myshorts:
            folder_count += 1

            dirpath = Path(ytdir+folder)
            strdirpath = str(dirpath)
            self.fill_line(0, 0, strdirpath, 3)
            strfcnt = f'{folder_count}/{total_folders}'
            row = self.width-len(strfcnt)
            self.stdscr.addstr(0, row, strfcnt, self.clr[3])

            maxres = self.get_maxres(folder, defaultres)

            if Path(dirpath).exists():
                csv_file = Path(dirpath, export_file)
                if not os.path.exists(csv_file):
                    open(csv_file, 'w').close()
                self.DownloadChannel(
                    channel_link="https://www.youtube.com/@" +
                                 myshorts[folder] + "/shorts",
                    folder=dirpath,
                    maxres=maxres)

        pickle.dump(data, open("YT_downloader.pkl", "wb"))

    def safe_filename(self, s: str, max_length: int = 255) -> str:
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
        s = s.replace(" / ", " ")

        # Characters in range 0-31 (0x00-0x1F) are not allowed in NTFS.
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
            r"\\\\",
            r"\.$",
        ]
        pattern = "|".join(ntfs_characters + characters)
        regex = re.compile(pattern, re.UNICODE)
        filename = regex.sub(" ", s).\
            encode('cp1251', 'ignore').decode('cp1251').replace("  ", " ")
        return filename[:max_length].rsplit(" ", 0)[0]

    def find_name(self, dirpath, filename):
        fileindex = ''
        ext = filename[-4:]
        name = filename[:-4].split(' #')[0].strip()
        if os.path.isfile(dirpath+'\\'+name+ext):
            counter = 2
            fileindex = ' ' + str(counter)
            while os.path.isfile(dirpath+'\\'+name+fileindex+ext):
                counter += 1
                fileindex = ' ' + str(counter)
        return name, fileindex, ext

    def download_cover(self, videoId):
        names = [
            'maxresdefault',
            'sddefault',
            'hqdefault',
            'mqdefault',
            'default',
        ]
        for name in names:
            tmburl = 'https://i.ytimg.com/vi/' + videoId + '/' + name + '.jpg'
            response = requests.get(tmburl)
            if response.headers['Content-Length'] != '1097':
                break
        open(image, "wb").write(response.content)

    def DownloadVideo(self, video_link, folder, filename,
                      maxres=None, progressive=True):

        self.fill_line(4, 0, ' ', 2)
        self.fill_line(5, 0, ' ', 2)
        self.stdscr.refresh()

        logwin = curses.newwin(self.height-6, 23, 6, 0)
        logwin.clear()
        logwin.border(' ', ' ', '_', ' ', '_', '_', ' ', ' ')
        logwin.refresh()

        coderwin = curses.newwin(self.height-6, self.width-24, 6, 24)
        coderwin.clear()
        coderwin.border(' ', ' ', '_', ' ', '_', '_', ' ', ' ')
        coderwin.refresh()

        logwin.addstr(1, 0, "Video Started\n", self.clr[2])
        logwin.refresh()

        video = YouTube(video_link)

        # Скачивание видео по заданному разрешению
        if maxres is None:
            video_file = video.streams.\
                order_by('resolution').desc().first().download()
        else:
            try:
                print(video_link)
                streams = video.streams.order_by('resolution').\
                    filter(progressive=progressive).desc()
                res = dict((id, s.resolution) for id, s in enumerate(streams))
                print(res)
                if maxres in res.values():
                    key = [i for i, v in res.items() if v == maxres][0]
                else:
                    resid = resolutions.index(maxres)
                    if resolutions.index(res[0]) > resid:
                        if progressive:
                            self.DownloadVideo(video_link, folder, filename,
                                               maxres=maxres,
                                               progressive=False)
                            return None
                        else:
                            key = 0
                    else:
                        key = resolutions.index(res[0])
                        for i, v in res.items():
                            if resolutions.index(v) == resid - 1:
                                key = i
                                break

                logwin.addstr(f"Download Start {res[key]}\n", self.clr[2])
                logwin.refresh()

                # Если есть два потока с одинаковым разрешением, ищем кодек avc
                # Если будет скачан MP4 поток, то он не будет перекодироваться
                # Это сэкономит много времени и, часто, дисковое пространство
                if res[key] == res[key+1]:
                    if streams[key+1].parse_codecs()[0][:3] == 'avc':
                        key = key + 1

                size = "{:,}".format(streams[key].filesize).replace(",", " ")
                filesize = f"Video size: {size}"
                self.fill_line(4, 0, filesize, 2)
                self.stdscr.refresh()

                video_file = streams[key].download(max_retries=10)
            except HTTPError as err:
                print(err)
                self.DownloadVideo(video_link, folder, filename, maxres=maxres)
                return None
            except TimeoutError as err:
                print(err)
                self.DownloadVideo(video_link, folder, filename, maxres=maxres)
                return None
            except HTTPClient.IncompleteRead as err:
                print(err)
                if res.get(key + 1) is not None:
                    self.DownloadVideo(video_link, folder, filename, maxres=res[key + 1])
                with open(problem_file, 'a', newline='') as errcsvf:
                    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    spamwriter = csv.writer(errcsvf, quoting=csv.QUOTE_MINIMAL)
                    spamwriter.writerow([dt, video_link, 'IncompleteRead', res[key]])
                return None
            except pytubeexceptions.AgeRestrictedError as err:
                print(err)
                with open(problem_file, 'a', newline='') as errcsvf:
                    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    spamwriter = csv.writer(errcsvf, quoting=csv.QUOTE_MINIMAL)
                    spamwriter.writerow([dt, video_link, 'AgeRestrictedError'])
                return 'Restricted'
            except pytubeexceptions.LiveStreamError as err:
                print(err)
                with open(problem_file, 'a', newline='') as errcsvf:
                    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    spamwriter = csv.writer(errcsvf, quoting=csv.QUOTE_MINIMAL)
                    spamwriter.writerow([dt, video_link, 'LiveStreamError'])
                return 'LiveStream'

        logwin.addstr("Download Done\n", self.clr[2])
        logwin.refresh()

        vfdata = ffmpeg.probe(video_file)
        vdur = round(float(vfdata['format']['duration']))
        hours = str(vdur // 3600).zfill(2)
        minutes = str((vdur % 3600) // 60).zfill(2)
        seconds = str(vdur % 60).zfill(2)
        duration = f"Video duration: {hours}:{minutes}:{seconds}"
        self.fill_line(4, 0, duration, 2)
        self.stdscr.refresh()

        logwin.addstr("Video Done\n", self.clr[2])
        logwin.refresh()

        # Проверка аудиодорожки в скачанном файле, скачивание, если нет
        # Проверка видеодорожки в скачанном файле, MP4 не будем перекодировать
        hasaudio = False
        mp4video = False
        for s in vfdata['streams']:
            if s['codec_type'] == 'audio':
                if s['codec_name'] == 'aac':
                    hasaudio = True
                    audio_file = video_file
                    logwin.addstr("Audio Presents\n", self.clr[2])
                    logwin.refresh()
                    shutil.copyfile(f"{video_file}", f"_{filename}")
            if s['codec_type'] == 'video':
                if s['codec_name'] == 'h264':
                    mp4video = True

        if not hasaudio:
            logwin.addstr("Audio Started\n", self.clr[2])
            logwin.refresh()
            # Выбираем аудио с максимальным битрейтом
            audio_file = video.streams.filter(only_audio=True).\
                order_by('abr').desc().first().\
                download(filename_prefix="audio_")
            logwin.addstr("Audio Done\n", self.clr[2])

            logwin.addstr("Concatenation Started\n", self.clr[2])
            logwin.refresh()

            # Объединение видео и аудио
            # MP4 не будем перекодировать
            if mp4video:
                cmd = f'ffmpeg -y -i "{video_file}" -i "{audio_file}" \
                    -c:v copy -c:a aac "_{filename}"'
            else:
                cmd = f'ffmpeg -y -i "{video_file}" -i "{audio_file}" \
                    -filter_complex [0][1]concat=a=1:n=1:v=1[s0] -map [s0] \
                    "_{filename}"'

            reg = re.compile(r'(\d\d:\d\d:\d\d).*')

            with subprocess.Popen(cmd,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  bufsize=1,
                                  encoding='cp1251', errors='ignore') as process:
                for line in process.stderr:
                    if 'frame=' in line:
                        coderwin.addstr(1, 0, line, self.clr[2])
                        coderwin.refresh()

                        ret = reg.search(line)
                        if ret:
                            tmSplit = ret.group(1).split(':')
                            curDuration = (int(tmSplit[0]) * 3600) \
                                + (int(tmSplit[1]) * 60) \
                                + int(tmSplit[2])
                            perc = round(((curDuration / vdur) * 100), 1)

                            curdurstr = f'Video done    : {ret.group(1)} - {perc}%'
                            self.fill_line(5, 0, curdurstr, 2)
                            self.stdscr.refresh()

            logwin.addstr("Concatenation Done\n", self.clr[2])

        logwin.addstr("Add Cover\n", self.clr[2])
        logwin.refresh()

        # Скачивание и добавление обложки видео в файл
        self.download_cover(video.video_id)
        cmd = f'ffmpeg -y -i "_{filename}" -i "{image}" \
                -map 0:0 -map 0:1 -c copy \
                -map 1 -c:v:1 mjpeg -disposition:v:1 attached_pic \
                "{folder}/{filename}"'

        with subprocess.Popen(cmd,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              bufsize=1,
                              encoding='cp1251', errors='ignore') as process:
            for line in process.stderr:
                if 'frame=' in line:
                    coderwin.addstr(1, 0, line, self.clr[2])
                    coderwin.refresh()

        logwin.addstr("Cover added\n", self.clr[2])
        logwin.refresh()

        # Сохранение описания видео в .nfo файл
        logwin.addstr("Add NFO file\n", self.clr[2])
        logwin.refresh()

        nfo_name = filename[:-4] + ".nfo"
        pathstr = Path(folder, filename)
        nfopathstr = Path(folder, nfo_name)
        with open(nfopathstr, 'w', encoding="utf8") as f:
            f.write(video.description)
        filedate = pathstr.stat().st_ctime
        os.utime(nfopathstr, times=(filedate, filedate))

        # Копируем обложку в кэш KODI
        logwin.addstr("Add KODI thumbnail\n", self.clr[2])
        logwin.refresh()
        db_path = "v:\\KODI\\Database\\Textures13.db"
        tmb_path = 'v:\\KODI\\Thumbnails'
        f = str(pathstr)
        f = f[0].upper() + f[1:]

        encf = re.sub(r'%[0-9A-Z]{2}',
                      lambda matchobj: matchobj.group(0).lower(),
                      urllib.parse.quote(str(f))) \
                 .replace('%21', '!') \
                 .replace('%28', '(') \
                 .replace('%29', ')')
        path = 'image://video@' + encf + '/'
        bpath = path.lower().encode('utf8')
        c = CRC.crc32_mpeg2(msg=bpath)
        tmb_file = c[2:].zfill(8)
        tmb_fold = tmb_file[0]

        dst = f"{tmb_path}/{tmb_fold}/{tmb_file}.jpg"
        shutil.copyfile(image, dst)

        idata = ffmpeg.probe(image)
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(db_path)
        with conn:
            cur = conn.cursor()
            sql = 'INSERT INTO texture (url, cachedurl) VALUES (?, ?)'
            values = (path, f'{tmb_fold}/{tmb_file}.jpg')
            cur.execute(sql, values)
            idTmb = cur.lastrowid
            sql = 'INSERT INTO sizes \
                  (idtexture, size, width, height, usecount, lastusetime) \
                  VALUES (?, ?, ?, ?, ?, ?)'
            values = (
                idTmb, 1,
                idata['streams'][0]['width'],
                idata['streams'][0]['height'],
                1, dt
            )
            cur.execute(sql, values)
            logwin.addstr(f'Inserted ID={idTmb}\n', self.clr[2])
            logwin.addstr(tmb_file + '.jpg added\n', self.clr[2])
            logwin.refresh()

        # Удаление временных файлов
        os.unlink('_' + filename)
        os.unlink(video_file)
        if not hasaudio:
            os.unlink(audio_file)
        return None

    def DownloadList(self, list_videos, folder, maxres=None):
        video_count = 0
        total_video = len(list_videos)

        totalstr = f'{total_video} Videos Found'
        self.fill_line(1, 0, totalstr, 4)
        self.stdscr.refresh()

        list_videos_downloaded = []
        with open(export_file, 'r', newline='') as csvf:
            spamwriter = csv.reader(csvf, quoting=csv.QUOTE_MINIMAL)
            for row in spamwriter:
                list_videos_downloaded.append(row[0])

        for video in list_videos:
            video_count += 1

            self.fill_line(2, 0, video, 1)
            self.stdscr.refresh()

            if video in list_videos_downloaded:
                cntstr = (
                    f'Video {video_count}/{total_video}'
                    f' already downloaded'
                )
                self.fill_line(1, 20, cntstr, 4)
                self.stdscr.refresh()

            else:
                cntstr = f'Video {video_count}/{total_video} Started'
                self.fill_line(1, 20, cntstr, 4)

                try:
                    video_title = YouTube(video).title
                except pytubeexceptions.PytubeError as err:
                    print(err)
                    continue

                video_name = self.safe_filename(video_title) + ".mp4"
                name, fileindex, ext = self.find_name(str(folder), video_name)
                video_name = name + fileindex + ext

                self.fill_line(3, 0, video_name, 2)
                self.stdscr.refresh()

                if not os.path.exists(Path(folder, video_name)):
                    err = self.DownloadVideo(
                        video_link=video,
                        folder=folder,
                        filename=video_name,
                        maxres=maxres
                    )
                    if err in ("Restricted",
                               "LiveStream"
                               ):
                        continue
                else:
                    cntstr = (
                        f'Video {video_count}/{total_video}'
                        f' downloaded before'
                    )
                    self.fill_line(1, 20, cntstr, 4)
                    self.stdscr.refresh()

                with open(export_file, 'a', newline='') as csvf:
                    spamwriter = csv.writer(csvf, quoting=csv.QUOTE_MINIMAL)
                    spamwriter.writerow([video])
                local_csv_file = Path(folder, export_file)
                with open(local_csv_file, 'a', newline='') as loccsvf:
                    spamwriter = csv.writer(loccsvf, quoting=csv.QUOTE_MINIMAL)
                    spamwriter.writerow([video_name, video])

                cntstr = f'Video {video_count}/{total_video} Done'
                self.fill_line(1, 20, cntstr, 4)
                self.stdscr.refresh()

    def DownloadPlaylist(self, palylist_link, folder, maxres=None):
        pure_link = palylist_link.replace("/featured", "/videos")
        list_videos = Playlist(pure_link).video_urls
        self.DownloadList(list_videos, folder, maxres)

    def DownloadChannel(self, channel_link, folder, maxres=None):
        list_videos = Channel(channel_link).video_urls
        self.DownloadList(list_videos, folder, maxres)

    def fill_line(self, line, col, string, pair):
        self.stdscr.addstr(line, col, string, self.clr[pair])
        if len(string) < self.width:
            self.stdscr.addstr(line,
                               len(string) + col,
                               " " * (self.width - len(string) - col),
                               self.clr[pair])

    def get_maxres(self, folder, defaultres):
        res = [k for k, v in defaultres.items() if folder in v]
        if len(res) == 1:
            return res[0]
        return "720p"


def main(stdscr):
    with open(working_file, 'w') as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    YT_DL = YT_downloader(stdscr)
    try:
        YT_DL.main()
    except Exception as e:
        print(e)
    finally:
        os.unlink(working_file)

while True:
    if not os.path.isfile(working_file):
        curses.wrapper(main)
        break
    else:
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              'Waiting for other YTDL process finished')
        sleep(60)
