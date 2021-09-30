# download privacy policies

## Setup

- Requires Google Chrome **or** Chromium.
  - To install Chromium:
    - `sudo apt install chromium-browser`
    - **OR** see Chromium [documentation](https://www.chromium.org/developers/how-tos/get-the-code) to build from source on Windows, Linux, or Mac.
  - To install Google Chrome:
    - `sudo apt install google-chrome-stable`
    - **OR** download from the Chrome [website](https://www.google.com/chrome/).
- Requires Chromedriver.
  - The major version must match your version of Google Chrome or Chromium. More information on which version to install can be found on the Chromedriver [website](https://chromedriver.chromium.org/downloads/version-selection).
  - To install Chromedriver:
    - `wget https://chromedriver.storage.googleapis.com/83.0.4103.39/chromedriver_linux64.zip; unzip chromedriver_linux64.zip` This will download the chromedriver compatible with version 83 of Chrome and Chromium on Linux - substitute with the appropriate link for your OS and version of Chromium or Chrome.
    - **OR** download from the Chromedriver [website](https://chromedriver.chromium.org/downloads).

- Python dependencies can be installed via the Pipfile: `pipenv install`
  - To install pipenv: [instructions](https://pipenv.pypa.io/en/latest/install/#installing-pipenv)
  - For more information on Pipfile and Pipfile.lock usage: [documentation](https://pipenv.pypa.io/en/latest/basics/)

## download_privacy.py

`download_privacy.py` is a script to download privacy policies for a set of apps.

```
usage: download_privacy.py [-h] -d DRIVER_PATH -i INPUT_FILE -o OUTPUT_DIRECTORY_ROOT -c COUNTRY [-s SOCKS_PROXY] [-p HTTP_PROXY]

optional arguments:
  -h, --help            show this help message and exit
  -d DRIVER_PATH, --driver_path DRIVER_PATH
                        /path/to/chromedriver/executable
  -i INPUT_FILE, --input_file INPUT_FILE
                        CSV with columns of privacy policy URLs per country
  -o OUTPUT_DIRECTORY_ROOT, --output_directory_root OUTPUT_DIRECTORY_ROOT
                        directory to save downloaded privacy policy .html files
  -c COUNTRY, --country COUNTRY
                        Two-letter country code corresponding with column in input file
  -s SOCKS_PROXY, --socks_proxy SOCKS_PROXY
                        SOCKS5 proxy with format ip:port
  -p HTTP_PROXY, --http_proxy HTTP_PROXY
                        HTTP(S) proxy with format ip:port
```

The `INPUT_FILE` should be a CSV file.
- The first row contains the column headers.
- The first column contains the app IDs.
- The remaining columns correspond to the privacy policy URLs of those apps per country - the column headers are the two-letter country codes.
  - Privacy policy URLs are found in the metadata on an app's Google Play homepage. If an app is not available or if the policy URL is missing, it can be represented with `N/A`.
```
appId,US,CA
app.id.one,https://privacy1.policy,https://privacy1.policy
app.id.two,https://privacy2.policy,N/A,
app.id.three,https://privacy3.policy.us,https://privacy3.policy.ca
```

The `DRIVER_PATH` should be the full path to the chromedriver executable (e.g. `/home/user/folder/chromedriver`). Relative paths (e.g. `folder/chromedriver`) may cause errors.

The `COUNTRY` must match one of the country headers in the input file.

The program creates the directory `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/` containing output files `log.txt` and the downloaded policies `{APP_ID}.html`.
- Crawls can be stopped and restarted if the script is rerun with the same `OUTPUT_DIRECTORY_ROOT` and `COUNTRY`. Saved policies will not be redownloaded and the log will be appended to.
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/log.txt`
  - When the program starts, the following lines are appended.
  ```
  YYYY/MM/DD HH:MM:SS> Input: full_privacy.csv
  YYYY/MM/DD HH:MM:SS> Output directory: out/US
  YYYY/MM/DD HH:MM:SS> Log file: out/US/log.txt
  YYYY/MM/DD HH:MM:SS> Starting crawl: YYYY-MM-DD_HH-MM-SS
  ```
  - The Google Play site location is output up to five times (once per thread). This can be used to verify the location if using a proxy.
  ```
  YYYY/MM/DD HH:MM:SS> Location: {COUNTRY_NAME}
  ```
  - The download responses per app policy are output (either success, an error message, or no privacy policy link in the input file).
  ```
  YYYY/MM/DD HH:MM:SS> {APP_ID}: policy downloaded
  YYYY/MM/DD HH:MM:SS> {APP_ID}: {ERROR_MESSAGE}
  YYYY/MM/DD HH:MM:SS> {APP_ID}: no privacy policy
  ```
  - When the program ends, the following line is appended.
  ```
  YYYY/MM/DD HH:MM:SS> Finished crawl: YYYY-MM-DD_HH-MM-SS
  ```
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{APP_ID}.html`
  - Downloaded policies are saved as HTML files named with the respective application IDs.

### Example Usage

```console
user@shell:~$ ls /home/user/folder/
chromedriver  privacy_policies.csv
user@shell:~$
```

**Input file:** `/home/user/folder/privacy_policies.csv`
```
appId,CA,UK,US
com.opera.browser,https://www.opera.com/privacy,https://www.opera.com/privacy,https://www.opera.com/privacy
uk.co.theofficialnationallotteryapp.android.play,N/A,https://www.national-lottery.co.uk/privacy-policy,N/A
com.google.android.apps.books,https://play.google.com/books/intl/privacy.html,https://play.google.com/books/intl/privacy.html,https://play.google.com/books/intl/privacy.html
```

**Proxy:** `127.0.0.1:24001` -> Canada

**Run script:**
```python download_privacy.py -d "/home/user/folder/chromedriver" -i `/home/user/folder/privacy_policies.csv` -o "/home/user/folder/output/" -c "CA" -s "127.0.0.1:24001"```

```console
user@shell:~$ ls /home/user/folder/
chromedriver  privacy_policies.csv  output
user@shell:~$
user@shell:~$ ls /home/user/folder/output/*
/home/user/folder/output/CA:
com.opera.browser.html  log.txt
user@shell:~$
```

**Output file:** `/home/user/folder/output/CA/log.txt`
```
2020/06/25 10:53:37> Input: /home/user/folder/privacy_policies.csv
2020/06/25 10:53:37> Output directory: /home/user/folder/output/CA
2020/06/25 10:53:37> Log file: /home/user/folder/output/CA/log.txt
2020/06/25 10:53:37> Starting crawl: 2020-06-25_10-53-37
2020/06/25 10:53:39> Location: Canada
2020/06/25 10:53:39> Location: Canada
2020/06/25 10:53:39> Location: Canada
2020/06/25 10:53:39> Location: Canada
2020/06/25 10:53:40> Location: Canada
2020/06/25 10:53:41> uk.co.theofficialnationallotteryapp.android.play: no privacy policy
2020/06/25 10:53:42> com.opera.browser: policy downloaded
2020/06/25 10:54:09> com.google.android.apps.books: Message: timeout: Timed out receiving message from renderer: -0.001   (Session info: headless chrome=83.0.4103.61)
2020/06/25 10:54:09> Finished crawl: 2020-06-25_10-54-09
```

**Rerun script:**
```python download_privacy.py -d "/home/user/folder/chromedriver" -i `/home/user/folder/privacy_policies.csv` -o "/home/user/folder/output/" -c "CA" -s "127.0.0.1:24001"```

```console
user@shell:~$ ls /home/user/folder/output/*
/home/user/folder/output/CA:
com.google.android.apps.books.html  com.opera.browser.html  log.txt
user@shell:~$
```

**Output file:** `/home/user/folder/output/CA/log.txt`
```
2020/06/25 10:53:37> Input: /home/user/folder/privacy_policies.csv
2020/06/25 10:53:37> Output directory: /home/user/folder/output/CA
2020/06/25 10:53:37> Log file: /home/user/folder/output/CA/log.txt
2020/06/25 10:53:37> Starting crawl: 2020-06-25_10-53-37
2020/06/25 10:53:39> Location: Canada
2020/06/25 10:53:39> Location: Canada
2020/06/25 10:53:39> Location: Canada
2020/06/25 10:53:39> Location: Canada
2020/06/25 10:53:40> Location: Canada
2020/06/25 10:53:41> uk.co.theofficialnationallotteryapp.android.play: no privacy policy
2020/06/25 10:53:42> com.opera.browser: policy downloaded
2020/06/25 10:54:09> com.google.android.apps.books: Message: timeout: Timed out receiving message from renderer: -0.001   (Session info: headless chrome=83.0.4103.61)
2020/06/25 10:54:09> Finished crawl: 2020-06-25_10-54-09
2020/06/25 10:55:02> Input: /home/user/folder/privacy_policies.csv
2020/06/25 10:55:02> Output directory: /home/user/folder/output/CA
2020/06/25 10:55:02> Log file: /home/user/folder/output/CA/log.txt
2020/06/25 10:55:02> Starting crawl: 2020-06-25_10-55-02
2020/06/25 10:55:04> Location: Canada
2020/06/25 10:55:04> Location: Canada
2020/06/25 10:55:04> Location: Canada
2020/06/25 10:55:04> Location: Canada
2020/06/25 10:55:04> Location: Canada
2020/06/25 10:55:05> uk.co.theofficialnationallotteryapp.android.play: no privacy policy
2020/06/25 10:55:06> com.google.android.apps.books: policy downloaded
2020/06/25 10:55:06> Finished crawl: 2020-06-25_10-55-06
```