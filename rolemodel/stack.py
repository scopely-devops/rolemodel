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
import time

import rolemodel.role

LOG = logging.getLogger(__name__)


class Stack(object):

    completed_states = ('CREATE_COMPLETE', 'UPDATE_COMPLETE')
    failed_states = ('ROLLBACK_COMPLETE',)

    def __init__(self, session, name, roles_template, assuming_account_id):
        self._session = session
        self._name = name
        self._template_path = roles_template
        self._assuming_account_id = str(assuming_account_id)
        self._cfn = self._session.create_client('cloudformation')

    @property
    def name(self):
        return self._name

    def exists(self):
        """
        Does Cloudformation Stack already exist?
        """
        try:
            response = self._cfn.describe_stacks(StackName=self.name)
            LOG.debug('Stack %s exists', self.name)
        except Exception:
            LOG.debug('Stack %s does not exist', self.name)
            response = None
        return response

    def wait(self):
        done = False
        while not done:
            time.sleep(1)
            response = self._cfn.describe_stacks(StackName=self.name)
            LOG.debug(response)
            status = response['Stacks'][0]['StackStatus']
            LOG.debug('Stack status is: %s', status)
            if status in self.completed_states:
                done = True
            if status in self.failed_states:
                msg = 'Could not create stack %s: %s' % (self.name, status)
                raise ValueError(msg)

    def _validate_template(self, template_body):
        LOG.debug('validate_template')
        response = self._cfn.validate_template(TemplateBody=template_body)
        return response['Parameters']

    def _create(self):
        LOG.debug('create_stack: stack_name=%s', self.name)
        template_body = open(self._template_path).read()
        self._validate_template(template_body)

        response = self._cfn.create_stack(
            StackName=self.name, TemplateBody=template_body,
            Capabilities=['CAPABILITY_IAM','CAPABILITY_NAMED_IAM'],
            Parameters=[{'ParameterKey': 'AssumingAccountID',
                         'ParameterValue': self._assuming_account_id,
                         'UsePreviousValue': False}])
        LOG.debug(response)
        self.wait()

    def _update(self):
        LOG.debug('update_stack: stack_name=%s', self.name)
        template_body = open(self._template_path).read()
        try:
            template_parameters = self._validate_template(template_body)
            parameters = [{'ParameterKey': 'AssumingAccountID',
                             'ParameterValue': self._assuming_account_id,
                             'UsePreviousValue': False}]

            # Use previous parameter values for any extra parameters defined in
            # the CloudFormation stack.
            for p in template_parameters:
                parameters.append({'ParameterKey': p['ParameterKey'], 'UsePreviousValue': True})

            response = self._cfn.update_stack(
                StackName=self.name, TemplateBody=template_body,
                Capabilities=['CAPABILITY_IAM','CAPABILITY_NAMED_IAM'],
                Parameters=parameters)
            LOG.debug(response)
        except Exception as e:
            if 'No updates are to be performed' in str(e):
                LOG.info('No Updates Required')
            else:
                raise
        self.wait()

    def update(self):
        if self.exists():
            self._update()
        else:
            self._create()

    def resources(self):
        LOG.debug('resources(): stack_name=%s', self.name)
        response = self._cfn.describe_stack_resources(
            StackName=self.name)
        LOG.debug(response)
        return response['StackResources']

    def roles(self):
        LOG.debug('roles(): stack_name=%s', self.name)
        response = self._cfn.describe_stack_resources(
            StackName=self.name)
        LOG.debug(response)
        roles = []
        for resource in response['StackResources']:
            if resource['ResourceType'] == 'AWS::IAM::Role':
                role = rolemodel.role.Role(self._session, resource)
                roles.append(role)
        return roles

    def delete(self):
        LOG.debug('delete(): stack_name=%s', self.name)
        response = self._cfn.delete_stack(StackName=self.name)
        LOG.debug(response)
