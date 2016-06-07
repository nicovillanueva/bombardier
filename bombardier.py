#!/usr/bin/python3
import requests, threading, logging, argparse, time, sys, json, yaml, urllib, os, ast
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

def parse_orders(orders_file):
    with open(orders_file) as f:
        conf = yaml.load(f)
        for c in conf:
            orders.append(Order(c))
        return orders

class Order(object):
    def __init__(self, target):
        if type(target) is dict:
            self.id = target.get("id") or 1
            self.target = target.get("target")
            self.method = target.get("method")
            self.payload = target.get("payload") or None
            self.cookies = ast.literal_eval(target.get("cookies")) if target.get("cookies") else None
            self.headers = ast.literal_eval(target.get("headers")) if target.get("headers") else None
        else:
            self.id = 1
            self.target = target
            self.method = "GET"
            self.payload = None
            self.headers = None
            self.cookies = None
    def __str__(self):
        return "id: {}, target: {}, method: {}, payload: {}, headers: {}, cookies: {}"\
                .format(self.id, self.target, self.method, self.payload, self.headers, self.cookies)

class Squad(object):
    self.soldiers = []
    self.orders = []
    def __init__(self, army_size, orders, ammo=10, duration=0, interval=0):
        pass

    def spawn_soldiers(self, amount):
        # TODO: clear previous soldiers
        for i in amount:
            p = Soldier(name="soldier-{}".format(i), daemon=True)
            self.soldiers.append(p)
        print("{} soldiers standing by".format(amount))

    def execute(self, order=None):
        with ThreadPoolExecutor() as executor:
            executor.map(lambda x: x.start(), self.soldiers)

class Soldier(object):
    class Gun(multiprocessing.Process):
        def __init__(self, daemon=False):
            # For clarity. May be removed
            Gun.__init__(self, daemon=daemon)
        def run():
            # do request here
            pass

    # TODO: Random name from list
    def __init__(self, orders, ammo=10, duration=0, interval=0, name="UnnamedSoldier", daemon=True):
        super(Soldier, self).__init__()
        self.orders = []
        self.interval = 0
        self.duration = 0
        self.ammo = 0
        print("{} is born".format(self.name))
    #def start(order):

    def run():
        # move to Gun
        for order in orders:  # TODO: Sequential. Make parallel!
            for a in ammo:
                print("{} goes pewpew".format(self.name))
                resp = requests.request(method=order.method,
                                        url=order.target,
                                        data=order.payload,
                                        headers=order.headers,
                                        cookies=order.cookies,
                                        timeout=TIMEOUT)
            print("{} has ran out of ammo".format(self.name))


def parse_arguments():
    parser = argparse.ArgumentParser(add_help=False, description="Spam GET requests, in parallel")

    options = parser.add_argument_group("Options")
    options.add_argument('-u', '--url', type=str, required=True, help='URL to bombard')
    options.add_argument('-t', '--threads', type=int, required=True, help='Parallel threads to hit with')
    options.add_argument('-r', '--requests', type=int, required=True, help='Requests to do with each thread')
    options.add_argument('-c', '--config', type=str, required=False, help='Request configuration file to use')
    options.add_argument('--timeout', type=int, required=False, default=5, help='Seconds after the requests timeout (default: 5)')
    options.add_argument('-l', '--logfile', type=str, required=False, default='bombardier.log', help='Where to write the log')
    options.add_argument('-d', '--dump', type=str, required=False, default=None, help='Dump workers\' results in a file')
    options.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    return parser.parse_args()


def setup_logging(logfile):
    FORMAT = '%(asctime)-15s %(threadName)-10s %(levelname)s %(message)s'

    logging.basicConfig(level=logging.DEBUG,
                        format=FORMAT,
                        filename=logfile,
                        filemode='w',
                        )
    logging.addLevelName( logging.INFO,    "\033[1;32m%s\033[1;0m"   % logging.getLevelName(logging.INFO) )     # Green
    logging.addLevelName( logging.WARNING, "\033[1;33m%s\033[1;0m"   % logging.getLevelName(logging.WARNING) )  # Yellow
    logging.addLevelName( logging.ERROR,   "\033[1;31;1m%s\033[1;0m" % logging.getLevelName(logging.ERROR) )    # Bold red
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # Squelch any requests' logging lower than WARNING

    console = logging.StreamHandler()  # Log to the console
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)-8s] %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def do_requests(config, amount, ret_values, workers_log=None):
    global TIMEOUT
    responses = []
    timings = []
    for i in range(amount):
        try:
            resp = requests.request(method=config.method,
                                    url=config.target,
                                    data=config.payload,
                                    headers=config.headers,
                                    cookies=config.cookies,
                                    timeout=TIMEOUT)
        except requests.exceptions.Timeout:
            responses.append(requests.codes.TIMEOUT)
            timings.append(TIMEOUT)
            logging.error("Request #%i in %s timed out" % (i, threading.currentThread().getName()))
            continue
        except requests.exceptions.ConnectionError:
            responses.append("CONNECTION_ERROR")
            logging.error("Request #%i in %s had a connection error" % (i, threading.currentThread().getName()))
            continue

        if resp.status_code == 200:
            logging.info("Request #%i in %s had code 200 and it took %.4f seconds." % (i, threading.currentThread().getName(),
                                                                              resp.elapsed.total_seconds()))
        else:
            logging.warning("Request #%i in %s had code %i and it took %.4f seconds." % (i, threading.currentThread().getName(),
                                                                                resp.status_code,
                                                                                resp.elapsed.total_seconds()))
        timings.append(resp.elapsed.total_seconds())
        responses.append(resp.status_code)
    logging.info("Completed all requests for %s" % threading.currentThread().getName())
    # Workaround way to return values from a threaded method:
    if len(timings) is not 0:
        ret_values.append({"responses": responses, "average": (sum(timings) / len(timings))})


def perform(config, threaded_method, worker_amount, worker_efforts, workers_log=None):
    start_time = time.time()
    threads = []
    worker_results = []
    for i in range(worker_amount):
        t = threading.Thread(target=threaded_method, args=(config, worker_efforts, worker_results))
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

    logging.info("----- All done! -----")
    logging.info("Completed %i requests in %.2f seconds" % (args.requests * args.threads, end_time - start_time))
    if workers_log is not None:
        with open(workers_log) as f:
            f.write(json.dumps(ret_values))
    return worker_results


def print_statistics(worker_results):
    averages = list(map(lambda x: x.get("average"), worker_results))
    if args.dump is not None:
        with open(args.dump, mode='w') as f:
            f.write(json.dumps(worker_results, sort_keys=True, indent=2, separators=(',', ': ')))

    def no_numpy_stats(results):
        logging.info("Average time: %f" % (sum(results) / len(results)))
        wrs = []
        [wrs.extend(wr.get("responses")) for wr in worker_results]
        resps = {}
        for r in wrs:
            if r not in resps.keys():
                resps[r] = 1
            else:
                resps[r] += 1
        for r in resps.keys():
            logging.info("- {amt} responses with code {code}".format(amt=resps.get(r), code=r))


    def numpy_stats(results):
        logging.info('Stats time!')
        no_numpy_stats(results)
        a = np.array(results)
        logging.info("80th percentile: {}".format(np.percentile(results, 80)))
        logging.info("99th percentile: {}".format(np.percentile(results, 99)))
        logging.info("Minimum: {}".format(a.min()))
        logging.info("Maximum: {}".format(a.max()))
        logging.info("Variance: {}".format(a.var()))
        logging.info("Standard Deviation: {}".format(a.std()))

    if len(averages) is 0:
        logging.warn("No requests really made. Nothing to do.")
        sys.exit(0)
    try:
        import numpy as np
        numpy_stats(averages)
    except ImportError:
        no_numpy_stats(averages)
        logging.warn("No NumPy module found, so no more statistics for you.")


def is_valid_url(url, qualifying=None):
    min_attributes = ('scheme', 'netloc')
    qualifying = min_attributes if qualifying is None else qualifying
    token = urllib.parse.urlparse(url)
    return all([getattr(token, qualifying_attr)
                for qualifying_attr in qualifying])


if __name__ == '__main__':
    global TIMEOUT
    args = parse_arguments()
    TIMEOUT = args.timeout
    setup_logging(args.logfile)
    sc = TargetDefinition(args.config or args.url)
    if not is_valid_url(args.url):
        logging.error("Malformed URL: {}".format(args.url))
        sys.exit(1)
    results = perform(sc, do_requests, args.threads, args.requests)
    print_statistics(results)
