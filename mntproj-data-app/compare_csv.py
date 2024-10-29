#!/usr/bin/env python
"""
Compare Mountain Project tick lists

Example:
python compare_csv.py mp-user1 mp-user2

Options:
-n  Don't get new csv files, use cached files
-p  Print common routes
-c  Check consistency between user's tick list and each route's tick list
 
MNTPROJ_USER_IDS_FILE yaml file example:
thomas-anderson: 111111111
suzy-bishop: 222222222
"""

import json
import logging
import os
import sys

import pandas as pd
import requests
import yaml

from common_functions import get_csv_file
from constants import MNTPROJ_USER_IDS_FILE, USER_TICK_CSV_DIR, ROUTE_TICKS_CACHE_FILE
from constants import LOG_DIR , LOG_FILE_COMPARE_CSV, LOG_FORMAT

LOG_LEVEL = logging.INFO
LOG_FILE = f"{LOG_DIR}/{LOG_FILE_COMPARE_CSV}"

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)

    mntproj_user_name1 = sys.argv[1]
    mntproj_user_name2 = sys.argv[2]

    if os.path.isdir(LOG_DIR) is False:
        print(LOG_DIR + " not found, logging to local logs directory")
        os.makedirs("logs", exist_ok=True)
        LOG_FILE = f"logs/{LOG_FILE_COMPARE_CSV}"

    logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL, format=LOG_FORMAT)
    logging.info("Starting Compare CSV for %s and %s", mntproj_user_name1, mntproj_user_name2)
    logging.info("Python version: %s", sys.version)

    REFRESH_CSV_FILE = True
    PRINT_COMMON = False
    CHECK_CONSISTENCY = False

    if '-n' in sys.argv:
        REFRESH_CSV_FILE = False
    if '-p' in sys.argv:
        PRINT_COMMON = True
    if '-c' in sys.argv:
        CHECK_CONSISTENCY = True

    with open(MNTPROJ_USER_IDS_FILE, encoding='utf-8') as open_mntproj_user_ids:
        mntproj_user_ids = yaml.safe_load(open_mntproj_user_ids)

    MNTPROJ_USER_ID1 = str(mntproj_user_ids[mntproj_user_name1])
    MNTPROJ_USER_ID2 = str(mntproj_user_ids[mntproj_user_name2])

    session = requests.Session()

    CSV_FILENAME1 = f"{USER_TICK_CSV_DIR}/{mntproj_user_name1}_{MNTPROJ_USER_ID1}_ticks.csv"
    get_csv_file(MNTPROJ_USER_ID1, mntproj_user_name1, session, CSV_FILENAME1, REFRESH_CSV_FILE)
    df1 = pd.read_csv(CSV_FILENAME1)

    CSV_FILENAME2 = f"{USER_TICK_CSV_DIR}/{mntproj_user_name2}_{MNTPROJ_USER_ID2}_ticks.csv"
    get_csv_file(MNTPROJ_USER_ID2, mntproj_user_name2, session, CSV_FILENAME2, REFRESH_CSV_FILE)
    df2 = pd.read_csv(CSV_FILENAME2)

    session.close()

    # Another method for removing duplicates routes from the user's tick list:
    # route_urls = df['URL'].drop_duplicates().reset_index(drop=True)

    df1_unique_url = df1['URL'].unique()
    df2_unique_url = df2['URL'].unique()

    common_route_urls = list(set(df1_unique_url) & set(df2_unique_url))

    if PRINT_COMMON is True:
        for common_route_url in common_route_urls:
            common_route_url_split = common_route_url.split('/')
            route_id = common_route_url_split[4]
            route_name = common_route_url_split[5]
            print(route_id, route_name)
        print()

    print("Common routes:", len(common_route_urls))

    if CHECK_CONSISTENCY is True:
        if PRINT_COMMON is True:
            print()
        print("Checking for inconsistencies between the second user's tick list and each route's tick list.")

        try:
            with open(ROUTE_TICKS_CACHE_FILE, encoding='utf-8') as open_cached_route_file:
                route_ticks_cached_data = json.load(open_cached_route_file)
        except FileNotFoundError:
            logging.error("%s not found, cannot complete check", ROUTE_TICKS_CACHE_FILE)
            logging.info("Compare CSV finished for %s and %s", mntproj_user_name1, mntproj_user_name2)
            sys.exit(1)

        common_route_ids = []
        for common_route_url in common_route_urls:
            common_route_url_split = common_route_url.split('/')
            route_id = common_route_url_split[4]
            common_route_ids.append(route_id)

        inconsistencies = {}
        for route_id in common_route_ids:
            if route_id in route_ticks_cached_data:
                route_name = route_ticks_cached_data[route_id]["route_name"]
                user_name_get1 = route_ticks_cached_data[route_id]["user_ticks"].get(MNTPROJ_USER_ID1)
                user_name_get2 = route_ticks_cached_data[route_id]["user_ticks"].get(MNTPROJ_USER_ID2)
                if user_name_get1 is None:
                    inconsistencies[route_id] = (route_name, mntproj_user_name1)
                elif user_name_get2 is None:
                    inconsistencies[route_id] = (route_name, mntproj_user_name2)

        if len(inconsistencies) != 0:
            print("Inconsistencies found:")
            for route_id in inconsistencies:
                route_name = inconsistencies[route_id][0]
                user_name = inconsistencies[route_id][1]
                print(route_id, route_name, "-", user_name, "missing from route tick list")
        else:
            print("No inconsistencies found.")

    logging.info("Compare CSV finished for %s and %s", mntproj_user_name1, mntproj_user_name2)
