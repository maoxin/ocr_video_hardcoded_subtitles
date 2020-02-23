# Convert hardcoded subtitles from videos to text files

Warning: this project is still under development. It is only suitable for 1080p videos, and the coodinates of subtitles on video frames is hardcoded as well as the subtitles themselves.

## Usage

1. Install the dependencies using pip:
  
    ```
    pip install progressbar2 baidu-aip opencv-python-headless numpy
    ```
    
2. Edit `config.json` file.
   * Note to change the value of `videosDir` to the path of videos folder on your computer.
   * `splitDuration` is the time intervals between every processed frame from all frames in a video. The default value is `1` second.
   * Please create an app using OCR APIs from Baidu AI Platform, and fill in the AppID, API Key and Secret Key in `config.json`.

3. Run `python get_frames.py` to get subtitle images from `videosDir`   and save them to a folder(`subtitleImgsDir` in `config.json`)

4. Run `python ocr_subtitles.py <video_name>` to convert subtitle images to a text file in `resultsDir`.

