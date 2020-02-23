import difflib
import json
import os
import sys
from functools import reduce
from glob import glob

import cv2
import numpy as np
import progressbar
from aip import AipOcr

CONFIG = json.load(open('config.json'))
APP_ID = CONFIG['AppId']
API_KEY = CONFIG['APIKey']
SECRET_KEY = CONFIG['SecretKey']

VIDEOS_DIR = CONFIG['videosDir']
SUB_IMGS_DIR = CONFIG['subtitleImgsDir']
COMBINED_IMGS_DIR = CONFIG['combinedImgsDir']
RESULTS_DIR = CONFIG['resultsDir']
SPLIT_DURATION = CONFIG['splitDuration']

client = AipOcr(APP_ID, API_KEY, SECRET_KEY)


def get_file_content(file_path):
    with open(file_path, 'rb') as fp:
        return fp.read()


class APIError(Exception):
    pass


# image_path -> [line_text]
def ocr_img(file_path, method=None):
    data = get_file_content(file_path)
    try:
        if method == 'acc':
            res = client.basicAccurate(data)
        else:
            res = client.basicGeneral(data)

        if res.get('error_code'):
            raise APIError(f"❎Error[{res['error_code']}]: {res['error_msg']}")

        text_arr = [line['words'] for line in res['words_result']]
        return text_arr
    except KeyboardInterrupt:
        print("\n⏹ Stopped!")
        raise
    except Exception as e:
        print(e)
        return []


# judge the same or similar lines of text
# [line_text], text => [line_text]
def add_unique(arr, new_item):
    if new_item in arr:
        return arr
    elif not new_item:
        return arr
    elif len(arr) > 0 and difflib.SequenceMatcher(None, arr[-1], new_item).quick_ratio() > 0.8:
        return arr
    else:
        return [*arr, new_item]


# Combine subtitle image files captured by frames to a large file up to the maximum size which the BaiduAPI can receive
def combine_images(images_dir, combined_dir):
    MAX_RECEIVE_HEIGHT = 4096
    images = sorted(glob(os.path.join(images_dir, '*.jpg')))
    current_img = cv2.imread(images[0])

    idx = 1
    combined_img = current_img

    print(f'⏳ Combine images from "{images_dir}" => "{combined_dir}" ...\n')

    for img_path in progressbar.progressbar(images[1:]):
        combined_img_height = combined_img.shape[0]

        current_img = cv2.imread(img_path)
        current_img_height = current_img.shape[0]

        if combined_img_height + current_img_height > MAX_RECEIVE_HEIGHT:
            combined_img = cv2.resize(combined_img, tuple(s // 4 for s in combined_img.shape[:-1])[::-1])
            cv2.imwrite(os.path.join(combined_dir, str(
                idx).zfill(5)) + '.jpg', combined_img)
            combined_img = cv2.imread(img_path)
            idx += 1
        else:
            combined_img = np.concatenate(
                [combined_img, current_img], axis=0)


def main():

    video_name = sys.argv[1]
    result = []
    sub_imgs_path = os.path.join(SUB_IMGS_DIR, video_name)
    combined_imgs_path = os.path.join(COMBINED_IMGS_DIR, video_name)

    if not os.path.exists(combined_imgs_path):
        os.mkdir(combined_imgs_path)
        combine_images(sub_imgs_path, combined_imgs_path)

    images = sorted(glob(os.path.join(combined_imgs_path, '*.jpg')))

    print(f'⏳ Recognizing subtitles of "{video_name}" ...\n')

    try:
        for img_path in progressbar.progressbar(images):
            res = ocr_img(img_path, method='acc')
            result += res
    except KeyboardInterrupt:
        pass
    finally:
        unique_result = reduce(add_unique, result, [])

        result_path = os.path.join(RESULTS_DIR, video_name)

        print(f'✅ OCR Over. Save results to "{result_path}.txt"')
        with open(f'{result_path}.txt', 'w') as f:
            f.write('\n'.join(unique_result))


if __name__ == "__main__":
    main()
