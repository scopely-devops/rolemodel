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
import json

LOG = logging.getLogger(__name__)


class Group(object):

    def __init__(self, iam, name, path):
        self._iam = iam
        self.name = name
        self.path = path

    def _delete_policies(self):
        LOG.info('Deleting policies from group %s', self.name)
        response = self._iam.list_group_policies(GroupName=self.name)
        LOG.debug(response)
        for policy in response['PolicyNames']:
            response = self._iam.delete_group_policy(
                GroupName=self.name, PolicyName=policy)
            LOG.debug(response)

    def _add_policy(self, policy_name, policy_document):
        LOG.debug('Adding policy %s to group %s', policy_name, self.name)
        response = self._iam.put_group_policy(
            GroupName=self.name, PolicyName=policy_name,
            PolicyDocument=policy_document)
        LOG.debug(response)

    def _check_policy(self, policy_name, policy_document):
        response = self._iam.list_group_policies(GroupName=self.name)
        LOG.debug(response)
        if policy_name in response['PolicyNames']:
            LOG.info('Group %s already contains policy %s',
                     self.name, policy_name)
            response = self._iam.get_group_policy(
                GroupName=self.name, PolicyName=policy_name)
            LOG.debug(response)
            new_policy = json.loads(policy_document)
            old_policy = response.get('PolicyDocument', '{}')
            new_resource = new_policy['Statement'][0]['Resource']
            old_resource = old_policy['Statement'][0]['Resource']
            if new_resource != old_resource:
                LOG.debug('Existing policy is referencing wrong role')
                self._add_policy(policy_name, policy_document)
        else:
            self._add_policy(policy_name, policy_document)

    def check(self, group_names=None):
        if group_names is None:
            response = self._iam.list_groups(PathPrefix=self.path)
            LOG.debug(response)
            group_names = [g['GroupName'] for g in response['Groups']]
        if self.name not in group_names:
            LOG.info('creating group %s', self.name)
            response = self._iam.create_group(
                GroupName=self.name, Path=self.path)
            LOG.debug(response)

    def add_policy(self, policy_name, policy_document):
        LOG.info('Adding policy %s to group %s',
                 policy_name, self.name)
        self._check_policy(policy_name, policy_document)

    def delete(self):
        LOG.info('deleting group %s', self.name)
        self._delete_policies()
        response = self._iam.delete_group(GroupName=self.name)
        LOG.debug(response)

    def sync_users(self, users):
        LOG.info('syncing users for group %s to %s', self.name, users)
        response = self._iam.get_group(GroupName=self.name)
        LOG.debug(response)
        current_users = response['Users']
        for user in current_users:
            if user['UserName'] not in users:
                response = self._iam.remove_user_from_group(
                    GroupName=self.name, UserName=user['UserName'])
                LOG.debug(response)
        existing_usernames = [u['UserName'] for u in current_users]
        for user_name in users:
            if user_name not in existing_usernames:
                response = self._iam.add_user_to_group(
                    GroupName=self.name, UserName=user_name)
                LOG.debug(response)
