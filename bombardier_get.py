#!/usr/bin/python3

import requests, requests.exceptions, threading, logging, argparse, time

parser = argparse.ArgumentParser(add_help=False, description="Spam GET requests, in parallel")

options = parser.add_argument_group("Options")
options.add_argument('-u', '--url', type=str, required=True, help='URL to bombard')
options.add_argument('-t', '--threads', type=int, required=True, help='Parallel threads to hit with')
options.add_argument('-r', '--requests', type=int, required=True, help='Requests to do with each thread')
options.add_argument('--timeout', type=int, required=False, default=5, help='Seconds after the requests timeout (default: 5)')
options.add_argument('-l', '--logfile', type=str, required=False, default='bombardier.log', help='Where to write the log')
options.add_argument('-h', '--help', action='help', help='Show this help message and exit')

args = parser.parse_args()

FORMAT = '%(asctime)-15s %(threadName)-10s %(levelname)s %(message)s'

logging.basicConfig(level=logging.DEBUG,
                    format=FORMAT,
                    filename=args.logfile,
                    filemode='w',
                    )
#DONE_LEVEL_NUM = 25
#logging.addLevelName( DONE_LEVEL_NUM,  "\033[1;34m%s\033[1;0m"   % "DONE" )
logging.addLevelName( logging.INFO,    "\033[1;32m%s\033[1;0m"   % logging.getLevelName(logging.INFO) )     # Green
logging.addLevelName( logging.WARNING, "\033[1;33m%s\033[1;0m"   % logging.getLevelName(logging.WARNING) )  # Yellow
logging.addLevelName( logging.ERROR,   "\033[1;31;1m%s\033[1;0m" % logging.getLevelName(logging.ERROR) )    # Bold red
logging.getLogger("requests").setLevel(logging.WARNING)  # Squelch any requests' logging lower than WARNING

"""
def done(self, message, *args, **kws):
    if logging.Logger.isEnabledFor(DONE_LEVEL_NUM):
        logging.Logger._log(DONE_LEVEL_NUM, message, args, **kws)
logging.Logger.done = done
"""

console = logging.StreamHandler()  # Log to the console
console.setLevel(logging.INFO)
formatter = logging.Formatter('[%(levelname)-8s] %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

def do_requests(target, amount, ret_values, index):
    responses = []
    timings = []
    for i in range(amount):
        try:
            resp = requests.get(args.url, timeout=args.timeout)
        except requests.exceptions.Timeout:
            responses.append(408)
            logging.error("Request #%i in %s timed out" % (i, threading.currentThread().getName()))
            continue
        except requests.exceptions.ConnectionError:
            responses.append(418)
            logging.error("Request #%i in %s had a connection error" % (i, threading.currentThread().getName()))
            continue

        if resp.status_code == 200:
            logging.info("Request #%i in %s had code 200 and it took %.4f" % (i, threading.currentThread().getName(),
                                                                              resp.elapsed.total_seconds()))
        else:
            logging.warning("Request #%i in %s had code %i and it took %.4f" % (i, threading.currentThread().getName(),
                                                                                resp.status_code,
                                                                                resp.elapsed.total_seconds()))
        timings.append(resp.elapsed.total_seconds())
        responses.append(resp.status_code)
    logging.info("Completed all requests for %s" % threading.currentThread().getName())
    # Stupid way to return values from a threaded method, as Py can't implement a 'return'
    ret_values[index] = {"responses": responses, "average": (sum(timings) / len(timings))}

start_time = time.time()

threads = []
return_values = {}
for i in range(args.threads):
    t = threading.Thread(target=do_requests, args=(args.url, args.requests, return_values, i))
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

# do statisticky stuff:
print(return_values)
total = 0
for i in range(len(return_values)):
    a = return_values.get(i)
    total += a.get("average")
print("Average response time: %f" % (total / len(return_values)))
#{0: {'average': 0.053794, 'responses': [408, 200, 200, 200, 200]}, 1: {'average': 0.048867, 'responses': [408, 200, 200, 200, 200]}, 2: {'average': 0.052397, 'responses': [408, 200, 200, 200, 200]}, 3: {'average': 0.04803075, 'responses': [408, 200, 200, 200, 200]}, 4: {'average': 0.049209499999999996, 'responses': [408, 200, 200, 200, 200]}}