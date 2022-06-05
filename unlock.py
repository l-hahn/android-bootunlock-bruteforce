#!/bin/bash
from math import log10, ceil, floor, sqrt
from subprocess import run, DEVNULL
from argparse import ArgumentParser



def load_checked_codes(filename):
  try:
    with open(filename, 'r') as file:
        testing_codes = [
            int(line.rstrip())
            for line in file
            if line.rstrip() != ""
        ]
        return testing_codes
  except:
    return []

def save_testing_codes(filename, testing_codes = [ ]):
  with open(filename, 'a') as file:
    for current_code in testing_codes:
        file.write(f"{current_code}\n")
    print(f"Saved codes '{','.join(map(str,testing_codes))}' in file '{filename}'")


def luhn_checksum(value):
    digits = [
        (value%(10**exp))//(10**(exp-1))
        for exp in range(
            ceil(log10(value)), 0, -1
        )
    ]
    return sum(
        digits + [ d + (d > 4)
        for d in digits[-2::-2] ]
    ) % 10

def increment_unlockcode_imei(imei, checksum, code):
    return  code + checksum + floor(sqrt(imei) * 1024)


def check_unlock_code(imei, checksum, filename, limit = 0):
    unlocked = False

    checked_codes = load_checked_codes(filename)
    count_attempts = len(checked_codes)
    start_code = checked_codes[-1] if count_attempts > 0 else 1000000000000000

    testing_codes = []
    current_code = 1000000000000000
    while current_code <= start_code:
        current_code = increment_unlockcode_imei(imei, checksum, current_code)

    print(f"Start testing unlock codes with startpoint: {current_code}\n")

    while not unlocked:
        testing_codes.append(current_code)
        count_attempts += 1
        code_check_result = run(
            ['fastboot', 'oem', 'unlock', f"{current_code}"],
            stdout = DEVNULL, stderr = DEVNULL
        )
        print(f"run {count_attempts}, try with code '{current_code}': {code_check_result.returncode == 0}")

        if limit != 0 and (count_attempts%(limit-1)) == 0:
            save_testing_codes(filename, testing_codes)
            testing_codes = []
            run(
                ['fastboot', 'reboot', 'bootloader'],
                stdout = DEVNULL, stderr = DEVNULL
            )

        if code_check_result == 0:
            unlocked = True
            save_testing_codes(filename, testing_codes)
            return current_code

        current_code = increment_unlockcode_imei(imei, checksum, current_code)


def main():
    parser = ArgumentParser(
        """Programm to try by brute-force unlocking an android based
        (Huawei) Phone concerning the bootloader"""
    )

    parser.add_argument(
        "--codesfile", "-f", type=str, default="testing_codes.txt", required=False,
        help="Filename or path to store tested codes in order to directly continue"
    )

    parser.add_argument(
        "--limit", "-l", type=int, default=5, required=False,
        help=(
            "Sets a limit of code tests where afterwards a bootloader reboot is triggered."
            "Limit of 0 means no limit; defaults to 5. Is typical required by Huawei in order"
            "to"
        )
    )

    parser.add_argument(
        "--imei", "-i", type=int, required=True,
        help="The (first) imei of the phone you want to test the bootloader unlock code."
    )

    args = parser.parse_args()

    filename = args.codesfile
    limit = args.limit
    imei = args.imei


    checksum = luhn_checksum(imei)

    print(
        "Unlocking bootloader of an android smartphone - No guarantee of anything,"
        "neither success nor no damage on to your phone!\n"
        "You do everything on your own risk!\n\n"
        "WARNING! Continuing this process will make you lose data!\n\n"
        "Please make sure that USB DEBUG and OEM UNLOCK is enabled in developer settings!\n"
    )

    run(
        ['adb', 'reboot', 'bootloader'],
        stdout = DEVNULL, stderr = DEVNULL
    )

    input("Press <enter> when device is in fastboot mode\n")

    unlock_code = check_unlock_code(imei, checksum, filename, limit)

    run(['fastboot', 'getvar', 'unlocked'])
    run(['fastboot', 'reboot'])

    print(
        f"Code '{unlock_code}' successfully unlocked device!\n"
        "Please note for further usage somewhere safe!"
    )

    input("Press <enter> to exit")

if __name__ == '__main__':
  main()