#!/usr/bin/python3
import requests, requests.exceptions, threading, logging, argparse, time, sys, json


def parse_arguments():
    parser = argparse.ArgumentParser(add_help=False, description="Spam GET requests, in parallel")

    options = parser.add_argument_group("Options")
    options.add_argument('-u', '--url', type=str, required=True, help='URL to bombard')
    options.add_argument('-t', '--threads', type=int, required=True, help='Parallel threads to hit with')
    options.add_argument('-r', '--requests', type=int, required=True, help='Requests to do with each thread')
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


def do_requests(target, amount, ret_values, index, workers_log=None):
    global TIMEOUT
    responses = []
    timings = []
    for i in range(amount):
        try:
            resp = requests.get(target, timeout=TIMEOUT)
        except requests.exceptions.Timeout:
            responses.append(requests.codes.TIMEOUT)
            timings.append(0)
            logging.error("Request #%i in %s timed out" % (i, threading.currentThread().getName()))
            continue
        except requests.exceptions.ConnectionError:
            responses.append(requests.codes.IM_A_TEAPOT)
            timings.append(0)
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
    # Stupid way to return values from a threaded method, as Py can't implement a 'return'
    ret_values.append({"responses": responses, "average": (sum(timings) / len(timings))})


def perform_attack(target_url, attack_method, worker_amount, worker_efforts, workers_log=None):
    start_time = time.time()
    threads = []
    worker_results = []
    for i in range(worker_amount):
        t = threading.Thread(target=attack_method, args=(target_url, worker_efforts, worker_results, i))
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
        logging.info("Average response time: %f" % (sum(results) / len(results)))

    def numpy_stats(results):
        logging.warn('Stats time:')
        a = np.array(results)
        logging.info("80th percentile: {}".format(np.percentile(results, 80)))
        logging.info("99th percentile: {}".format(np.percentile(results, 99)))
        logging.info("Mean: {}".format(a.mean()))
        logging.info("Minimum: {}".format(a.min()))
        logging.info("Maximum: {}".format(a.max()))
        logging.info("Variance: {}".format(a.var()))
        logging.info("Standard Deviation: {}".format(a.std()))

    try:
        import numpy as np
        numpy_stats(averages)
    except ImportError:
        no_numpy_stats(averages)
        logging.warn("No NumPy module found, so no more statistics for you.")


if __name__ == '__main__':
    global TIMEOUT
    args = parse_arguments()
    TIMEOUT = args.timeout
    setup_logging(args.logfile)
    results = perform_attack(args.url, do_requests, args.threads, args.requests)
    print_statistics(results)
