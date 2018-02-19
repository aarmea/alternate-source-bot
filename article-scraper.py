import json
import multiprocessing
import os
import subprocess
import random
import time

import sqlalchemy

from storage import Session, Article, Source

# TODO: Later, do a crawl of known news sites (maybe in a separate script)

READABILITY_PATH = "/usr/bin/readability-scrape"
READABILITY_TIMEOUT = 20 # seconds

def requestWait():
    time.sleep(random.uniform(1, 5))

# Scraping is mostly I/O-bound right now, so this is fine
SCRAPE_PROCESSES = multiprocessing.cpu_count() * 2

PID = os.getpid()
def printWithPid(item):
    print(str(PID) + ": " + str(item))


def scrapeArticlesFromSource(hostname):
    session = Session()
    for article in session.query(Article).filter(
            Article.source_hostname == hostname,
            Article.text.is_(None)).all():
        printWithPid(article.url)
        try:
            readabilityString = subprocess.check_output(
                    [READABILITY_PATH, "--json", article.url],
                    timeout=READABILITY_TIMEOUT)
            readabilityOutput = json.loads(readabilityString)

            article.title = readabilityOutput["title"]
            article.text = readabilityOutput["textContent"]

            session.commit()
            requestWait()
        except subprocess.CalledProcessError as e:
            printWithPid(e)
        except Exception as e:
            printWithPid(e)

if __name__ == "__main__":
    # Spawn, don't fork, so that each child gets its own database connection
    multiprocessing.set_start_method("spawn")
    while True:
        with multiprocessing.Pool(SCRAPE_PROCESSES, maxtasksperchild=1) as pool:
            try:
                session = Session()
                # Pass just the hostname so it can be serialized for the child
                pool.map(scrapeArticlesFromSource,
                        (s.hostname for s in session.query(Source.hostname)
                            .all()), 1)
            except sqlalchemy.exc.ResourceClosedError as e:
                printWithPid(e)
            except Exception as e:
                printWithPid(e)
