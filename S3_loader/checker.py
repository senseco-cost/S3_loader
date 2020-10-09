from datetime import datetime, timezone
from pathlib import Path

from S3_loader.database import Database

PRODUCT_TYPES = [
    'SR_1_SRA___', 'SR_1_SRA_A', 'SR_1_SRA_BS', 'SR_2_LAN___',
    'OL_1_EFR___', 'OL_1_ERR___', 'OL_2_LFR___', 'OL_2_LRR___',
    'SL_1_RBT___', 'SL_2_LST___',
    'SY_2_SYN___', 'SY_2_V10___', 'SY_2_VG1___', 'SY_2_VGP___'
]


def check_product_type(product_type):
    assert product_type in PRODUCT_TYPES, f'product type {product_type} is not one of acceptable {PRODUCT_TYPES}'


def parse_period(period):
    format_in = '%Y-%m-%d'
    assert isinstance(period, (list, tuple)), 'period should be a tuple of strings like ("2018-01-31", "2018-02-20")'
    period_len = len(period)
    if period_len == 2:
        date_start, date_end = period
        date_start = datetime.strptime(date_start, format_in)
        date_end = datetime.strptime(date_end, format_in)
        if date_start > date_end:
            date_start, date_end = date_end, date_start
        date_start = utcformat(date_start)
        date_end = utcformat(date_end)
    elif period_len == 1:
        date_start = utcformat(datetime.strptime(period[0], format_in))
        date_end = utcformat(datetime.now())  # 'NOW'
    else:
        raise Exception(f'period has incorrect length. Expected 1 or 2, got {period_len}, {period}')
    return date_start, date_end


def utcformat(dt, timespec='milliseconds'):
    """
    convert datetime to string in UTC format (YYYY-mm-ddTHH:MM:SS.mmmZ)
    function from https://stackoverflow.com/a/63627585 by Sam
    """
    iso_str = dt.astimezone(timezone.utc).isoformat('T', timespec)
    return iso_str.replace('+00:00', 'Z')


def parse_point(point):
    assert isinstance(point, (list, tuple)) and len(point) == 2,\
        f'point coordinates should be a tuple of length 2, like (56.46, 7.57), got {point}'
    lat, lon = point
    if not isinstance(lat, (int, float)):
        lat = float(lat)
    assert -90 < lat < 90, f'strange latitude {lat}, expected it to be in range [-90, 90]'
    if not isinstance(lon, (int, float)):
        lon = float(lon)
    assert -180 < lon < 180, f'strange longitude {lon}, expected it to be in range [-180, 180]'
    return lat, lon


def check_point_in_db(database_path, point):
    if Path(database_path).is_file():
        db = Database(database_path)
        if db.table_exists('points'):
            if db.count_points() != 0:
                point_id = db.get_point_id(point)
                assert point_id is not None, 'An attempt to use two different geo-points within the same database. ' + \
                                             'Please, use different databases for different points.'
        db.conn.close()