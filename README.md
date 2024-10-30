# Mountain Project Data Analyzer

Find other Mountain Project users with similar tick lists.

![graph](mntproj-data-app/static/mpda.svg)

### Setup

Use any of the following to install dependencies.

* Create a virtual environment and install dependencies from [requirements.txt](requirements.txt). This will use your current version of Python.
```shell script
python -m venv venv
pip install -r requirements.txt
```

* Create virtual environment and install dependencies from [Pipfile](Pipfile), or [Pipfile.lock](Pipfile.lock) if present. The specified version of Python is required.
```shell script
pipenv install
```

* With Anaconda installed, create virtual environment, install dependencies in [mntproj_py3.12.7.yaml](mntproj_py3.12.7.yaml), and install Python 3.12.7:
```shell script
conda env create -n mntproj_py3.12.7 -f mntproj_py3.12.7.yaml python=3.12.7
```

### Run as an API

Activate virtual env:
```shell script
source venv/bin/activate         # using venv
pipenv shell                     # using pipenv
conda activate mntproj_py3.12.7  # using Anaconda
```

Change to the app directory:
```shell script
cd mntproj-data-app
```

Start using Flask:
```shell script
python app.py
```

Start using Gunicorn:  
Set the number of workers to (number of CPU cores x 2) + 1

```shell script
# For shorter runs:
gunicorn -w 3 -b 0.0.0.0:8000 --timeout 1800 app:app

# Run in background:
nohup gunicorn -w 3 -b 0.0.0.0:8000 --timeout 1800 app:app >/var/log/mntproj/gunicorn.log 2>&1 <&- &
```

View in a browser running with Flask:
[http://127.0.0.1:5000/](http://127.0.0.1:5000/)  
View in a browser running with Gunicorn:
[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

The UID/name can be submitted on the page or with a query string.

### Run as a script

Create mntproj_user_ids.yaml and add UID/names, example:
```yaml
thomas-anderson: 123456789
suzy-bishop: 000000002
```

Example usage:
```shell script
python scrape_mntproj.py thomas-anderson

# Use cached data for routes checked within the last 60 min:
python scrape_mntproj.py thomas-anderson 60
```

Options:  
-n Try to use cached user's csv file

### Notes

This calls a Mountain Project API, you may receive HTTP response status code 429 (Too Many Requests) based on the rate limiting.

Compare two Mountain Project tick lists: [compare_csv.py](mntproj-data-app/compare_csv.py)
