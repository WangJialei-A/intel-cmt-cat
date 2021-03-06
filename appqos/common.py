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
Common global constants and helper functions
"""

import multiprocessing
import numbers
import config # pylint: disable=cyclic-import
import stats # pylint: disable=cyclic-import


CONFIG_FILENAME = "appqos.conf"
PRODUCTION = 1
PRE_PRODUCTION = 2
BEST_EFFORT = 3

CAT_CAP = "cat"
MBA_CAP = "mba"

MANAGER = multiprocessing.Manager()
CONFIG_STORE = config.ConfigStore()
STATS_STORE = stats.StatsStore()


def is_core_valid(core):
    """
    Checks core validity

    Parameters:
        core: core to be tested
    Returns:
        result: bool
    """
    if not isinstance(core, numbers.Number):
        return False
    return core < multiprocessing.cpu_count()


def is_event_set(event):
    """
    Checks is event set

    Parameters:
        event: event to be tested
    Returns:
        result: bool
    """
    try:
        return event.is_set()
    except IOError:
        return False
