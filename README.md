# geodiff-app
This repository contains the code associated with the paper **A Large-scale Investigation into Geodifferences in Mobile Apps** (USENIX 2022). More information about the project can be found at https://geodiff.app.
```
@inproceedings{kumar2022geodifferences,
  title={{A Large-scale Investigation into Geodifferences in Mobile Apps}},
  author={Renuka Kumar and Apurva Virkud and Ram Sundara Raman and Atul Prakash and Roya Ensafi},
  booktitle={USENIX Security Symposium},
  year={2022}
}
```
## Data

The metadata and APK error datasets can be downloaded directly [here](https://drive.google.com/drive/folders/1-UGiOUEEge-DA53k9B7KbIOvMlXKfiYZ?usp=sharing). Please reach out to us for access to the privacy policy and APK datasets.

## Code
- `apk-downloader`: download apps from Google Play
- `gpcrawler`: download app metadata from Google Play
- `privacy`: download privacy policies for Google Play apps

## Contact

The team can be contacted at geodiff.app@umich.edu.

# Setup
- This project uses Pipfiles to manage Python dependencies.
  - To install pipenv: [instructions](https://pipenv.pypa.io/en/latest/install/#installing-pipenv)
  - For more information on Pipfile and Pipfile.lock usage: [documentation](https://pipenv.pypa.io/en/latest/basics/)
- Run `pipenv install` in the same directory as the `Pipfile` whose dependencies you want to install.
    - `apk-downloader`, `gpcrawler`, and `privacy` each contain a `Pipfile` and `Pipfile.lock` for their respective dependencies.
    - There are conflicts between the dependencies for the three subdirectories, so it is recommended to use separate environments.
- `setup.cfg` contains formatting rules for development.
    - To lint code, install `pylint` and run `python -m pylint **/*.py **/**/*.py --rcfile=setup.cfg`

# Citation

Please use the following citation (provided in [BibTex](www.bibtex.org/) format) when using this dataset and/or code:

```
@inproceedings{kumar2022geodifferences,
  title={{A Large-scale Investigation into Geodifferences in Mobile Apps}},
  author={Renuka Kumar and Apurva Virkud and Ram Sundara Raman and Atul Prakash and Roya Ensafi},
  booktitle={USENIX Security Symposium},
  year={2022}
}
```

# Licensing
- This repository is released under the GNU General Public License (see [`LICENSE`](LICENSE)).
- `apk-downloader/PlaystoreDownloader` was originally forked from [**PlaystoreDownloader**](https://github.com/ClaudiuGeorgiu/PlaystoreDownloader) **v1.1.0**, which was released under the MIT License (see [`apk-downloader/PlaystoreDownloader/LICENSE`](apk-downloader/PlaystoreDownloader/LICENSE)).
- `gpcrawler/mpyscraper` was originally forked from [**google-play-scraper**](https://github.com/JoMingyu/google-play-scraper) **v0.0.6**, which was released under the MIT License (see [`gpcrawler/LICENSE`](gpcrawler/mpyscraper/LICENSE)).
