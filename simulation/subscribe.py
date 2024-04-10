import os
import argparse
import subprocess
import logging
from multiprocessing import Process


def build_command(topic_name):
    return [
    "gz",
    "topic",
    "--echo",
    "--json-output",
    "--topic",
    topic_name,
]


def worker_function(topic_name, output_dir):
    
    output_filename = f'{os.path.basename(topic_name)}.bag'
    full_path = os.path.join(output_dir, output_filename)
    logging.info(f'Dumping messages for topic {topic_name} at {full_path}')
    with open(full_path, "w") as output:
        sub = subprocess.Popen(
            build_command(topic_name),
            stdout=subprocess.PIPE,
        )
        for line in iter(sub.stdout.readline, ""):
            output.write(line.decode())
            output.flush()


def main(args):
    output_dir = "output"
    logging.info(f'Creating {output_dir}.')
    os.makedirs(output_dir, exist_ok=True)

    workers = []
    logging.info(f'topics: {args.topic_names}')
    for t in args.topic_names:
        worker = Process(target=worker_function, args=(t, output_dir))
        logging.info(f'Starting a worker for topic name {t}.')
        worker.start()
        workers.append(worker)

    for w in workers:
        w.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug", dest="debug",
        action="store_true",
        help="Enable debugging")
    parser.add_argument(
        "-t", "--topic-name", # nargs="+",
        dest="topic_names", required=True,
        action="append",
        help="List of topic names to subscribe")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')
    logging.debug(args)
    exit(main(args))
