# geodiff-app
This repository contains the code associated with the paper **A Large-scale Investigation into Geodifferences in Mobile Apps** (USENIX 2022). Data and more information about the project can be found at https://geodiff.app.
```
@inproceedings{
  title={A Large-scale Investigation into Geodifferences in Mobile Apps},
  author={Renuka Kumar and Apurva Virkud and Ram Sundara Raman and Atul Prakash and Roya Ensafi},
  booktitle={USENIX Security Symposium},
  year={2022}
}
```
- `apk-downloader`: download apps from Google Play
- `gpcrawler`: download app metadata from Google Play
- `privacy`: download privacy policies for Google Play apps

# Setup
- This project uses Pipfiles to manage Python dependencies.
  - To install pipenv: [instructions](https://pipenv.pypa.io/en/latest/install/#installing-pipenv)
  - For more information on Pipfile and Pipfile.lock usage: [documentation](https://pipenv.pypa.io/en/latest/basics/)
- Run `pipenv install` in the same directory as the `Pipfile` whose dependencies you want to install.
    - `apk-downloader`, `gpcrawler`, and `privacy` each contain a `Pipfile` and `Pipfile.lock` for their respective dependencies.
    - There are conflicts between the dependencies for the three subdirectories, so it is recommended to use separate environments.
- `setup.cfg` contains formatting rules for development.
    - To lint code, install `pylint` and run `python -m pylint **/*.py **/**/*.py --rcfile=setup.cfg`

# Licensing
- This repository is released under the GNU General Public License (see [`LICENSE`](LICENSE)).
- `apk-downloader/PlaystoreDownloader` was originally forked from [**PlaystoreDownloader**](https://github.com/ClaudiuGeorgiu/PlaystoreDownloader) **v1.1.0**, which was released under the MIT License (see [`apk-downloader/PlaystoreDownloader/LICENSE`](apk-downloader/PlaystoreDownloader/LICENSE)).
- `gpcrawler/mpyscraper` was originally forked from [**google-play-scraper**](https://github.com/JoMingyu/google-play-scraper) **v0.0.6**, which was released under the MIT License (see [`gpcrawler/LICENSE`](gpcrawler/mpyscraper/LICENSE)).