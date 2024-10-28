"""Constants for mntproj-compare scripts"""

MNTPROJ_USER_IDS_FILE = 'mntproj_user_ids.yaml'
ALL_ROUTE_TICKS_FILE = 'all_route_ticks.json'

MNT_PROJ_BASE_URL = "https://www.mountainproject.com"
API_V2_ROUTES = "api/v2/routes"

USER_PROFILE_BASE_URL = f"{MNT_PROJ_BASE_URL}/user"
USER_TICK_CSV_DIR = 'user_tick_csv'

TIMESTAMP_STR_FORMAT = '%Y-%m-%d %H:%M:%S'

LOG_FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
# LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# LOG_DIR = '/var/log/mntproj/'
LOG_DIR = 'logs'
LOG_FILE_SCRAPE_MNTPROJ = 'scrape_mntproj.log'
LOG_FILE_FLASK_APP = 'app.log'
LOG_FILE_COMPARE_CSV = 'compare_csv.log'

CHECK_MP_LIMIT_MINS = 1  # 60, 1440, 10080
# ROUTE_CACHE_LIM_MIN = 43800
SAME_ROUTE_MAX_LIMIT = 50
