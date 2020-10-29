from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Dict, List, Set
import argparse
import math
import os

import numpy as np

EMAIL_TO_NAMES_FILENAME = "names.txt"
PAST_GROUPS_DIRECTORY_PATH = "past-groups"

GROUP_SIZE = 4
MAKE_GROUP_ATTEMPTS = 1000
MAX_PAST_GROUP_INTERSECTION = 2


def get_email_to_names_table(email_to_names_filename: str) -> Dict[str, str]:
    email_to_names_table = {}
    with open(email_to_names_filename, "r") as email_to_names_file:
        for line in email_to_names_file:
            email, name = line.rstrip().split(sep=",")
            assert email not in email_to_names_table
            email_to_names_table[email] = name
    return email_to_names_table


def get_past_groups(past_groups_directory_path: str) -> List[Set[str]]:
    past_groups = []
    for entry in os.scandir(past_groups_directory_path):
        with open(entry.path) as group_file:
            for line in group_file:
                past_groups.append(set(line.split()))
    return past_groups


def get_random_grouping(emails: List[str]) -> List[Set[str]]:
    num_groups = math.ceil(len(emails) / GROUP_SIZE)
    permuted_emails = np.random.permutation(emails)
    return [set(group) for group in np.array_split(permuted_emails, num_groups)]


def grouping_is_valid(
    proposed_grouping: List[Set[str]], past_groups: List[Set[str]]
) -> bool:
    for group in proposed_grouping:
        for past_group in past_groups:
            if len(group & past_group) > MAX_PAST_GROUP_INTERSECTION:
                return False
    return True


def print_grouping(
    grouping: List[Set[str]], email_to_names: Dict[str, str], output_filename: str
) -> None:
    for group in grouping:
        print(" ".join(group))
        print(", ".join(email_to_names[email] for email in group))
        print()

    with open(output_filename, "w") as output_file:
        for group in grouping:
            output_file.write(" ".join(group) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Outputs groups of people such that the generated groups have "
        "small overlap with past groups."
    )
    parser.add_argument(
        "--output_file",
        type=str,
        help="Filename at which to write the generated groups",
    )
    args = parser.parse_args()
    output_filename = PAST_GROUPS_DIRECTORY_PATH + "/" + args.output_file

    email_to_names = get_email_to_names_table(EMAIL_TO_NAMES_FILENAME)
    past_groups = get_past_groups(PAST_GROUPS_DIRECTORY_PATH)
    emails = list(email_to_names.keys())
    for attempt in range(1, MAKE_GROUP_ATTEMPTS + 1):
        grouping = get_random_grouping(emails)
        if grouping_is_valid(proposed_grouping=grouping, past_groups=past_groups):
            print(f"Found groups in {attempt} attempts.\n")
            print_grouping(
                grouping=grouping,
                email_to_names=email_to_names,
                output_filename=output_filename,
            )
            return
    print(
        f"Failed to find groups in {MAKE_GROUP_ATTEMPTS} attempts. "
        "Try pruning the list of past groups."
    )


if __name__ == "__main__":
    main()
