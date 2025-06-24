#!/usr/bin/env python
"""
Find other Mountain Project users with the most routes in common.

Example usage, 2nd arg is cached data limit in minutes:
python scrape_mntproj.py thomas-anderson
python scrape_mntproj.py thomas-anderson 60

Options:
-n  Try to use cached user's csv file

MNTPROJ_USER_IDS_FILE yaml file example:
thomas-anderson: 123456789
suzy-bishop: 000000002
"""

import json
import os
import logging
import sys
import time
from datetime import datetime, timedelta
from json import JSONDecodeError

import pandas as pd
import requests
import yaml

from constants import USER_TICK_CSV_DIR
from constants import MNTPROJ_USER_IDS_FILE, ROUTE_TICKS_CACHE_FILE
from constants import MNT_PROJ_BASE_URL, API_V2_ROUTES
from constants import TIMESTAMP_STR_FORMAT
from constants import LOG_DIR , LOG_FILE_SCRAPE_MNTPROJ, LOG_FORMAT
from constants import CHECK_MP_LIMIT_MINS, SAME_ROUTE_MAX_LIMIT
from common_functions import get_csv_file

GET_USER_CSV = True

# LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
# LOG_LEVEL = logging.WARNING

LOG_FILE = f"{LOG_DIR}/{LOG_FILE_SCRAPE_MNTPROJ}"

class ScrapeMntProj:
    """Compare users in Mountain Project route tick lists"""

    def __init__(self, route_ticks_cache_file, session) -> None:
        self.date_time_now = datetime.now()
        self.route_ticks_cache_file = route_ticks_cache_file
        self.route_ticks_cached_data = self.load_cached_data()
        self.route_user_data = {}
        self.session = session

    def load_cached_data(self):
        """Load cached route data"""
        try:
            with open(self.route_ticks_cache_file, encoding='utf-8') as open_cached_data_file:
                return json.load(open_cached_data_file)
        except (PermissionError, JSONDecodeError) as err:
            logging.critical(err)
            sys.exit(1)
        except FileNotFoundError:
            logging.error("%s not found, creating empty object", ROUTE_TICKS_CACHE_FILE)
            return {}

    def dump_cached_data(self):
        """Dump cached route data"""
        try:
            with open(self.route_ticks_cache_file, 'w', encoding='utf-8') as open_cached_data_file:
                json.dump(self.route_ticks_cached_data, open_cached_data_file, indent=4)  # use to make human readable
                # json.dump(self.route_ticks_cached_data, open_cached_data_file)  # use to save space
        except (FileNotFoundError, PermissionError) as err:
            logging.error(err)
            logging.error("Not saving new route data")

    def cache_route_user_data(self, route_id, route_name, route_ticks_total, route_json_list):
        """Cache route user data"""

        logging.debug("Parsing new route data")
        timestamp = self.date_time_now.strftime(TIMESTAMP_STR_FORMAT)
        for entry in route_json_list:
            if entry.get("user") is None or entry["user"] is False:
                continue
            user_id2 = entry["user"]["id"]
            name2 =  entry["user"]["name"]
            if self.route_user_data.get(route_id) is None:
                self.route_user_data[route_id] = {"route_name": route_name,
                                                  "last_total_mp": route_ticks_total,
                                                  "cache_last_updated": timestamp, 
                                                  "mp_last_checked": timestamp,
                                                  "user_ticks": {}}
            self.route_user_data[route_id]["user_ticks"][user_id2] = name2

        if self.route_ticks_cached_data.get(route_id) is None:
            self.route_ticks_cached_data[route_id] = self.route_user_data[route_id]
        else:
            self.route_ticks_cached_data[route_id]["last_total_mp"] = route_ticks_total
            self.route_ticks_cached_data[route_id]["cache_last_updated"] = timestamp
            self.route_ticks_cached_data[route_id]["mp_last_checked"] = timestamp

            for user_tick in self.route_user_data[route_id]["user_ticks"]:
                user_tick_key_str = str(user_tick)
                user_tick_value = self.route_user_data[route_id]["user_ticks"][user_tick]
                user_tick_k_v = {user_tick_key_str:user_tick_value}
                self.route_ticks_cached_data[route_id]["user_ticks"].update(user_tick_k_v)

        logging.debug(self.route_user_data[route_id]["user_ticks"])

    def evaluate_cached_data(self, route_id, route_name):
        """Evaluate and update cached Mountain Project route data"""

        update_last_checked_timestamp_only = False

        check_mp_time_limit = timedelta(minutes=CHECK_MP_LIMIT_MINS)
        # route_cache_limit = timedelta(minutes=ROUTE_CACHE_LIM_MIN)

        mp_last_checked = self.date_time_now + check_mp_time_limit
        if self.route_ticks_cached_data.get(route_id) and\
        self.route_ticks_cached_data[route_id].get("mp_last_checked"):
            try:
                mp_last_checked = datetime.strptime(self.route_ticks_cached_data[route_id]["mp_last_checked"], TIMESTAMP_STR_FORMAT)
                if self.date_time_now - mp_last_checked < check_mp_time_limit:
                    logging.info("Mountain Project last checked within time limit, using cached data")
                    return
            except ValueError:
                pass

        route_ticks_data, route_ticks_total, update_last_checked_timestamp_only = self.get_route_ticks(route_id)

        if update_last_checked_timestamp_only is False:
            logging.debug("Updating route data cache")
            self.cache_route_user_data(route_id, route_name, route_ticks_total, route_ticks_data)
        else:
            logging.info("Updating last checked timestamp only, route/%s", route_id)
            self.route_ticks_cached_data[route_id]["mp_last_checked"] = self.date_time_now.strftime(TIMESTAMP_STR_FORMAT)
            # self.dump_cached_data()

    def get_route_page(self, next_page_url):
        """Get an individual page of a route's tick list"""

        max_retries = 5
        retries = 0

        try:
            response = self.session.get(next_page_url, timeout=10)
        except requests.RequestException as err:
            logging.critical(err)
            sys.exit(1)

        while response.status_code == 429 and retries < max_retries:
            wait_time = 2 ** retries
            logging.warning("Received HTTP 429, sleeping for %s seconds (retry %s)", wait_time, retries)
            time.sleep(wait_time)
            try:
                response = self.session.get(next_page_url, timeout=10)
            except requests.RequestException as err:
                logging.critical(err)
                sys.exit(1)

        if response.status_code == 200:
            logging.debug(response.headers)
            return response
        if response.status_code == 429:
            logging.critical("Exceeded max retries due to HTTP 429.")
        else:
            logging.critical("HTTP status code: %s", response.status_code)
            sys.exit(1)

        return None

    def get_route_ticks(self, route_id):
        """Get all pages of a route's tick list from Mountain Project"""

        ticks_per_page = 250
        page_count_limit = 100
        page_count = 0

        route_ticks_data = []
        route_ticks_total = 0
        update_last_checked_timestamp_only = False

        next_page_url = f"{MNT_PROJ_BASE_URL}/{API_V2_ROUTES}/{route_id}/ticks?per_page={ticks_per_page}&page=1"

        while next_page_url is not None:
            page_count += 1
            if page_count > page_count_limit:
                logging.info("Page count has exceeded limit of %s for %s", page_count_limit, next_page_url)
                break
            logging.info("Getting %s", next_page_url)
            route_ticks = self.get_route_page(next_page_url)

            try:
                route_ticks_json = route_ticks.json()
            except JSONDecodeError as err:
                logging.error(err)
                logging.warning("Trying to get %s again", next_page_url)
                try:
                    route_ticks = self.get_route_page(next_page_url)
                    route_ticks_json = route_ticks.json()
                except JSONDecodeError as err2:
                    logging.critical(err2)
                    logging.critical("Failed to get %s", next_page_url)
                    sys.exit(1)

            if route_ticks_json.get("current_page") == 1 and\
            self.route_ticks_cached_data.get(route_id) and\
            route_ticks_json["total"] == self.route_ticks_cached_data[route_id]["last_total_mp"]:
                logging.info("Route tick total same as cached, using cached data, route/%s", route_id)
                update_last_checked_timestamp_only = True
                break

            route_ticks_data = route_ticks_data + route_ticks_json['data']
            next_page_url = route_ticks_json['next_page_url']
            route_ticks_total = route_ticks_json['total']

            if route_ticks_json.get("current_page") == 1 and\
            self.route_ticks_cached_data.get(route_id):
                total_difference = route_ticks_json["total"] - self.route_ticks_cached_data[route_id]["last_total_mp"]
                logging.info("Total difference: %s, route/%s", total_difference, route_id)
                if 0 < total_difference <= ticks_per_page:
                    break

        return route_ticks_data, route_ticks_total, update_last_checked_timestamp_only


def start_scrape_mntproj(mp_uid, mp_name):
    "Start everything, get user's csv file and ticks from each route."

    start_time = datetime.now().timestamp()

    logging.info("Creating session")
    session = requests.Session()

    user_csv_file = f"{USER_TICK_CSV_DIR}/{mp_name}_{mp_uid}_ticks.csv"
    get_csv_file(mp_uid, mp_name, session, user_csv_file, GET_USER_CSV)

    logging.info("Creating dataframe from %s", user_csv_file)
    df = pd.read_csv(user_csv_file)

    logging.info("Removing duplicates routes from user's tick list")
    route_urls = df['URL'].drop_duplicates().reset_index(drop=True)

    scrape_mnt_proj = ScrapeMntProj(ROUTE_TICKS_CACHE_FILE, session)

    logging.info("Getting route ticks for all routes from either cached data or API")
    routes_total = len(route_urls)
    for route_url_i in range(routes_total):
        route_url = route_urls[route_url_i]
        running_count_url = f"{route_url_i + 1}/{routes_total} {mp_name}:{mp_uid} {route_url}"
        logging.info(running_count_url)
        try:
            _,_,_,_, route_id_from_url, route_name_from_url = route_url.split('/')
        except ValueError:
            logging.warning("Either route ID or name is missing from URL. Skipping route.")
        else:
            scrape_mnt_proj.evaluate_cached_data(route_id_from_url, route_name_from_url)

    logging.info("Closing session")
    session.close()

    logging.info("Saving new route data")
    scrape_mnt_proj.dump_cached_data()

    logging.info("Finding user counts per route")
    user_counts = {}
    for route_url in route_urls:
        try:
            route_id_from_url = route_url.split('/')[4]
        except IndexError:
            continue
        user_ids = scrape_mnt_proj.route_ticks_cached_data[route_id_from_url]['user_ticks']
        for user_id in user_ids:
            if user_counts.get(user_id):
                user_counts[user_id]["same_route_count"] = user_counts[user_id]["same_route_count"] + 1
            else:
                name = scrape_mnt_proj.route_ticks_cached_data[route_id_from_url]['user_ticks'][user_id]
                user_counts[user_id] = {}
                user_counts[user_id]["name"] = name
                user_counts[user_id]["same_route_count"] = 1

    logging.info("Creating list of tuples with users and same route counts")
    user_list = []
    for user_id in user_counts:
        name = user_counts[user_id]["name"]
        same_route_count = user_counts[user_id]["same_route_count"]
        user_list.append((name, same_route_count))

    logging.info("Sorting user list")
    sorted_user_list = sorted(user_list, key=lambda x: x[1], reverse=True)

    logging.info("Printing users, shared route counts, and percentages")
    results = []
    try:
        user_route_total = user_counts[int(mp_uid)]["same_route_count"]  # empty object was created
    except KeyError:
        user_route_total = user_counts[str(mp_uid)]["same_route_count"]  # json cache file was loaded
    for user_i in range(len(sorted_user_list)):
        name, same_route_count = sorted_user_list[user_i]
        if user_i + 1 > SAME_ROUTE_MAX_LIMIT:
            break
        same_route_percent = round(same_route_count / user_route_total * 100, 1)
        result_line = f"{name}, {same_route_count}, {same_route_percent}%"
        results.append(result_line)

    end_time = datetime.now().timestamp()
    runtime = end_time - start_time
    logging.info("Mountain Project scraper finished for %s in %.2f seconds", mp_name, runtime)

    return results


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    mntproj_name = sys.argv[1]

    if len(sys.argv) > 2:
        try:
            CHECK_MP_LIMIT_MINS = int(sys.argv[2])
        except ValueError:
            pass

        if '-n' in sys.argv:
            GET_USER_CSV = False

    if os.path.isdir(LOG_DIR) is False:
        print(LOG_DIR + " not found, logging to local logs directory")
        os.makedirs("logs", exist_ok=True)
        LOG_FILE = f"logs/{LOG_FILE_SCRAPE_MNTPROJ}"

    logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL, format=LOG_FORMAT)
    logging.info("Starting Mountain Project scraper for %s", mntproj_name)
    logging.info("Python version: %s", sys.version)

    logging.info("Opening %s",  MNTPROJ_USER_IDS_FILE)
    try:
        with open(MNTPROJ_USER_IDS_FILE, encoding='utf-8') as open_mntproj_user_ids:
            mntproj_user_ids = yaml.safe_load(open_mntproj_user_ids)
    except (FileNotFoundError, PermissionError) as err:
        logging.critical(err)
        sys.exit(1)

    mntproj_uid = mntproj_user_ids[mntproj_name]

    mp_scrape_results = start_scrape_mntproj(mntproj_uid, mntproj_name)
    for result in mp_scrape_results:
        print(result)
