import os
import tempfile
from pathlib import Path

from get_frames import unprocessed_videos


def test_unprocessd_videos():

    with tempfile.TemporaryDirectory() as videos_dir:
        with tempfile.TemporaryDirectory() as results_dir:
            same_video = os.path.join(videos_dir, 'same_video.mp4')
            same_result = os.path.join(results_dir, 'same_video.txt')

            diff_video = os.path.join(videos_dir, 'diff_video.mp4')
            diff_result = os.path.join(results_dir, 'oediv_ffid.txt')

            for path in [same_result, same_video, diff_result, diff_video]:
                Path(path).touch()

            unprocessed = unprocessed_videos(videos_dir, results_dir)

            assert unprocessed == ['diff_video.mp4']
