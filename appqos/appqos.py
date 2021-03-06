#!/usr/bin/env python2.7

################################################################################
# BSD LICENSE
#
# Copyright(c) 2019 Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
################################################################################

"""
Main module.
Parses command line arguments, sets up logging, initialises perf interface,
REST API server and runs main logic (AppQoS)
"""

import argparse
import multiprocessing
import signal
import syslog

from time import sleep
from jsonschema import ValidationError

import cache_ops
import caps
import common
import log
import rest


class AppQoS(object):
    """
    Main logic.
    Starts and stops all processes.
    Handles configuration changes.
    """


    def __init__(self):
        self.stop_event = multiprocessing.Event()


    def run(self, args):
        """
        Runs main loop.

        Parameters:
            args: command line arguments
        """

        try:
            common.CONFIG_STORE.from_file(args.config)
        except IOError as ex:
            log.error("Error reading from config file {}... ".format(args.config))
            log.error(ex)
            return
        except (ValueError, ValidationError) as ex:
            log.error("Could not parse config file {}... ".format(args.config))
            log.error(ex)
            return

        # get SYS, HP, BE PIDs and cores
        p_pids = common.CONFIG_STORE.get_attr_list('pids', common.PRODUCTION)
        p_cores = common.CONFIG_STORE.get_attr_list('cores', common.PRODUCTION)

        pp_pids = common.CONFIG_STORE.get_attr_list('pids', common.PRE_PRODUCTION)
        pp_cores = common.CONFIG_STORE.get_attr_list('cores', common.PRE_PRODUCTION)

        be_pids = common.CONFIG_STORE.get_attr_list('pids', common.BEST_EFFORT)
        be_cores = common.CONFIG_STORE.get_attr_list('cores', common.BEST_EFFORT)

        log.debug("P Pool")
        log.debug("Cores: {}".format(p_cores))
        log.debug("PIDs: {}".format(p_pids))

        log.debug("PP Pool")
        log.debug("Cores: {}".format(pp_cores))
        log.debug("PIDs: {}".format(pp_pids))

        log.debug("BE Pool")
        log.debug("Cores: {}".format(be_cores))
        log.debug("PIDs: {}".format(be_pids))

        # set initial, static CAT configuration
        log.info("Configuring CAT")
        result = cache_ops.configure_cat()
        if result != 0:
            log.error("Failed to apply initial CAT configuration, terminating...")
            return

        # set CTRL+C sig handler
        signal.signal(signal.SIGINT, self.signal_handler)

        while not self.stop_event.is_set():
            log.debug("GENERAL stats: {}".format(common.STATS_STORE.general_stats_get()))

            if common.CONFIG_STORE.is_config_changed():
                log.info("Configuration changed")
                cache_ops.configure_cat()

            sleep(1)

        log.info("Terminating...")

        return


    def signal_handler(self, _signum, _frame):
        """
        Handles CTR+C
        """

        print "CTRL+C..."
        self.stop_event.set()


def main():
    """
    Main entry point
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', metavar="PATH", default=common.CONFIG_FILENAME,
                        help="Configuration file path")
    parser.add_argument('--port', metavar=("PORT"), default=[5000], type=int, nargs=1,
                        help="REST API port")
    parser.add_argument('-V', '--verbose', action='store_true', help="Verbose mode")
    cmd_args = parser.parse_args()

    # configure syslog output
    syslog.openlog("AppQoS")

    if cmd_args.verbose:
        log.enable_verbose()

    result = cache_ops.PQOS_API.init()
    if result != 0:
        log.error("libpqos initialization failed, Terminating...")
        return

    # initialize capabilities
    result = caps.caps_init()
    if result == 0:
        # initialize main logic
        app_qos = AppQoS()

        # start REST API server
        server = rest.Server()
        result = server.start("0.0.0.0", cmd_args.port[0], cmd_args.verbose)
        if result == 0:
            # run main logic
            app_qos.run(cmd_args)

            # stop REST API server
            server.terminate()
        else:
            log.error("Failed to start REST API server, Terminating...")
    else:
        log.error("Required capabilities not supported, Terminating...")

    # de-initialize libpqos
    cache_ops.PQOS_API.fini()


if __name__ == '__main__':
    main()
