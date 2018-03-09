# Copyright (C) 2015 UCSC Computational Genomics Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import logging
import os
import subprocess

from toil.provisioners.abstractProvisioner import AbstractProvisioner

logger = logging.getLogger(__name__)


class AnsibleDriver(AbstractProvisioner):
    """
    Wrapper class for Ansible calls.
    """
    contrib = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'contrib')
    inventory = ''  # to be set by child class

    def __init__(self, playbooks, config=None):
        self.playbooks = playbooks
        super(AnsibleDriver, self).__init__(config)

    def callPlaybook(self, playbook, ansibleArgs, wait=True, tags=["all"]):
        """
        Run a playbook.

        :param playbook: An Ansible playbook to run.
        :param ansibleArgs: Arguments to pass to the playbook.
        :param wait: Wait for the play to finish if true.
        :param tags: Control tags for the play.
        """
        playbook = os.path.join(self.playbooks, playbook)  # Path to playbook being executed
        verbosity = "-vvvvv" if logger.isEnabledFor(logging.DEBUG) else "-v"
        command = ["ansible-playbook", verbosity, "--tags", ",".join(tags), "--extra-vars"]
        command.append(" ".join(["=".join(i) for i in ansibleArgs.items()]))  # Arguments being passed to playbook
        command.append(playbook)

        logger.info("Executing Ansible call `%s`", " ".join(command))
        p = subprocess.Popen(command)
        if wait:
            p.wait()
            if p.returncode != 0:
                logger.error("Ansible reported an error when executing playbook %s" % playbook)

    @classmethod
    def _getInventory(cls, clusterName):
        """
        List all nodes in the cluster.
        Data model info: https://docs.ansible.com/ansible/latest/guide_azure.html#dynamic-inventory-script.

        :param clusterName: The cluster identified by the name of the resource group.
        :return: A list of nodes as dictionaries of properties.
        """
        command = ["python", os.path.join(cls.contrib, cls.inventory), "--resource-groups", clusterName]
        data = subprocess.check_output(command)
        return json.loads(data)
