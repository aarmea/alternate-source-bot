#!/usr/bin/env python3

import multiprocessing

import google_news
import reddit

def addAndStartProcess(processes, function):
    process = multiprocessing.Process(target=function)
    process.start()
    processes.append(process)

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")

    processes = list()
    addAndStartProcess(processes, google_news.scrapeProcess)
    addAndStartProcess(processes, reddit.replyProcess)

    for process in processes:
        process.join()
