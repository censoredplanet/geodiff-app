# download metadata

## Setup

- Python dependencies can be installed via the Pipfile: `pipenv install`
  - To install pipenv: [instructions](https://pipenv.pypa.io/en/latest/install/#installing-pipenv)
  - For more information on Pipfile and Pipfile.lock usage: [documentation](https://pipenv.pypa.io/en/latest/basics/)

## mpyscraper

`mpyscraper` provides functions to scrape data from Google Play.
- This project was originally forked from [**google-play-scraper**](https://github.com/JoMingyu/google-play-scraper) **v0.0.6**, which was released under the [MIT License](mpyscraper/LICENSE).
- [**google-play-scraper**](https://github.com/facundoolano/google-play-scraper) for Node.js was also used as reference.

### API
- ```python
  google_location(proxy: Optional[str] = None) -> str
  ```
  Scrape the Google Play store location from the home page.

- ```python
  details(app_id: str, proxy: Optional[str] = None, lang: Optional[str] = None,
          country: Optional[str] = None) -> Dict[str, Any]
  ```
  Scrape the details for an app.

- ```python
  similar(app_id: str, proxy: Optional[str] = None, lang: Optional[str] = None,
          country: Optional[str] = None) -> List[Any]
  ```
  Scrape the similar app list for an app.

- ```python
  developer(dev_id: str, proxy: Optional[str] = None, lang: Optional[str] = None,
            country: Optional[str] = None) -> List[Any]
  ```
  Scrape the details for a developer.

- ```python
    search(term: str, proxy: Optional[str] = None, lang: Optional[str] = None,
           country: Optional[str] = None) -> List[Any]
  ```
  Scrape the results of a search on Google Play.

- ```python
    collection(collection_name: str, proxy: Optional[str] = None, lang: Optional[str] = None,
               country: Optional[str] = None) -> List[Any]
  ```
  Scrape the apps in a Google Play collection.

- ```python
  category(category_name: str, proxy: Optional[str] = None, lang: Optional[str] = None,
           country: Optional[str] = None) -> List[Any]
  ```
  Scrape the recommended apps in a Google Play category.

- ```python
  filtered_collection(category_name: str, collection_name: str = "top",
                      proxy: Optional[str] = None, lang: Optional[str] = None,
                      country: Optional[str] = None) -> List[Any]
  ```
  Scrape the apps in a Google Play top collection.

- ```python
  permissions(app_id: str, proxy: Optional[str] = None, lang: Optional[str] = None,
              country: Optional[str] = None) -> Dict[str, List[Any]]
  ```
  Scrape the permissions for an app.

### Exceptions
- `GooglePlayScraperException`: base exception class
- `InvalidURLError`: thrown when attempting to build an invalid Google Play URL
- `NotFoundError`: thrown when an HTTP(S) request to Google Play returns a 404 error
- `ExtraHTTPError`: thrown when an HTTP(S) request to Google Play returns a non-404 error

### Constants
- `COLLECTIONS`: dictionary of Google Play collections
- `CATEGORIES`: dictionary of Google Play categories

## generate_app_list.py
`generate_app_list.py` is a script to generate a list of popular apps.

```bash
usage: generate_app_list.py [-h] -o OUTPUT_DIRECTORY_ROOT [-g COUNTRY]
                            [-s SEARCH] [-c CATEGORY] [-t THREAD_COUNT]
                            [-p PROXY]

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIRECTORY_ROOT, --output_directory_root OUTPUT_DIRECTORY_ROOT
                        root directory for output files
  -g COUNTRY, --country COUNTRY
                        country code for crawl
  -s SEARCH, --search SEARCH
                        file containing list of search terms
  -c CATEGORY, --category CATEGORY
                        file containing list of categories
  -t THREAD_COUNT, --thread_count THREAD_COUNT
                        number of worker threads
  -p PROXY, --proxy PROXY
                        proxy (IP:PORT)
```

The search and category input files are optional. If either are provided,
the files should contain one item (a search term or category) per line.
- The default search terms are "vpn", "ad blocker", "privacy", "security", and "crypto wallet".
- The default categories are all of the Google Play defined categories. The full list can be found in `mpyscraper/constants/constant.py`. Categories that are not in this file are considered invalid and will be ignored.
- Comments (lines beginning with a `#`) are skipped.

The app list is the union of the search results and the top apps per category.

The program creates the output directory `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}` containing output files `log.txt`, `category.txt`, `search.txt` `app_list.txt`, `summary.txt`,
and `results.txt`.
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/log.txt`: contains logging information.
  - The first two lines are the start time and output directory.
  ```
  Starting crawl: {CURRENT_TIMESTAMP}
  Saving output files to {OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}
  ```
  - Search and category queries are logged with the following format(either success or error).
  ```
  SEARCH| {TERM}: success
  SEARCH| {TERM}: error
  CATEGORY| {CATEGORY}: success
  CATEGORY| {CATEGORY}: error
  ```
  - The app list is logged after the search and category queries finish.
  ```
  App list done: {TIMESTAMP}
  App list contains {COUNT} apps saved to {OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/app_list.txt
  ```
  - Queries for an app's category are logged (either the category on success or error).
  ```
  DETAILS| {APP_ID}: {CATEGORY}
  DETAILS| {APP_ID}: error
  ```
  - The last two lines are the end time and output files.
  ```
  Finished crawl: {END_TIMESTAMP}
  Full organized results saved to {OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/results.txt, summary saved to {OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/summary.txt
  ```
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/category.txt`: contains the results of the (top apps per) category queries.
  - Each category has a commented header line (`# {CATEGORY}`) followed by the app IDs that were returned for the query.
  ```
  # EDUCATION
  education.one
  education.two
  education.three
  # GAME
  game.one
  game.two
  game.three
  ```
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/search.txt`: contains the results of the search queries.
  - Each search term has a commented header line (`# {TERM}`) followed by the app IDs that were returned for the query.
  ```
  # vpn
  vpn.one
  vpn.two
  # ad blocker
  ad.blocker.one
  ad.blocker.two
  ```
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/app_list.txt`: contains the app list, one app ID per line.
  - These apps are the union of the apps from `category.txt` and `search.txt`.
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/summary.txt`: contains the total number of apps per category.
  - Each line is formatted `# {CATEGORY} {COUNT}`.
  ```
  # FINANCE 234
  # FOOD_AND_DRINK 189
  ```
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/results.txt`: contains the app list organized by categories.
  - Each category has a commented header line (`# {CATEGORY} {COUNT}`) followed by all app IDs from the app list that belong to the category.
  ```
  # FINANCE 234
  finance.one
  ...
  finance.twohundred.thirtyfour
  # FOOD_AND_DRINK 189
  food.one
  ...
  food.onehundred.ninetyeight
  ```

### Example Usage

```console
user@shell:~$ ls /home/user/folder/
input_categories.txt  input_search.txt
user@shell:~$
```

**Input file:** `/home/user/folder/input_categories.txt`
```
ART_AND_DESIGN
MEDICAL
```

**Input file:** `/home/user/folder/input_search.txt`
```
vpn
crypto wallet
```

**Proxy:** `127.0.0.1:24001` -> Canada


**Run script:**
`python generate_app_list.py -o /home/user/folder/output/ -g CA -s /home/user/folder/input_search.txt -c /home/user/folder/input_categories.txt -p 127.0.0.1:24001`


```console
user@shell:~$ ls /home/user/folder/
input_categories.txt  input_search.txt  output
user@shell:~$
user@shell:~$ ls /home/user/folder/output/*/*
/home/user/folder/output/CA/2020-05-17_21-14-38:
app_list.txt  category.txt  log.txt  results.txt  search.txt  summary.txt
user@shell:~$
```

**Output file:** `/home/user/folder/output/CA/2020-05-17_21-14-38/log.txt`
```
Starting crawl: 2020-05-17_21-14-38
Saving output files to /home/user/folder/output/CA/2020-05-17_21-14-38
SEARCH| vpn: success
SEARCH| crypto wallet: success
CATEGORY| ART_AND_DESIGN: success
CATEGORY| MEDICAL: success
App list done: 2020-05-17_21-14-44
App list contains 803 apps saved to /home/user/folder/output/CA/2020-05-17_21-14-38/app_list.txt
DETAILS| jp.ne.ibis.ibispaintx.app: ART_AND_DESIGN
DETAILS| com.expressvpn.vpn: TOOLS
...
Finished crawl: 2020-05-17_21-20-15
Full organized results saved to /home/user/folder/output/CA/2020-05-17_21-14-38/results.txt, summary saved to /home/user/folder/output/CA/2020-05-17_21-14-38/summary.txt
```

**Output file:** `/home/user/folder/output/CA/2020-05-17_21-14-38/category.txt`
```
# ART_AND_DESIGN
jp.ne.ibis.ibispaintx.app
com.canva.editor
com.redberry.glitterdressa2
com.adobe.spark.post
com.colorbynumber.unicorn.pixel.art.pokepix.draw.paintbynumber
...
com.kvadgroup.posters
com.baselayoutsforcoc
com.sweefitstudios.drawtattoo
com.codelunatics.posemakerpro
com.redberry.glitterunicornkids
# MEDICAL
com.babylon.telushealth
com.maplenativeuser
com.appsci.sleep
com.lifescan.reveal
md.akira
...
com.zdn35.music.songs.audio.spamusicandrelaxmusicsparelaxation
com.bxh_mvp
com.atomengineapps.teachmeanatomy
com.zygne.earextender
com.lyric.language_medical_terminology
```

**Output file:** `/home/user/folder/output/CA/2020-05-17_21-14-38/search.txt`
```
# vpn
com.fast.free.unblock.thunder.vpn
free.vpn.unblock.proxy.turbovpn
com.security.xvpn.z35kb
hotspotshield.android.vpn
co.infinitysoft.vpn360
...
vpn.japan
com.candylink.openvpn
com.superapp.fastvpn
com.bluewhale.funnyshark.vpn
xyz.easypro.httpcustom
# crypto wallet
exodusmovement.exodus
piuk.blockchain.android
com.enjin.mobile.wallet
com.wallet.crypto.trustapp
com.coinomi.wallet
...
cash.simply.wallet
com.mal.saul.coinmarketcap
io.github.jangerhard.BitcoinWalletTracker
com.blockchain.explorer
com.m2049r.xmrwallet
```

**Output file:** `/home/user/folder/output/CA/2020-05-17_21-14-38/app_list.txt`
```
jp.ne.ibis.ibispaintx.app
com.canva.editor
com.redberry.glitterdressa2
com.adobe.spark.post
com.colorbynumber.unicorn.pixel.art.pokepix.draw.paintbynumber
...
cash.simply.wallet
com.mal.saul.coinmarketcap
io.github.jangerhard.BitcoinWalletTracker
com.blockchain.explorer
com.m2049r.xmrwallet
```

**Output file:** `/home/user/folder/output/CA/2020-05-17_21-14-38/summary.txt`
```
# ART_AND_DESIGN 197
# COMMUNICATION 83
# FINANCE 143
# MEDICAL 195
# TOOLS 185
```

**Output file:** `/home/user/folder/output/CA/2020-05-17_21-14-38/results.txt`
```
# ART_AND_DESIGN 197
jp.ne.ibis.ibispaintx.app
...
# COMMUNICATION 83
com.superapp.fastvpn
...
# FINANCE 143
exodusmovement.exodus
...
# MEDICAL 195
com.babylon.telushealth
...
# TOOLS 185
com.fast.free.unblock.thunder.vpn
...
```

## metadata_crawl.py
`metadata_crawl.py` is a script to crawl Google Play for app metadata (category, number of installs, version, etc).

```bash
usage: metadata_crawl.py [-h] --input_apps INPUT_APPS --country COUNTRY
                        --output_directory_root OUTPUT_DIRECTORY_ROOT
                        [--num_workers NUM_WORKERS] [--proxy PROXY]
                        [--random] [--full_metadata]

optional arguments:
  -h, --help            show this help message and exit
  --input_apps INPUT_APPS, -i INPUT_APPS
                        input file containing one app id per line
  --country COUNTRY, -c COUNTRY
                        two-letter country code
  --output_directory_root OUTPUT_DIRECTORY_ROOT, -o OUTPUT_DIRECTORY_ROOT
                        root folder for output files
  --num_workers NUM_WORKERS, -n NUM_WORKERS
                        number of worker threads
  --proxy PROXY, -p PROXY
                        HTTP(S) proxy (IP:PORT)
  --random, -r          randomize crawl order of apps
  --full_metadata, -f   save the full metadata
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

The program creates the output directory `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}` containing output files `log.txt` and `metadata.csv`:
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/log.txt`
    - The first four lines are the input file, metadata file, log file, and start time.
    ```
    Input: {INPUT_APPS}
    Output: {OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/metadata.csv
    Log file: {OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/log.txt
    Starting crawl: {CURRENT_TIMESTAMP}
    ```
    - The last line is the end time.
    ```
    Finished crawl: {END_TIMESTAMP}
    ```
    - Check the log for any program error messages (e.g. invalid input).
- `{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/metadata.csv`
    - The program exits before creating `metadata.csv` if input is invalid.

Metadata requests are logged to `log.txt`:
- error message on failure (e.g. `not.an.app: Page not found(404).`)
- the Google Play site location on success (e.g. `com.facebook.katana: siteLocation United States, written`)
    - The site location can confirm if a proxy is working correctly.

By default, `metadata.csv` contains the following column headers:
    `appId,version,updated,released,downloadLink,downloadLinkEnabled`

If the `--full-metadata`/`-f` flag is enabled,
`metadata.csv` contains the following column headers:
```
appId,url,siteLocation,siteLanguage,title,description,summary,installs,numInstalls,minInstalls,score,ratings,reviews,histogram,price,free,currency,offersIAP,size,androidVersion,androidVersionText,developer,developerId,developerEmail,developerWebsite,developerAddress,privacyPolicy,developerInternalID,genre,genreId,contentRating,contentRatingDescription,adSupported,containsAds,released,updated,version,recentChanges,comments,similarURL,downloadLink,downloadLinkEnabled
```

### Example Usage

```console
user@shell:~$ ls /home/user/folder/
apps.txt
user@shell:~$
```

**Input file:** `/home/user/folder/apps.txt`
```
# org.havenapp.main
com.opera.browser
# com.genius.android
com.google.android.apps.books
canada.free.unlimited.vpn
com.microsoft.teams
# com.c25k
# uk.co.radioplayer
# com.google.android.apps.googlevoice
# com.sony.songpal.mdr
```

**Proxy:** `127.0.0.1:24001` -> Canada

**Run script:**
`python metadata_crawl.py -i /home/user/folder/apps.txt -c CA -o /home/user/folder/output/ -p 127.0.0.1:24001 -r`

```console
user@shell:~$ ls /home/user/folder/
apps.txt  output
user@shell:~$
user@shell:~$ ls /home/user/folder/output/*/*
/home/user/folder/output/CA/2020-06-11_11-23-50:
log.txt  metadata.csv
user@shell:~$
```

**Output file:** `/home/user/folder/output/CA/2020-06-11_11-23-50/log.txt`
```
Input: /home/user/folder/apps.txt
Output: /home/user/folder/output/CA/2020-06-11_11-23-50/metadata.csv
Log file: /home/user/folder/output/2020-06-11_11-23-50/log.txt
Starting crawl: 2020-06-11_11-23-50
com.microsoft.teams: siteLocation Canada, written
canada.free.unlimited.vpn: Page not found(404).
com.opera.browser: siteLocation Canada, written
com.google.android.apps.books: siteLocation Canada, written
Finished crawl: 2020-06-11_11-24-11
```

**Output file:** `/home/user/folder/output/CA/2020-06-11_11-23-50/metadata.csv`
```
appId,version,updated,released,downloadLink,downloadLinkEnabled
com.microsoft.teams,1416/1.0.0.2020050805,1591686178,"Nov 2, 2016",True,True
com.opera.browser,Varies with device,1590567964,"Nov 8, 2010",True,True
com.google.android.apps.books,Varies with device,1591167865,"Dec 6, 2010",True,True
```
