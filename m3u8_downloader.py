#! /usr/bin/python3
"""M3U8 Downloader

Download the ts files according to the given m3u8 file.
"""

import os.path
from os import makedirs

import m3u8
from ffmpy import FFmpeg
from requests import Session

CHUNK_SIZE = 1024 * 1024    # 1MB
"""int: The chunk size (in byte) used by requests when downloading from the
server.
"""
FFMPEG_PATH = r'ffmpeg'

class M3U8Downloader:
    def __init__(self, *args, **kwargs):
        self.uri = args[0]
        self.m3u8 = m3u8.load(*args, **kwargs)

    def download(
            self,
            save_path='',
            merge=True,
            merged_file_name='merged.ts',
            ts_list_name='ts_list.txt'):
        if self.m3u8.is_variant:

            print('There are multiple m3u8 file listed by this file.')
            print('Select one to download.')
            print()

            for index, playlist in enumerate(self.m3u8.playlists):
                self._print_stream_info(playlist, index)

            try:
                fetch_index = int(input('Index> '))

                dounloader = M3U8Downloader(
                    self.m3u8.playlists[fetch_index].absolute_uri)
                dounloader.download(
                    save_path, merge, merged_file_name, ts_list_name)
            except (ValueError, IndexError):
                print('Invalid index.')

        else:
            makedirs(save_path, exist_ok=True)
            session = Session()

            if merge:
                merged_file_path = os.path.join(save_path, merged_file_name)
                FFmpeg(FFMPEG_PATH,
                       '-y',
                       inputs={self.uri: None},
                       outputs={merged_file_path: '-c copy'},
                      ).run()

            else:
                ts_files = []
                for segment in self.m3u8.segments:
                    filename = os.path.basename(segment.uri)
                    ts_file_path = os.path.join(save_path, filename)
                    with open(ts_file_path, 'wb') as ts_file:
                        self._download_and_write(session, segment, ts_file)
                    ts_files.append(filename)

                # Output the ts filenames
                ts_list_path = os.path.join(save_path, ts_list_name)
                with open(ts_list_path, 'w') as ts_list:
                    ts_list.write('\n'.join(ts_files))

    @classmethod
    def _download_and_write(cls, session, segment, output_file):
        req = session.get(segment.absolute_uri, stream=True)
        for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
            output_file.write(chunk)

    @staticmethod
    def _print_stream_info(playlist, index=0):
        print('INDEX: ' + str(index))

        stream_info = playlist.stream_info
        if stream_info.bandwidth:
            print('Bandwidth: {}'.format(stream_info.bandwidth))
        if stream_info.average_bandwidth:
            print('Average bandwidth: {}'.format(stream_info.average_bandwidth))
        if stream_info.program_id:
            print('Program ID: {}'.format(stream_info.program_id))
        if stream_info.resolution:
            print('Resolution: {}'.format(stream_info.resolution))
        if stream_info.codecs:
            print('Codecs: {}'.format(stream_info.codecs))
        print()


def main():
    downloader = M3U8Downloader('https://video.twimg.com/ext_tw_video/'
                                '884699254991667201/pu/pl/'
                                '6PuYiv2cXGlVZmB6.m3u8')
    downloader.download('output')

if __name__ == '__main__':
    main()
