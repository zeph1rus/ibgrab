"""scans a popular image site for recent images and downloads the ones it's not
seen before"""

#
# NOTE: You will need to change the regexes in this code to match the site you
# wish to scan. currently they are set to match links in the form
# /something/something/something.html
# and images in the form 
# /something/something/imagename.[jpeg/jpg/png]

import urllib2
import re
import time
import datetime
import sqlite3
from collections import defaultdict
from BeautifulSoup import BeautifulSoup
import wget

# base urls (same as first url in next dict
base_urls = []
# map base urls to an image directory (i.e. when they have a img. domain etc
src_base_urls = dict([('http://recent.image.url', 'http://site.base.url'),])

db_location = '/opt/ibgrab/db/ibgrab.db'
image_dir = '/opt/ibgrab/i'
recent_scans = defaultdict(list)

def is_image_in_db(url):
    """ Scan SQLite DB to see if image is in images table"""
    conn = sqlite3.connect(db_location)
    c = conn.cursor()
    t = (url, )
    c.execute('SELECT * FROM images WHERE imageurl=?', t)
    res = c.fetchone()
    if res is not None:
        conn.close()
        return 1

    conn.close()
    return None

def put_image_in_db(url):
    """insert new image url to the db"""
    conn = sqlite3.connect(db_location)
    c = conn.cursor()
    t = (str(url), time.strftime("%x"))
    c.execute('INSERT INTO images VALUES (?,?)', t)
    conn.commit()
    conn.close()

def download_file(url, site):
    """use wget to download new image"""
    try:
        filename = wget.download(src_base_urls[site] + url, out=image_dir + '/')
        return 1
    except Exception as e:
        print str(e)
        return None

def parse_recent(url):
    """parse the 'recent images page and return a list of image threads, pass that to the scan function"""
    print "Checking Page: " + url
    global recent_scans
    try:
        html_page = urllib2.urlopen(url)
        soup = BeautifulSoup(html_page)
        links = []
        for link in soup.findAll('a', attrs={'href' :re.compile(r'^\/.+\/[0-9]+\.html#[0-9]+')}):
            links.append(link.get('href'))

        new_urls = list(set(links) - set(recent_scans[url]))
        if not new_urls:
            print "Page not updated: "
        else:
            print "Page Updated"
            for z in new_urls:
                newbase = src_base_urls[url] + z
                try:
                    scan_url(newbase, url)
                except Exception as e:
                    print "couldn't scan urls: " + str(e)
            recent_scans[url] = list(links)
    except Exception as e:
        print "issue loading page or upstream pages: " + str(e)



def scan_url(in_url, site):
    """scan a thread for images, pass images to download function"""
    html_page = urllib2.urlopen(in_url)
    soup = BeautifulSoup(html_page)
    idups = 0
    idowns = 0
    for link in soup.findAll('a', attrs={'href' :re.compile(r'^\/[a-z]+\/[a-z]+\/[0-9]+\.[jpnge]{0,4}$')}):
        cur_image = link.get('href')
        if is_image_in_db(cur_image) is None:
            try:
                download_file(cur_image, site)
                put_image_in_db(cur_image)
                idowns += 1
            except Exception as e:
                print "error downloading file" + str(e)
        else:
            idups += 1
    print "URL: " + in_url + " Dups: " + str(idups) + " Downs: " + str(idowns)


for new_scan_url in base_urls:
    recent_scans[new_scan_url] = []

print recent_scans
while 1:
    try:
        print datetime.datetime.now().time()
        for to_scan_url in base_urls:
            parse_recent(to_scan_url)
    except Exception as e:
        print "error in iteration: " + str(e)
    print "Sleeping"
    time.sleep(273)
