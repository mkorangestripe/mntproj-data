#!/usr/bin/env python
"""
Compare users in Mountain Project route tick lists.
This script does not use caching.

Example:
python scrape_mntproj_nocache.py 123456789/thomas-anderson
"""

import sys
import pandas as pd
import requests
from constants import MNT_PROJ_BASE_URL, API_V2_ROUTES, USER_PROFILE_BASE_URL

class ScrapeMntProj:
    """Compare users in Mountain Project route tick lists"""

    def __init__(self) -> None:
        self.users_all_routes = {}

    def get_route_ticks(self, route_id):
        """Get route tick list from Mountain Project api and create list of users"""

        next_page_url = f"{MNT_PROJ_BASE_URL}/{API_V2_ROUTES}/{route_id}/ticks?per_page=250&page=1"
        page_count_limit = 100
        page_count = 0
        route_ticks_data = []

        while next_page_url is not None:
            if page_count < page_count_limit:
                page_count += 1
                route_ticks = requests.get(next_page_url)
                route_ticks_json = route_ticks.json()
                route_ticks_data = route_ticks_data + route_ticks_json['data']
                next_page_url = route_ticks_json['next_page_url']
            else:
                print("Page count has exceeded limit of", page_count_limit, "for", next_page_url)
                break

        user_ids_current_route = []
        for entry in route_ticks_data:
            # print(entry)  # debugging
            if entry.get("user") is None or entry["user"] is False:
                continue
            user_id = entry["user"]["id"]
            if user_id not in user_ids_current_route:
                user_ids_current_route.append(user_id)
                if user_id not in self.users_all_routes:
                    self.users_all_routes[user_id] = {"name": entry["user"]["name"], "same_route_count": 1}
                else:
                    same_route_count_p1 = self.users_all_routes[user_id]["same_route_count"] + 1
                    self.users_all_routes[user_id]["same_route_count"] = same_route_count_p1


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    uid_name = sys.argv[1]
    USER_PROFILE_URL = f"{USER_PROFILE_BASE_URL}/{uid_name}"

    USER_TICK_CSV_EXPORT_URL = USER_PROFILE_URL + '/' + 'tick-export'
    df = pd.read_csv(USER_TICK_CSV_EXPORT_URL)

    route_urls = df['URL'].drop_duplicates().reset_index(drop=True)

    # route_urls = ['https://www.mountainproject.com/route/105717367/incredible-hand-crack']  # testing

    scrape_mnt_proj = ScrapeMntProj()

    for route_url in route_urls:
        print(route_url)
        route_id_from_url = route_url.split('/')[4]
        scrape_mnt_proj.get_route_ticks(route_id_from_url)

    # print(scrape_mnt_proj.users_all_routes)  # debugging

    user_list = []
    for user_id2 in scrape_mnt_proj.users_all_routes:
        name = scrape_mnt_proj.users_all_routes[user_id2]['name']
        same_route_count = scrape_mnt_proj.users_all_routes[user_id2]['same_route_count']
        user_list.append((name, same_route_count))

    sorted_user_list = sorted(user_list, key=lambda x: x[1], reverse=True)

    user_id3 = int(USER_PROFILE_URL.split('/')[4])
    user_route_total = scrape_mnt_proj.users_all_routes[user_id3]['same_route_count']

    SAME_ROUTE_PERCENT_LIMIT = .198
    for user in sorted_user_list:
        name = user[0]
        same_route_count = user[1]
        if same_route_count >= (user_route_total * SAME_ROUTE_PERCENT_LIMIT):
            print(name, same_route_count)
