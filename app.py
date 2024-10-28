#!/usr/bin/env python

"""Entry point for Mountain Project data analyzer"""

import logging
import sys
from flask import Flask, render_template, request, redirect, url_for
from constants import LOG_DIR , LOG_FILE_FLASK_APP, LOG_FORMAT
from scrape_mntproj import start_scrape_mntproj

# LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
# LOG_LEVEL = logging.WARNING

LOG_FILE = f"{LOG_DIR}/{LOG_FILE_FLASK_APP}"

logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL, format=LOG_FORMAT)
logging.info("Starting Mountain Project Data Analyzer")
logging.info("Python version: %s", sys.version)

def validate_input(mp_uid_name):
    "Validate input from user"
    if len(mp_uid_name) > 100:
        return "UID/name too long", 400
    try:
        mntproj_uid, mntproj_name = mp_uid_name.strip('/').split('/')
    except ValueError as err:
        logging.error(err)
        return "UID/name not valid", 400
    return (mntproj_uid, mntproj_name), 200

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    "Input form for Mnt Proj scraper"
    if request.method == 'POST':
        mp_uid_name = request.form.get('input_field')
        return redirect(url_for('results', uid_name=mp_uid_name))
    return render_template('index.html')

@app.route('/results')
def results():
    "Mnt Proj scrape results"
    mp_uid_name = request.args.get('uid_name', '')
    parsed_mp_uid_name = validate_input(mp_uid_name)
    if parsed_mp_uid_name[1] == 400:
        return parsed_mp_uid_name
    mntproj_uid, mntproj_name = parsed_mp_uid_name[0]
    scrape_results = start_scrape_mntproj(mntproj_uid, mntproj_name)
    return render_template('results.html', results=scrape_results)

if __name__ == '__main__':
    app.run(debug=True)
