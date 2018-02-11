import json
import os
import subprocess
import time

from storage import Session, Article, Source

# TODO: Later, do a crawl of known news sites (maybe in a separate script)

session = Session()

# TODO: Use something other than boilerpipe that does a better job
BOILERPIPE_PATH = os.path.expanduser("~/go/bin/boilerpipe")
REQUEST_WAIT_TIME = 5 # seconds

for source in session.query(Source.hostname).all():
    # TODO: Spawn a thread/process per news site
    print(source.hostname)
    for article in session.query(Article).filter(
            Article.source_hostname == source.hostname,
            Article.text.is_(None)).all():
        print(article.url)
        boilerpipeProcess = subprocess.run(
                [BOILERPIPE_PATH, "extract", article.url],
                stdout=subprocess.PIPE)
        boilerpipeOutput = json.loads(boilerpipeProcess.stdout)
        print(json.dumps(boilerpipeOutput, indent=4)) # XXX

        time.sleep(REQUEST_WAIT_TIME)
