import json
import os
import shutil

import numpy as np
import cv2
import progressbar

CONFIG = json.load(open('config.json'))
VIDEOS_DIR = CONFIG['videosDir']
SUB_IMGS_DIR = CONFIG['subtitleImgsDir']
RESULTS_DIR = CONFIG['resultsDir']
SPLIT_DURATION = CONFIG['splitDuration']


# 读取视频截图，默认每秒抓取一次，裁剪+二值化字幕区域, 保存到指定文件夹
def get_frames(video_path, output_path, process=True):
    vc = cv2.VideoCapture(video_path)
    c = 1

    if not vc.isOpened():
        print(f'Invalid Video Path: {video_path}')
        return

    fps = round(vc.get(5))
    timeF = fps * SPLIT_DURATION
    frame_count = vc.get(cv2.CAP_PROP_FRAME_COUNT)

    print("-" * 36)
    print("Processing: ", os.path.split(video_path)[-1])
    with progressbar.ProgressBar(max_value=frame_count) as bar:
        try:
            while True:
                rval, frame = vc.read()
                if not rval:
                    break
                if(c % timeF == 0):
                    if process:
                        frame = process_image(frame)

                    sub_img = os.path.join(output_path, str(
                        c).zfill(10) + '.jpg')
                    cv2.imwrite(sub_img, frame)

                bar.update(c)
                c += 1
                cv2.waitKey(1)
        except TypeError as e:
            print(e)
        finally:
            vc.release()


# 目前功能：裁剪字幕区域+二值化
def process_image(img_arr):
    TOP = 930
    LEFT = 285
    BOTTOM = 1005
    RIGHT = 1625

    cropped = img_arr[TOP:BOTTOM, LEFT:RIGHT]
    white_region = cv2.inRange(cropped, (230, 230, 230), (255, 255, 255))
    kernel = np.ones((3, 3),np.uint8)
    white_region = cv2.morphologyEx(white_region, cv.MORPH_TOPHAT, kernel)
    return white_region


# 获取还未处理的视频列表
def unprocessed_videos(videos_dir, results_dir):
    results = os.listdir(results_dir)
    videos = os.listdir(videos_dir)

    unprocessed = [video for video in videos if os.path.splitext(video)[
        0] + '.txt' not in results]

    return unprocessed


def main():
    unprocessed = unprocessed_videos(VIDEOS_DIR, RESULTS_DIR)

    for video in unprocessed:

        video_name = os.path.splitext(video)[0]
        sub_imgs_path = (os.path.join(SUB_IMGS_DIR, video_name))
        video_path = os.path.join(VIDEOS_DIR, video)

        if os.path.exists(sub_imgs_path):
            if os.listdir(sub_imgs_path):
                continue
        else:
            os.mkdir(sub_imgs_path)

        get_frames(video_path, sub_imgs_path)


if __name__ == "__main__":
    main()
