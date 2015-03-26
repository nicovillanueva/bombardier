#!/usr/bin/python3

import requests, requests.exceptions, threading, logging, argparse, time

parser = argparse.ArgumentParser(add_help=False, description="Spam GET requests, in parallel")

options = parser.add_argument_group("Options")
options.add_argument('-u', '--url', type=str, required=True, help='URL to bombard')
options.add_argument('-t', '--threads', type=int, required=True, help='Parallel threads to hit with')
options.add_argument('-r', '--requests', type=int, required=True, help='Requests to do with each thread')
options.add_argument('--timeout', type=int, required=False, default=5, help='Seconds after the requests timeout')
options.add_argument('-l', '--logfile', type=str, required=False, default='bombardier.log', help='Where to write the log')
options.add_argument('-h', '--help', action='help', help='Show this help message and exit')

args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    filename=args.logfile,
                    filemode='w',
                    )
logging.addLevelName( logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName( logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.getLogger("requests").setLevel(logging.WARNING)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

def do_requests(target, amount):
    responses = []
    for i in range(amount):
        try:
            resp = requests.get(args.url, timeout=args.timeout)
        except requests.exceptions.Timeout:
            responses.append(False)
            logging.warning("Request #%i in %s timed out" % (i, threading.currentThread().getName()))
            continue
        responses.append(resp.status_code == 200)
        logging.info("Request #%i in %s had code %i and it took %.4f" % (i, threading.currentThread().getName(), resp.status_code, resp.elapsed.total_seconds()))
    logging.info("Completed all requests for %s" % threading.currentThread().getName())
    return all(responses)

start_time = time.time()

threads = []
for i in range(args.threads):
    t = threading.Thread(target=do_requests, args=(args.url, args.requests))
    t.setName("worker-%i" % i)
    t.setDaemon(True)
    threads.append(t)
    t.start()
    logging.info("Started worker %i" % i)

main_th = threading.currentThread()
for t in threading.enumerate():
    if t is main_th:
        continue
    t.join()

end_time = time.time()

logging.info("Completed %i requests in %.2f seconds" % (args.requests * args.threads, end_time - start_time))
