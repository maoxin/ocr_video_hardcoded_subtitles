# ocr 得到结果，保存到结果数组
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

APP_ID = ''
API_KEY = ''
SECRET_KEY = ''

CONFIG = json.load(open('config.json'))
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


def add_unique(arr, new_item):
    if new_item in arr:
        return arr
    elif not new_item:
        return arr
    elif len(arr) > 0 and difflib.SequenceMatcher(None, arr[-1], new_item).quick_ratio() > 0.8:
        return arr
    else:
        return [*arr, new_item]


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
            cv2.imwrite(os.path.join(combined_dir, str(
                idx).zfill(5)) + '.jpg', combined_img)
            combined_img = cv2.imread(img_path)
            idx += 1
        else:
            combined_img = np.concatenate(
                [combined_img, current_img], axis=0)


def main_simple():
    result = []
    images = sorted(os.listdir(sub_imgs_dir))

    try:
        for img in images:
            res = ocr_img(sub_imgs_dir + img)
            if res:
                if not result:
                    print(res[0])
                    result.append(res[0])
                    continue
                lastword = result[-1]
                # 与上一次识别结果进行比对，若相似度过高，则放弃放入数组
                if difflib.SequenceMatcher(None, lastword, res[0]).quick_ratio() < 0.8:
                    print(res[0])
                    result.append(res[0])
    except KeyboardInterrupt:
        pass
    finally:
        with open('/Users/maorui/Desktop/result.txt', 'w') as f:
            f.write('\n'.join(result))


def main_accurate(video_name):
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
    main_accurate(sys.argv[1])
