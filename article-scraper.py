import json
import multiprocessing
import subprocess
import random
import time

from storage import Session, Article, Source

# TODO: Later, do a crawl of known news sites (maybe in a separate script)

READABILITY_PATH = "/usr/bin/readability-scrape"

def requestWait():
    time.sleep(random.uniform(1, 5))

# Scraping is mostly I/O-bound right now, so this is fine
SCRAPE_PROCESSES = multiprocessing.cpu_count() * 2

def scrapeArticlesFromSource(source):
    # We just forked, so reseed to try to get a unique one
    random.seed()
    session = Session()
    for article in session.query(Article).filter(
            Article.source_hostname == source.hostname,
            Article.text.is_(None)).all():
        try:
            print(article.url)
            readabilityProcess = subprocess.run(
                    [READABILITY_PATH, "--json", article.url],
                    stdout=subprocess.PIPE)
            readabilityOutput = json.loads(readabilityProcess.stdout)

            newTitle = readabilityOutput["title"]
            if article.title != newTitle:
                print("Changing title to: " + newTitle)
                article.title = newTitle

            article.text = readabilityOutput["textContent"]

            session.commit()
            requestWait()
        except Exception as e:
            print(e)

with multiprocessing.Pool(SCRAPE_PROCESSES) as pool:
    pool.map(scrapeArticlesFromSource, Session().query(Source.hostname).all())
