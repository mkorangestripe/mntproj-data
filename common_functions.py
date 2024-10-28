"""Common functions for mntproj-compare"""

import logging
import os
import sys
from constants import USER_TICK_CSV_DIR, USER_PROFILE_BASE_URL

def get_csv_file(mntproj_user_id, mntproj_user_name, session, user_csv_file, refresh_csv_file):
    """Get Mountain Project csv tick list"""

    os.makedirs(USER_TICK_CSV_DIR, exist_ok=True)

    user_profile_url = f"{USER_PROFILE_BASE_URL}/{mntproj_user_id}/{mntproj_user_name}"
    user_tick_csv_export_url = user_profile_url + '/' + 'tick-export'

    if os.path.isfile(user_csv_file) is False or refresh_csv_file is True:
        logging.info("Getting %s", user_tick_csv_export_url)
        try:
            response = session.get(user_tick_csv_export_url, timeout=10)
        except session.RequestException as err:
            logging.critical(err)
            sys.exit(1)
        if response.status_code == 200:
            with open(user_csv_file, 'wb') as open_file:
                open_file.write(response.content)
        else:
            logging.critical("HTTP status code: %s", response.status_code)
            sys.exit(1)
    else:
        logging.info("Using cached %s", user_csv_file)
