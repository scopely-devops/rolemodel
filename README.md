rolemodel
=========

**Rolemodel** is a command line tool that helps you set up and maintain
cross-account IAM roles for the purpose of using them in the new
[switch role](https://aws.amazon.com/blogs/aws/new-cross-account-access-in-the-aws-management-console/)
capability of the AWS management console.  These same cross-account roles
can also be used with the AWSCLI as described
[here](http://lexical.scopely.com/2015/01/09/switching-roles/).

The main benefit of enabling these cross-account roles is that you only
have to maintain a single set of IAM users in one "master" AWS account.
By controlling which IAM groups these users are members of, you can control
which other accounts they have access to and what privileges they have
in each of those accounts.

A Little Terminology
--------------------

For the purposes of this document, lets define a couple of terms.

* **Assumable Account** is an AWS account in which IAM roles have been created
  for the purpose of allowing cross-account access.  You can have any number of
  assumable accounts.
* **Master Account** is the account in which you will create and maintain IAM
  users.  This is the account your users will log into to switch to other
  assumable accounts.  You can have only one master account.

What Does rolemodel Do?
-----------------------

The ``rolemodel`` tool:

* Uses CloudFormation to create a consistent set of roles across all assumabe
  accounts you specify.
* Creates IAM groups in the master account to control which IAM users in the
  master account can assume which roles in which assumable accounts.  If you
  have defined four roles and you have 4 assumable accounts, ``rolemodel`` will
  create a total of 16 groups in the master account.
* Optionally, ``rolemodel`` can also be used to map existing IAM users in the
  master account into the appropriate roles for each of the assumable
  accounts.  It will not create IAM users for you.

The ``rolemodel`` tool will create all roles and groups initially but can also
be used to update roles over time.  If you add more roles or change the
policies of existing roles you can run the ``update`` command and ``rolemodel``
will take care of the rest.

What Do I Have To Do?
---------------------

As an administrator you are responsible for:

* Defining the IAM roles and related policies that you want to enable in all of
  your assumable accounts.
* Running the ``rolemodel`` tool to create and update the IAM roles when
  necessary.
* Manage the membership in the IAM groups created in the master account.  By
  adding an IAM user to one of the IAM groups you are granting that user the
  ability to switch to that account with the privileges granted by the IAM
  policies associated with that IAM role.
* Carefully control IAM access in the master account.  Any IAM user that can
  change group membership in the master account has the ability to elevate any
  IAM user in the master account to the most-privileged IAM role in all
  assumable accounts.  You should control this carefully!

Getting Started
---------------

First, you need to install ``rolemodel``.  The easiest way is with pip,
preferably inside a virtualenv.

    $ pip install rolemodel

You can also clone the
[Github repo](https://github.com/scopely-devops/rolemodel) and then run
``python setup.py install`` inside the cloned directory.

``rolemodel`` is built with [botocore](https://github.com/boto/botocore) and
uses the same credential file as defined by
[AWSCLI](https://github.com/aws/aws-cli).

The next step is to define your master set of roles in a CloudFormation
template.  There is a sample set of roles contained in the file
``samples/roles.cf`` but you should edit this to suit your needs.  Each role
defined in your CloudFormation template will be created in all of the assumable
accounts you specify.

The next thing you need to do is create a configuration file to tell
``rolemodel`` about your assumable accounts and other info.  There is a sample
YAML config file in ``samples/config.yml``.  You need to provide the following
information in the config file.

* **assumable_roles** should be the path to the CloudFormation template
  defining the IAM roles that will be created in each assumable account.
* **master_account_id** is the 12-digit ID for the account that will be the
  master account.
* **master_account_profile** is the name of the profile within your AWS config
  or credential file that contains the credentials for the master account.
* for each assumable account:
    * **name** is the symbolic name of the assumable account.  This name is used
    when constructing the group names in the master account.
    * **profile** is the name of the profile within your AWS config or
    credential file that contains the credentials for this assumable account.
    These credentials must be able to create IAM roles within the assumabl
    account.

Once you have the IAM roles defined and your configuration file created you can
run the ``rolemodel`` command line tool.

    $ rolemodel <path to config file> update

This will create or update all of the IAM roles defined in your CloudFormation
template in all assumable accounts specified in your configuration file.  It
will then create or update all required IAM groups in your master account.  You
can run this command multiple times.  If no changes have been made in your IAM
roles then nothing will be done by ``rolemodel``.

If you want to get a list of all roles and all assumable accounts, use:

    $ rolemodel <path to config file> list

Finally, if you want to delete all IAM roles in all assumable accounts and also
delete all IAM groups in the master account, use:

    $ rolemodel <path to config file> delete

Managing Users in Master Account
--------------------------------

You can do the above steps and then manually manage the process of making IAM
users in the master account members of the appropriate groups to allow them to
assume roles in assumable accounts.  However, ``rolemodel`` does provide a
mechanism to support this part of the process as well.

To take advantage of this feature, you need an additional YAML file that maps
existing IAM users in the master account into the necessary IAM groups.  The
structure of this file is shown below.

    ---
    acct1:
      role1:
        - user1
        - user2
      role2:
        - user3
        - user4
    acct2:
      role1:
        - user1
        - user3
      role2:
        - user5
        - user6

The main keys in this dictionary are the names of the assumable accounts.
Within each of the accounts are additionaly dictionaries for each of the
assumable roles that are defined.  And each role name contains a list of
existing IAM users in the master account that should be allowed to assume that
role.

Once you have defined this file for your accounts, you can run the command to
sync your groups with this file.

    $ rolemodel <path to config file> sync_users <path to user map file>

The ``sample`` directory includes an example of a user map file you can edit
for your purposes.

Groups In Master Account
------------------------

The name of each group created in the master account will be of the form:

    <assumble account name>.<role name>

The ``assumable account name`` comes from the name you provide for the
assumable account in the config file.  The ``role name`` comes from the name
used for the role in the CloudFormation template.

In addition, all groups created by ``rolemodel`` will have a path of
/RoleModel/ to help separate them from other resources in IAM.
