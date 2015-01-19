# Copyright (c) 2015 Scopely, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import logging

LOG = logging.getLogger(__name__)


class Role(object):

    def __init__(self, session, data):
        self._session = session
        self.logical_name = data['LogicalResourceId']
        self.physical_name = data['PhysicalResourceId']
        self.stack_arn = data['StackId']
        self._iam = self._session.create_client('iam')
        self._arn = None

    @property
    def arn(self):
        if self._arn is None:
            response = self._iam.get_role(
                RoleName=self.physical_name)
            LOG.debug(response)
            self._arn = response['Role']['Arn']
            LOG.debug('role_arn: %s', self._arn)
        return self._arn
