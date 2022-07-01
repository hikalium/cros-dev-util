# Copyright 2021 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Proxy server for configuring callboxes."""

import traceback
import urllib

import flask
from flask import request

from ..callbox_utils import cmw500_cellular_simulator as cmw
from ..simulation_utils import ChromebookCellularDut
from ..simulation_utils import LteSimulation


app = flask.Flask(__name__)
app.config['DEBUG'] = False

class CallboxConfiguration:
    """Callbox access configuration."""
    def __init__(self):
        self.host = None
        self.port = None
        self.dut = None
        self.simulator = None
        self.simulation = None
        self.parameter_list = None

class CallboxManager:
    """Manager object that holds configurations to known callboxes."""

    def __init__(self):
        self.configs_by_host = dict()

    def configure_callbox(self, data):
        self._require_dict_keys(
                data, 'callbox', 'hardware',
                'cellular_type', 'parameter_list')
        config = self._get_callbox_config(data['callbox'], True)
        if data['hardware'] == 'CMW':
            config.simulator = cmw.CMW500CellularSimulator(
                    config.host, config.port, app.logger)

        config.dut = ChromebookCellularDut.ChromebookCellularDut(
                'no_dut_connection', app.logger)
        if data['cellular_type'] == 'LTE':
            config.simulation = LteSimulation.LteSimulation(
                    config.simulator, app.logger, config.dut,
                    {
                            'attach_retries': 1,
                            'attach_timeout': 120
                    }, None)

        config.parameter_list = data['parameter_list']
        return 'OK'

    def begin_simulation(self, data):
        self._require_dict_keys(data, 'callbox')
        config = self._get_callbox_config(data['callbox'])
        config.simulation.parse_parameters(config.parameter_list)
        config.simulation.start()
        return 'OK'

    def send_sms(self, data):
        self._require_dict_keys(data, 'callbox')
        config = self._get_callbox_config(data['callbox'])
        config.simulation.send_sms(data['sms'])
        return 'OK'

    def _get_callbox_config(self, callbox, create_if_dne=False):
        if callbox not in self.configs_by_host:
            if create_if_dne:
                url = urllib.parse.urlsplit(callbox)
                if not url.hostname:
                    url = urllib.parse.urlsplit('//' + callbox)
                if not url.hostname:
                    raise ValueError(f'Unable to parse callbox host: "{callbox}"')
                config = CallboxConfiguration()
                config.host = url.hostname
                config.port = 5025 if not url.port else url.port
                self.configs_by_host[callbox] = config
            else:
                raise ValueError(f'Callbox "{callbox}" not configured')
        return self.configs_by_host[callbox]

    @staticmethod
    def _require_dict_keys(d, *keys):
        for key in keys:
            if key not in d:
                raise Exception(f'Missing required data key "{key}"')

callbox_manager = CallboxManager()

path_lookup = {
        'config': callbox_manager.configure_callbox,
        'start': callbox_manager.begin_simulation,
        'sms': callbox_manager.send_sms,
}

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def entrypoint(path):
    try:
        return path_lookup[path](request.json)
    except Exception as e:
        return '%s:\n%s' % (e, traceback.format_exc()), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
