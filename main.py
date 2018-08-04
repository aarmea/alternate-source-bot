#!/usr/bin/env python3

import multiprocessing

import article_scraper
import google_news
import reddit

from settings import Settings

def addAndStartProcess(processes, function):
    process = multiprocessing.Process(target=function)
    process.start()
    processes.append(process)

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    processes = list()

    if Settings["ACTIVE_ROLES"].getboolean("article_scraper"):
        addAndStartProcess(processes, article_scraper.scrapeProcess)

    if Settings["ACTIVE_ROLES"].getboolean("google_news"):
        addAndStartProcess(processes, google_news.scrapeProcess)

    if Settings["ACTIVE_ROLES"].getboolean("reddit"):
        addAndStartProcess(processes, reddit.replyProcess)

    for process in processes:
        process.join()
