"""Script for partitioning people in groups such that the generated groups have
small overlap with any past groups.

The original use case for this was that I wanted to regularly partition a set of
people into small groups to assign them to eat lunch together. I wanted each
resulting group to not resemble any past lunch group and to not contain too many
people who already regularly work together.

To use this script, first create a file in this directory called "names.txt"
listing email-name pairs for each person participating in the grouping process.
The format should look as follows:
    alice@example.com,Alice
    bob@example.com,Bob
    carol@example.com,Carol
    ...

In the "past-groups/" directory, list any past groups. This is also the
directory to which the script will write newly generated groupings. Each file in
"past-groups/" should look as follows:
    alice@example.com bob@example.com erin@example.com
    dan@example.com frank@example.com grace@example.com
    ...
The above example signals that Alice, Bob, and Erin have been in the same group
in the past and that Dan, Frank, and Grace have also been in the same group in
the past. The ability to list past groups in several different files is only for
organizational convenience---the behavior would be the same if all files in
"past-groups/" were concatenated together.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Dict, List, Set
import argparse
import math
import os

import numpy as np

# Name of file containing email->name mapping.
EMAIL_TO_NAMES_FILENAME = "names.txt"
# Directory of files listing past groups.
PAST_GROUPS_DIRECTORY_PATH = "past-groups"

# Desired group size.
GROUP_SIZE = 4
# How many times to attempt to construct a grouping before giving up.
GROUPING_ATTEMPTS = 1000
# The max intersection size that any generated group may have with any past
# group.
MAX_PAST_GROUP_INTERSECTION = 2


def get_email_to_names_table(email_to_names_filename: str) -> Dict[str, str]:
    """Get a mapping of emails to names from the input file.

    Args:
        email_to_names_filename: Path to file with emails and corresponding
          names, where each email-name pair is on a separate line and each line
          looks like the following:
                email@example.com,Name

    Returns:
        A dict mapping emails to names.
    """

    email_to_names_table = {}
    with open(email_to_names_filename, "r") as email_to_names_file:
        for line in email_to_names_file:
            email, name = line.rstrip().split(sep=",")
            assert email not in email_to_names_table
            email_to_names_table[email] = name
    return email_to_names_table


def get_past_groups(past_groups_directory_path: str) -> List[Set[str]]:
    """Get all past groups of people listed in the input directory."

    Args:
        past_groups_directory_path: Path to directory holding files containing
          past groups. Each file in the directory should be text files
          containing past groups, where each group is indicated its own s
          line containing email addresses separated by spaces.

    Returns:
        A list of all past groups.
    """
    past_groups = []
    for entry in os.scandir(past_groups_directory_path):
        if not entry.name.startswith(".") and entry.is_file:
            with open(entry.path) as group_file:
                for line in group_file:
                    past_groups.append(set(line.split()))
    return past_groups


def get_random_grouping(entries: List[str], group_size: int) -> List[Set[str]]:
    """Returns a random grouping of the input list with each groups being
    of size approximately `group_size`.

    Args:
        entries: List of entries to be grouped.
        group_size: The desired size of each group.

    Returns:
        A random partition of the input entries with each group in the partition
        being of size `group_size` or `group_size - 1`.
    """

    num_groups = math.ceil(len(entries) / group_size)
    permuted_entries = np.random.permutation(entries)
    return [set(group) for group in np.array_split(permuted_entries, num_groups)]


def grouping_is_valid(
    proposed_grouping: List[Set[str]],
    past_groups: List[Set[str]],
    max_intersection_size: int,
) -> bool:
    """Returns true if no group in the proposed grouping intersects with any
    past group with intersection size strictly greater than
    `max_intersection_size`.
    """
    for group in proposed_grouping:
        for past_group in past_groups:
            if len(group & past_group) > max_intersection_size:
                return False
    return True


def print_grouping(
    grouping: List[Set[str]], email_to_names: Dict[str, str], output_filename: str
) -> None:
    """Prints the emails and names given by the input grouping and writes the
    emails to the given output file.
    """
    for group in grouping:
        print(" ".join(group))
        names = [email_to_names[email] for email in group]
        # Print out names in the format of an email greeting.
        greeting = "Hi " + (", ".join(names[:-1])) + ", and " + names[-1] + ","
        print(greeting)
        print()

    with open(output_filename, "w") as output_file:
        for group in grouping:
            output_file.write(" ".join(group) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Outputs groups of people such that the generated groups "
        "have small overlap with past groups. The program prints the groups "
        f"and writes them to `{PAST_GROUPS_DIRECTORY_PATH}/[output_file]`."
    )
    parser.add_argument(
        "output_file", type=str, help="Filename at which to write the generated groups",
    )
    args = parser.parse_args()
    output_filename = PAST_GROUPS_DIRECTORY_PATH + "/" + args.output_file

    email_to_names = get_email_to_names_table(EMAIL_TO_NAMES_FILENAME)
    past_groups = get_past_groups(PAST_GROUPS_DIRECTORY_PATH)
    emails = list(email_to_names.keys())
    for attempt in range(1, GROUPING_ATTEMPTS + 1):
        grouping = get_random_grouping(entries=emails, group_size=GROUP_SIZE)
        if grouping_is_valid(
            proposed_grouping=grouping,
            past_groups=past_groups,
            max_intersection_size=MAX_PAST_GROUP_INTERSECTION,
        ):
            print(f"Found groups in {attempt} attempts.\n")
            print_grouping(
                grouping=grouping,
                email_to_names=email_to_names,
                output_filename=output_filename,
            )
            return
    print(
        f"Failed to find groups in {GROUPING_ATTEMPTS} attempts. "
        "Try again or prune the list of past groups."
    )


if __name__ == "__main__":
    main()
