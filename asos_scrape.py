"""
Example script that scrapes data from the IEM ASOS download service
"""
from __future__ import print_function
import time
from datetime import datetime
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
    """Build a listing of stations from a simple file listing the stations.

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
    print(stations_time)
    return stations_time


def main():
    """Our main function"""
    service = SERVICE + "data=all&tz=Etc/UTC&format=comma&latlon=yes&"

    # Two examples of how to specify a list of stations
    stations_time = get_stations_from_filelist("stations2.txt")
    for x in stations_time:
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
    main()