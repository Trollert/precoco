#!/usr/bin/env python3
from precoco.common.UI import create_ui
from precoco.common.miscfunctions import read_user_config, is_up_to_date


def run():
    """
    This is the main function to call to start the UI and process the inserted .htm-file.
    It only provides the control sequence, not the underlying logic. Refer to the submodules for that
    """
    # first check the local version of PreCoCo and read the config file if present
    path_directory_reports, _local_version_ = read_user_config()
    # check version and get new updater if out of date
    flag_up_to_date = is_up_to_date(_local_version_)

    create_ui(flag_up_to_date, _local_version_, path_directory_reports)


