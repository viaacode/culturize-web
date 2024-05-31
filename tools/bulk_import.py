import argparse
import csv
import fileinput
import logging
import requests


def parse_args():
    parser = argparse.ArgumentParser(description="bulk upload of multiple entries to culturize-web")

    parser.add_argument("url", "-u", help="culturize-web instance url")
        # a simplification could be to determine the URL from the input CSV
    parser.add_argument("api-key", "-k", help="culturize-web instance api key", dest="key")
        # security improvement would be to also allow other ways to input key: env, conf,...
    parser.add_argument("--batch-size", "-s", help="how many entries to group in one api call",
                        type=int, default=100, dest="batch")

    parser.add_argument('files', metavar='FILE', nargs='*', help='files to upload, if empty, stdin is used')

    return parser.parse_args()


def upload(body, url, key):
    header = {"Culturize-Key": key}
    response = requests.post(url, headers=header, json=body)
    if response.status_code != 201:
        logging.error("upload failed")
    else:
        logging.error("upload success")


def main():
    args = parse_args()

    lst = []
    for line in fileinput.input(args.files):
        lst.append(line.strip())

    reader = csv.DictReader(lst)

    body = []
    i = 0
    j = 0
    for row in reader:
        if len(body) == args.batch:
            # send request
            i += 1
            j += len(body)
            logging.error(f"uploading bulk {i}")
            upload(body, args.url, args.key)

            body = []
        else:
            # append to body
            body.append({"persistent_url": row["pURI"][7:], "resource_url": row["artinflanders URL"]})

    if len(body):
        i += 1
        j += len(body)
        logging.info(f"uploading bulk {i}")
        upload(body, args.url, args.key)

    logging.warning(f"uploaded {j} records in {i} bulks")


if __name__ == "__main__":
    main()
