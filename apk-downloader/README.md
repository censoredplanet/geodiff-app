# apk-downloader

## Setup

- Python dependencies can be installed via the Pipfile: `pipenv install`
  - To install pipenv: [instructions](https://pipenv.pypa.io/en/latest/install/#installing-pipenv)
  - For more information on Pipfile and Pipfile.lock usage: [documentation](https://pipenv.pypa.io/en/latest/basics/)

## PlaystoreDownloader

**PlaystoreDownloader** is a tool for downloading Android applications directly from the Google Play Store. After an
initial (one-time) configuration, applications can be downloaded by specifying their package name.
- This project was originally forked from [**PlaystoreDownloader**](https://github.com/ClaudiuGeorgiu/PlaystoreDownloader) **v1.1.0**, which was released under the [MIT License](PlaystoreDownloader/LICENSE).

### Configuration

Before interacting with the Play Store you have to provide valid credentials and an **ANDROID ID** associated to your
account. The credentials file (default `PlaystoreDownloader/credentials.json`) has the following format:
```
[
  {
    "USERNAME": "username@gmail.com",
    "PASSWORD": "password",
    "ANDROID_ID": "XXXXXXXXXXXXXXXX",
    "LANG_CODE": "en_US",
    "LANG": "us"
  }
]
```
* Enter your Google email and password in the `USERNAME` and `PASSWORD` fields. This information is needed to authenticate with Google's servers.
* Use the above credentials on an Android device (real or emulated) and download at least one application using the
official Google Play Store on the device. This step is necessary in order to associate the **ANDROID ID** of the
device to your account, so that you will be able to download applications as if you were directly using your device.
Do not remove the account from the device or its **ANDROID ID** won't be valid anymore.
* Get the **ANDROID ID** of the device and fill the `ANDROID_ID` field. You can
obtain the **ANDROID ID** by installing the [Device ID](https://play.google.com/store/apps/details?id=com.evozi.deviceid) application on your device, then copy the string corresponding to `Google Service Framework (GSF)` (use this string instead of the `Android Device ID`presented by the application).
* In case of errors related to the authentication after the above steps, consider allowing less secure apps to access
your account by visiting <https://myaccount.google.com/lesssecureapps> (visit the link while you are logged in).

_Note that you will be able to download only the applications compatible with the device corresponding to the aforementioned **ANDROID ID** and further limitations may influence the total number of applications available for download_.


## crawler.py
`crawler.py` is a script to download apps from Google Play.
```
usage: crawler.py [-h] -o OUTPUT_DIRECTORY_ROOT -i INPUT_APPS [INPUT_APPS ...] -c COUNTRY [--credentials CREDENTIALS] [-p PROXY] [-r] [-l NUM_REQUESTS NUM_SECONDS]

Download the input apps from Google Play.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIRECTORY_ROOT, --out OUTPUT_DIRECTORY_ROOT
                        directory to save downloaded .apk files
  -i INPUT_APPS [INPUT_APPS ...], --input_apps INPUT_APPS [INPUT_APPS ...]
                        app IDs OR the input filename containing one app per line
  -c COUNTRY, --country COUNTRY
                        country code
  --credentials CREDENTIALS
                        Google Play credentials file
  -p PROXY, --proxy PROXY
                        proxy (IP:PORT)
  -r, --random          enable to crawl apps in random order
  -l NUM_REQUESTS NUM_SECONDS, --limit NUM_REQUESTS NUM_SECONDS
                        rate limit: # of requests per # of seconds
```
The input file should contain one application ID per line.
- Duplicate app ids and comments are ignored.
- Comments are lines starting with the character '#' after surrounding whitespace is stripped.
```
com.facebook.katana
# This is a comment. The next line is ignored (duplicate ID)
com.facebook.katana
    # also.a.comment
com.snapchat.android
```

If the credentials argument is not provided, the default `PlaystoreDownloader/credentials.json` is used.
The credentials file should have the following format:
```
[
  {
    "USERNAME": "username@gmail.com",
    "PASSWORD": "password",
    "ANDROID_ID": "XXXXXXXXXXXXXXXX",
    "LANG_CODE": "en_US",
    "LANG": "us"
  }
]
```
See the PlaystoreDownloader [Configuration section](README.md#Configuration) for more details.

The program creates the output directory `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_DATE}` containing output files `info.log`, `finished.txt`, `failure.txt`, and `transient.txt`. `CURRENT_DATE` is formatted `YYYY-MM-DD`.
Subdirectories for the APK files are also created within the output directory on successful downloads.
- If an app download fails on the first attempt, it will automatically be retried once if the failure is not related to incorrect credentials.
- We found that the following errors correlated to specific root causes and could be verified:
  - "Item not found"
  - "Your device is not compatible with this item"
  - "The Play Store application on your device is outdated and does not support this purchase"
  - "Google Play purchases are not supported in your country. Unfortunately you will not be able to complete purchases"
  - "This item is not available on your service provider"
- Any errors not specified above are considered transient (e.g. SSL errors)
- An app is considered finished if it was successfully downloaded or if it had a verified failure. This is true even if an app previously failed with a transient error.
- Crawls can be stopped and restarted on the same day if the script is rerun with the same `OUTPUT_DIRECTORY_ROOT` and `COUNTRY`. **This will not overwrite the existing files**; apps that are finished will not be reattempted and the 4 output files will be appended to.
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_DATE}/info.log`
    - When the program starts, the following lines are appended.
    ```
    YYYY/MM/DD HH:MM:SS> {# NOT IN finished.txt} apps left to crawl of {# INPUT_APPS} in input list.
    YYYY/MM/DD HH:MM:SS> Crawl start time: {CURRENT_TIMESTAMP}
    ```
    - While running:
      - The Google Play site location is output every 50 apps. This can be used to verify the location if using a proxy.
      ```
      YYYY/MM/DD HH:MM:SS> Site Location: {COUNTRY}
      ```
      - The download responses per app are output (either success or an error message).
      ```
      YYYY/MM/DD HH:MM:SS> {APP_ID}: success
      YYYY/MM/DD HH:MM:SS> Error for app '{APP_ID}': {ERROR_MESSAGE}
      ```
    - When the program ends (or is manually stopped), the following lines are appended.
    ```
    YYYY/MM/DD HH:MM:SS> {# FINISHED IN THIS RUN} apps finished during crawl.
    YYYY/MM/DD HH:MM:SS> Crawl end time: {END_TIMESTAMP}
    YYYY/MM/DD HH:MM:SS> Time elapsed: {TIME_ELAPSED}
    ```
    - The log will also contain any program error messages (e.g. invalid input, credentials) and logging from the PlaystoreDownloader library.
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_DATE}/finished.txt`
  - Contains the finished apps, one app ID per line.
  - Any apps in this file will not be retried if the script is rerun with this output directory and country.
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_DATE}/failure.txt`
  - Contains apps with verifiable errors on download.
  ```
  {APP_ID}: {ERROR_MESSAGE}
  ```
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_DATE}/transient.txt`
  - Contains apps with transient errors on download.
  ```
  {APP_ID}: {ERROR_MESSAGE}
  ```
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_DATE}/{APP_ID}/{APP_ID}.apk`
  - Each subdirectory contains the APK file corresponding to the application ID.

### Example Usage

```console
user@shell:~$ ls /home/user/folder/
apps.txt  credentials.json
user@shell:~$
```

**Input file:** `/home/user/folder/apps.txt`
```
com.fourchars.lmp
com.opera.browser
com.tophatter
com.google.android.apps.books
com.sprint.android.musicplus2033
canada.free.unlimited.vpn
com.microsoft.teams
uk.co.radioplayer
com.vzw.ecid
```

**Input file:** `/home/user/folder/credentials.json`
```
[
  {
    "USERNAME": "username@gmail.com",
    "PASSWORD": "password",
    "ANDROID_ID": "XXXXXXXXXXXXXXXX",
    "LANG_CODE": "en_US",
    "LANG": "us"
  }
]
```

**Proxy:** `127.0.0.1:24001` -> Canada


**Run script:**
`python crawler.py -i /home/user/folder/apps.txt -o /home/user/folder/output/ -c CA --credentials /home/user/folder/credentials.json -p 127.0.0.1:24001 -r`


```console
user@shell:~$ ls /home/user/folder/
apps.txt  credentials.json  output
user@shell:~$
user@shell:~$ ls /home/user/folder/output/*/*
/home/user/folder/output/CA/2020-06-11:
com.google.android.apps.books  com.microsoft.teams  com.opera.browser  failure.txt  finished.txt  info.log  transient.txt
user@shell:~$
user@shell:~$ ls /home/user/folder/output/*/*/*
/home/user/folder/output/CA/2020-06-11/failure.txt
/home/user/folder/output/CA/2020-06-11/finished.txt
/home/user/folder/output/CA/2020-06-11/info.log
/home/user/folder/output/CA/2020-06-11/transient.txt

/home/user/folder/output/CA/2020-06-11/com.google.android.apps.books:
com.google.android.apps.books.apk

/home/user/folder/output/CA/2020-06-11/com.microsoft.teams:
com.microsoft.teams.apk

/home/user/folder/output/CA/2020-06-11/com.opera.browser:
com.opera.browser.apk
user@shell:~$
```

**Output file:** `/home/user/folder/output/CA/2020-06-11/info.log`
```
2020/06/11 11:54:59> 9 apps left to crawl of 9 in input list.
2020/06/11 11:54:59> Crawl start time: 2020-06-11_11-54-59
2020/06/11 11:54:59> Site Location: Canada
2020/06/11 11:55:05> Error for app 'com.vzw.ecid': Your device is not compatible with this item.
2020/06/11 11:55:09> com.opera.browser: success
2020/06/11 11:55:11> Error for app 'com.fourchars.lmp': The Play Store application on your device is outdated and does not support this purchase.
2020/06/11 11:55:13> Error for app 'uk.co.radioplayer': Google Play purchases are not supported in your country. Unfortunately you will not be able to complete purchases.
2020/06/15 11:55:15> Error for app 'com.tophatter': Error retrieving information from server. DF-DFERH-01
2020/06/15 11:55:15> com.tophatter: Error for app 'com.tophatter': Error retrieving information from server. DF-DFERH-01
2020/06/11 11:55:17> Error for app 'com.sprint.android.musicplus2033': This item is not available on your service provider.
2020/06/11 11:55:25> com.google.android.apps.books: success
2020/06/11 11:55:27> Error for app 'canada.free.unlimited.vpn': Item not found.
2020/06/11 11:55:36> com.microsoft.teams: success
2020/06/11 11:55:38> Error for app 'com.vzw.ecid': Your device is not compatible with this item.
2020/06/11 11:55:39> Error for app 'com.fourchars.lmp': The Play Store application on your device is outdated and does not support this purchase.
2020/06/11 11:55:41> Error for app 'uk.co.radioplayer': Google Play purchases are not supported in your country. Unfortunately you will not be able to complete purchases.
2020/06/15 11:55:43> Error for app 'com.tophatter': Error retrieving information from server. DF-DFERH-01
2020/06/15 11:55:43> com.tophatter: Error for app 'com.tophatter': Error retrieving information from server. DF-DFERH-01
2020/06/11 11:55:45> Error for app 'canada.free.unlimited.vpn': Item not found.
2020/06/11 11:55:47> Error for app 'com.sprint.android.musicplus2033': This item is not available on your service provider.
2020/06/11 11:55:47> 8 apps finished during crawl.
2020/06/11 11:55:47> Crawl end time: 2020-06-11_11-55-47
2020/06/11 11:55:47> Time elapsed: 0:00:48
```

**Output file:** `/home/user/folder/output/CA/2020-06-11/finished.txt`
```
com.opera.browser
com.google.android.apps.books
com.microsoft.teams
com.vzw.ecid
com.fourchars.lmp
uk.co.radioplayer
canada.free.unlimited.vpn
com.sprint.android.musicplus2033
```

**Output file:** `/home/user/folder/output/CA/2020-06-11/failure.txt`
```
com.vzw.ecid: Your device is not compatible with this item.
com.fourchars.lmp: The Play Store application on your device is outdated and does not support this purchase.
uk.co.radioplayer: Google Play purchases are not supported in your country. Unfortunately you will not be able to complete purchases.
canada.free.unlimited.vpn: Item not found.
com.sprint.android.musicplus2033: This item is not available on your service provider.
```

**Output file:** `/home/user/folder/output/CA/2020-06-11/transient.txt`
```
com.tophatter: Error for app 'com.tophatter': Error retrieving information from server. DF-DFERH-01
com.tophatter: Error for app 'com.tophatter': Error retrieving information from server. DF-DFERH-01
```

**Rerun script:**
`python crawler.py -i /home/user/folder/apps.txt -o /home/user/folder/output/ -c CA --credentials /home/user/folder/credentials.json -p 127.0.0.1:24001 -r`


```console
user@shell:~$ ls /home/user/folder/output/*/*/*
/home/user/folder/output/CA/2020-06-11/failure.txt
/home/user/folder/output/CA/2020-06-11/finished.txt
/home/user/folder/output/CA/2020-06-11/info.log
/home/user/folder/output/CA/2020-06-11/transient.txt

/home/user/folder/output/CA/2020-06-11/com.google.android.apps.books:
com.google.android.apps.books.apk

/home/user/folder/output/CA/2020-06-11/com.microsoft.teams:
com.microsoft.teams.apk

/home/user/folder/output/CA/2020-06-11/com.opera.browser:
com.opera.browser.apk

/home/user/folder/output/CA/2020-06-11/com.tophatter:
com.tophatter.apk
user@shell:~$
```

**Output file:** `/home/user/folder/output/CA/2020-06-11/info.log`
```
2020/06/11 11:54:59> 9 apps left to crawl of 9 in input list.
2020/06/11 11:54:59> Crawl start time: 2020-06-11_11-54-59
2020/06/11 11:54:59> Site Location: Canada
2020/06/11 11:55:05> Error for app 'com.vzw.ecid': Your device is not compatible with this item.
2020/06/11 11:55:09> com.opera.browser: success
2020/06/11 11:55:11> Error for app 'com.fourchars.lmp': The Play Store application on your device is outdated and does not support this purchase.
2020/06/11 11:55:13> Error for app 'uk.co.radioplayer': Google Play purchases are not supported in your country. Unfortunately you will not be able to complete purchases.
2020/06/15 11:55:15> Error for app 'com.tophatter': Error retrieving information from server. DF-DFERH-01
2020/06/15 11:55:15> com.tophatter: Error for app 'com.tophatter': Error retrieving information from server. DF-DFERH-01
2020/06/11 11:55:17> Error for app 'com.sprint.android.musicplus2033': This item is not available on your service provider.
2020/06/11 11:55:25> com.google.android.apps.books: success
2020/06/11 11:55:27> Error for app 'canada.free.unlimited.vpn': Item not found.
2020/06/11 11:55:36> com.microsoft.teams: success
2020/06/11 11:55:38> Error for app 'com.vzw.ecid': Your device is not compatible with this item.
2020/06/11 11:55:39> Error for app 'com.fourchars.lmp': The Play Store application on your device is outdated and does not support this purchase.
2020/06/11 11:55:41> Error for app 'uk.co.radioplayer': Google Play purchases are not supported in your country. Unfortunately you will not be able to complete purchases.
2020/06/15 11:55:43> Error for app 'com.tophatter': Error retrieving information from server. DF-DFERH-01
2020/06/15 11:55:43> com.tophatter: Error for app 'com.tophatter': Error retrieving information from server. DF-DFERH-01
2020/06/11 11:55:45> Error for app 'canada.free.unlimited.vpn': Item not found.
2020/06/11 11:55:47> Error for app 'com.sprint.android.musicplus2033': This item is not available on your service provider.
2020/06/11 11:55:47> 8 apps finished during crawl.
2020/06/11 11:55:47> Crawl end time: 2020-06-11_11-55-47
2020/06/11 11:55:47> Time elapsed: 0:00:48
2020/06/11 12:00:01> 1 apps left to crawl of 9 in input list.
2020/06/11 12:00:01> Crawl start time: 2020-06-11_12-00-01
2020/06/11 12:00:01> Site Location: Canada
2020/06/11 12:00:08> com.tophatter: success
2020/06/11 12:00:08> 1 apps finished during crawl.
2020/06/11 12:00:08> Crawl end time: 2020-06-11_12-00-08
2020/06/11 12:00:08> Time elapsed: 0:00:07
```

**Output file:** `/home/user/folder/output/CA/2020-06-11/finished.txt`
```
com.opera.browser
com.google.android.apps.books
com.microsoft.teams
com.vzw.ecid
com.fourchars.lmp
uk.co.radioplayer
canada.free.unlimited.vpn
com.sprint.android.musicplus2033
com.tophatter
```

**Output file:** `/home/user/folder/output/CA/2020-06-11/failure.txt`
No change

**Output file:** `/home/user/folder/output/CA/2020-06-11/transient.txt`
No change