"""
Example script that scrapes data from the IEM ASOS download service
"""
from __future__ import print_function
import time
from datetime import datetime
import math
import re

# Python 2 and 3: alternative 4
try:
    from urllib.request import urlopen
except ImportError:
    from urllib3 import urlopen

# Number of attempts to download data
MAX_ATTEMPTS = 6
# HTTPS here can be problematic for installs that don't have Lets Encrypt CA
SERVICE = "http://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?"


def download_data(uri):
    """Fetch the data from the IEM

    The IEM download service has some protections in place to keep the number
    of inbound requests in check.  This function implements an exponential
    backoff to keep individual downloads from erroring.

    Args:
      uri (string): URL to fetch

    Returns:
      string data
    """
    attempt = 0
    while attempt < MAX_ATTEMPTS:
        try:
            data = urlopen(uri, timeout=300).read().decode("utf-8")
            if data is not None and not data.startswith("ERROR"):
                return data
        except Exception as exp:
            print("download_data(%s) failed with %s" % (uri, exp))
            time.sleep(5)
        attempt += 1

    print("Exhausted attempts to download, returning empty data")
    return ""


def get_stations_from_filelist(filename):
    """Build a listing of stations.txt from a simple file listing the stations.txt.

    The file should simply have one station per line.
    """
    stations_raw = []
    for line in open(filename):
        stations_raw.append(line.strip())

    stations_time = []
    for x in stations_raw:
        x = x.replace('(', '').replace(')', '').replace(',', '').replace("'", '')
        id_time = re.split(r'\s', x)
        stations_time.append(id_time)
    return stations_time


def list_slices(data):
    """ break up the list of stations into chunks due to sys limits

    :param x: list of stations and times
    :return: list of lists as chunks of original list
    """
    slices = []
    for x in range(len(data)):
        if x % 120 == 0:
            start_index = x - 120
            end_index = x
            if start_index >= 0:
                slice = data[start_index: end_index]
                slices.append(slice)
    return slices


def main(station_list):
    """Our main function"""

    service = SERVICE + "data=all&tz=Etc/UTC&format=comma&latlon=yes&"

    for x in station_list:
        # timestamps in UTC to request data for
        startts = datetime.strptime(x[1], '%Y%m%d%H%M')
        endts = datetime.strptime(x[1], '%Y%m%d%H%M')
        service += startts.strftime("year1=%Y&month1=%m&day1=%d&")
        service += endts.strftime("year2=%Y&month2=%m&day2=%d&")
        uri = "%s&station=%s" % (service, x[0])
        print("Downloading: %s" % (x[0],))
        data = download_data(uri)
        with open('wx_file.txt', "a") as wx:
            wx.write(data)


if __name__ == "__main__":
    stations = get_stations_from_filelist("stations.txt")
    data_chunks = list_slices(stations)
    chunk_count = 0
    for x in data_chunks:
        main(x)
        chunk_count += 1
        print(f'chunk {chunk_count} complete')
        time.sleep(5)


