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

import os

__version__ = open(os.path.join(os.path.dirname(__file__), '_version')).read()

import logging

import botocore.session

import rolemodel.stack
import rolemodel.group

LOG = logging.getLogger(__name__)

DebugFmtString = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
InfoFmtString = '%(message)s'

AssumeRolePolicy = """{{
  "Version": "2012-10-17",
  "Statement": [{{
    "Effect": "Allow",
    "Action": ["sts:AssumeRole"],
    "Resource": "{arn}"
  }}]
}}"""


class RoleModel(object):

    GroupName = '{acct}.{role}'
    Path = '/RoleModel/'

    def __init__(self, config, debug=False):
        if debug:
            self.set_logger('rolemodel', logging.DEBUG)
        else:
            self.set_logger('rolemodel', logging.INFO)
        self.config = config

    def debug(self):
        self.set_logger('rolemodel', logging.DEBUG)

    def set_logger(self, logger_name, level=logging.INFO):
        """
        Convenience function to quickly configure full debug output
        to go to the console.
        """
        log = logging.getLogger(logger_name)
        log.setLevel(level)

        ch = logging.StreamHandler(None)
        ch.setLevel(level)

        # create formatter
        if level == logging.INFO:
            formatter = logging.Formatter(InfoFmtString)
        else:
            formatter = logging.Formatter(DebugFmtString)

        # add formatter to ch
        ch.setFormatter(formatter)

        # add ch to logger
        log.addHandler(ch)

    def update(self):
        for acct in self.config['assumable_accounts']:
            LOG.info('updating account: %s', acct['name'])
            LOG.debug(acct)
            session = botocore.session.get_session()
            session.profile = acct['profile']
            stack = rolemodel.stack.Stack(
                session, 'RoleModel', self.config['assumable_roles'],
                self.config['master_account_id'])
            stack.update()
        self.update_groups()

    def delete(self):
        LOG.debug('delete called')
        for acct in self.config['assumable_accounts']:
            LOG.info('deleting %s', acct['name'])
            session = botocore.session.get_session()
            session.profile = acct['profile']
            stack = rolemodel.stack.Stack(
                session, 'RoleModel', self.config['assumable_roles'],
                self.config['master_account_id'])
            stack.delete()
        self.delete_groups()

    def list(self):
        LOG.debug('list called')
        list_data = {}
        for acct in self.config['assumable_accounts']:
            session = botocore.session.get_session()
            session.profile = acct['profile']
            stack = rolemodel.stack.Stack(
                session, 'RoleModel', self.config['assumable_roles'],
                self.config['master_account_id'])
            if stack.exists():
                list_data[acct['name']] = [
                    r.physical_name for r in stack.roles()]
        return list_data

    def _check_for_groups(self, iam, acct, stack):
        groups = iam.list_groups()
        group_names = [g['GroupName'] for g in groups['Groups']]
        for role in stack.roles():
            group_name = self.GroupName.format(
                acct=acct['name'], role=role.logical_name)
            group = rolemodel.group.Group(
                iam, group_name, self.Path)
            group.check(group_names)
            policy_name = '%s-Policy' % group_name
            policy_document = AssumeRolePolicy.format(arn=role.arn)
            group.add_policy(policy_name, policy_document)
            LOG.info('creating policy %s', policy_name)

    def update_groups(self):
        LOG.debug('update_groups called')
        session = botocore.session.get_session()
        session.profile = self.config['master_account_profile']
        iam = session.create_client('iam')
        for acct in self.config['assumable_accounts']:
            session = botocore.session.get_session()
            session.profile = acct['profile']
            stack = rolemodel.stack.Stack(
                session, 'RoleModel', self.config['assumable_roles'],
                self.config['master_account_id'])
            if stack.exists():
                self._check_for_groups(iam, acct, stack)

    def delete_groups(self):
        LOG.debug('delete_groups called')
        session = botocore.session.get_session()
        session.profile = self.config['master_account_profile']
        iam = session.create_client('iam')
        response = iam.list_groups(PathPrefix=self.Path)
        for group in response['Groups']:
            group = rolemodel.group.Group(
                iam, group['GroupName'], group['Path'])
            group.delete()

    def sync_users(self, users):
        LOG.debug('sync_users called')
        session = botocore.session.get_session()
        session.profile = self.config['master_account_profile']
        iam = session.create_client('iam')
        for acct in self.config['assumable_accounts']:
            if acct['name'] in users:
                session = botocore.session.get_session()
                session.profile = acct['profile']
                stack = rolemodel.stack.Stack(
                    session, 'RoleModel', self.config['assumable_roles'],
                    self.config['master_account_id'])
                if stack.exists():
                    for role in stack.roles():
                        role_map = users[acct['name']]
                        if role.logical_name in role_map:
                            group_name = self.GroupName.format(
                                acct=acct['name'], role=role.logical_name)
                            group = rolemodel.group.Group(
                                iam, group_name, self.Path)
                            group.sync_users(role_map[role.logical_name])
