import json
import multiprocessing
import subprocess
import random
import time
from urllib.parse import urljoin

from lxml import html
import requests
import sqlalchemy

from storage import Session, Article, Source
from util import printWithPid

READABILITY_PATH = "/usr/bin/readability-scrape"
REQUEST_TIMEOUT = 30 # seconds
RENDER_TIMEOUT = 120 # seconds

def _requestWait():
    time.sleep(random.uniform(1, 5))

# Scraping is mostly I/O-bound right now, so this is fine
SCRAPE_PROCESSES = max(4, multiprocessing.cpu_count() * 2)

def _scrapeArticlesFromSource(hostname):
    printWithPid("Scraping " + hostname)
    session = Session()

    # Find new articles from the homepage of the source
    # TODO: Recurse?
    try:
        # requests will follow redirects, including upgrades to https
        sourceRequest = requests.get("http://" + hostname,
                timeout=REQUEST_TIMEOUT)
        sourceTree = html.fromstring(sourceRequest.content)

        for link in sourceTree.findall(".//a"):
            if "href" not in link.attrib:
                continue
            url = urljoin(sourceRequest.url, link.attrib["href"])
            article = session.query(Article).get(url)
            if article is None and hostname in url:
                printWithPid("Found " + url)
                session.add(Article(url=url, source_hostname=hostname))
    except Exception as e:
        printWithPid(e)

    session.commit()
    _requestWait()

    # Actually retrieve the articles
    for article in session.query(Article).filter(
            Article.source_hostname == hostname,
            Article.text.is_(None),
            Article.retrieved.is_(None)):
        printWithPid("Retrieving " + article.url)
        try:
            readabilityString = subprocess.check_output(
                    [READABILITY_PATH, "--json", article.url],
                    timeout=RENDER_TIMEOUT).decode("utf8")
            readabilityOutput = json.loads(readabilityString)

            if readabilityOutput is not None:
                article.title = readabilityOutput["title"]
                article.text = readabilityOutput["textContent"]
        except subprocess.CalledProcessError as e:
            printWithPid(e)
        except Exception as e:
            printWithPid(e)

        article.retrieved = sqlalchemy.sql.functions.current_timestamp()

        session.commit()
        _requestWait()

def scrapeProcess():
    while True:
        printWithPid("-- Starting article scraper --");
        # Each process should be responsible for exactly one source to load
        # balance scraping a little better
        with multiprocessing.Pool(SCRAPE_PROCESSES, maxtasksperchild=1) as pool:
            try:
                session = Session()
                # Pass just the hostname so it can be serialized for the child
                pool.map(_scrapeArticlesFromSource,
                        (s.hostname for s in session.query(Source.hostname)), 1)
            except sqlalchemy.exc.ResourceClosedError as e:
                printWithPid(e)
            except Exception as e:
                printWithPid(e)

if __name__ == "__main__":
    # Spawn, don't fork, so that each child gets its own database connection
    multiprocessing.set_start_method("spawn")
    scrapeProcess()
