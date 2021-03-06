#!/usr/bin/env python3
#  This file is part of Bitextor.
#
#  Bitextor is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Bitextor is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Bitextor.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import base64
import os
import string
import sys
import html

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../utils")
from toolwrapper import ToolWrapper
from common import open_xz_or_gzip_or_plain


def filter_digits_and_punctuation(original_text):
    text_split = original_text.split()
    if len(text_split) == 1 and sum([1 for m in text_split[0] if m in string.punctuation + string.digits]) > len(
            text_split[0]) // 2:
        return False

    return True


def split_sentences(original_text, sent_tokeniser):
    tokenized_segs = ""
    seg = ""
    sent_tokeniser.writeline(html.escape(original_text.replace("\n\n", "\n").strip()) + "\n")
    while seg != "<P>":
        seg = sent_tokeniser.readline().strip()
        sys.stderr.write(seg+"\n")
        if seg != "" and seg != "<P>":
            tokenized_segs = tokenized_segs + seg + "\n"

    output = html.unescape(tokenized_segs)

    return [n for n in output.split("\n") if filter_digits_and_punctuation(n)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", dest="text_file", required=True,
                        help='File containing the plain text extracted from the HTML documents in a WARC file, '
                             'encoded in base64')
    parser.add_argument("--url", dest="url_file", required=True,
                        help="File containing the list of urls of the documents in a WARC file")
    parser.add_argument("--splitter", dest="splitter", default="",
                        help="Sentence splitting command")
    parser.add_argument("--tokenized", dest="tokenized", action="store_true",
                        help='Don\'t apply sentence splitter to the text (split by newlines only).')
    parser.add_argument("--output_prefix", dest="output_prefix", default="", required=False,
                        help="Prefix for output files within directory")
    parser.add_argument("--prune", dest="prune_threshold", type=int, default=80,
                        help="Prune sentences longer than n (words/characters)", required=False)
    parser.add_argument("--prune_type", dest="prune_type", choices={"words", "chars"},
                        default="words", help="Prune sentences either by words or characters", required=False)
    args = parser.parse_args()

    with open_xz_or_gzip_or_plain(args.text_file) as text_reader, \
            open_xz_or_gzip_or_plain(args.url_file) as url_reader:
        senttok = ToolWrapper(args.splitter.split())
        for line in text_reader:
            text = base64.b64decode(line.strip()).decode("utf-8")
            uri = next(url_reader, None).strip()

            if not text:
                continue

            if args.tokenized:
                split = split_sentences(text, None)
            else:
                split = split_sentences(text, senttok)

            for extracted_line in split:

                extracted_line = extracted_line.strip()
                if not extracted_line:
                    continue

                # prune long sentences
                extracted_line = extracted_line
                if args.prune_type == "chars":
                    if len(extracted_line) > args.prune_threshold:
                        continue
                elif args.prune_type == "words":
                    if len(extracted_line.split()) > args.prune_threshold:
                        continue

                print("{0}\t{1}".format(uri, extracted_line))
