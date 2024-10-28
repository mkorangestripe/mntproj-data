# Mountain Project Data Analyzer

Find other Mountain Project users with similar tick lists.

![graph](static/mpda.svg)

### Run as an API

Activate virtual env:
```shell script
pipenv shell                          # using pipenv
conda activate envs/mntproj_py3.12.7  # using Anaconda
```

Start using Flask:
```shell script
python app
```

Start using Gunicorn:  
Set the number of workers to (number of CPU cores x 2) + 1
```shell script
gunicorn -w 3 -b 0.0.0.0:8000 --timeout 1800 app:app
nohup gunicorn -w 3 -b 0.0.0.0:8000 --timeout 1800 app:app >/var/log/mntproj/gunicorn.log 2>&1 <&- &

```

View in a browser running with Flask:
[http://127.0.0.1:5000/](http://127.0.0.1:5000/)
View in a browser running with Gunicorn:
[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### Run as a script

Example usage, 2nd arg is cached data limit in minutes:
```shell script
python scrape_mntproj.py thomas-anderson
python scrape_mntproj.py thomas-anderson 60
```

Options:  
-n Try to use cached user's csv file

The UID/name must be present in [mntproj_user_ids.yaml](mntproj_user_ids.yaml), example:
```yaml
thomas-anderson: 123456789
suzy-bishop: 000000002
```

### Setup

```shell script
cd mntproj-compare
```

Use any of the following to install dependencies.

* Install dependencies from [requirements.txt](requirements.txt). Creating a virtual environment beforehand is recommended.
```shell script
pip install -r requirements.txt
```

* Create virtual environment and install dependencies from [Pipfile.lock](Pipfile.lock):
```shell script
pipenv install
```

* Anaconda can also be used to create a virtual environment.

Create cache file if doesn’t exist:
```shell script
echo '{}' > all_route_ticks.json
```

### Notes

This calls a Mountain Project API, you may receive HTTP response status code 429 (Too Many Requests) based on the rate limiting.

Compare two Mountain Project tick lists: [compare_csv.py](compare_csv.py)
