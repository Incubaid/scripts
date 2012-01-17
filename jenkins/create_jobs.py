# create_jobs.py - Utility to create Jenkins jobs based on existing Git branches
#
# Copyright (C) 2011  Incubaid BVBA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Utility to create Jenkins jobs based on existing Git branches
'''

import os
import re
import logging
import optparse
import subprocess

try:
    from lxml import etree
    print("running with lxml.etree")
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree
            except ImportError:
                # normal ElementTree install
                import elementtree.ElementTree as etree

import autojenkins
import autojenkins.jobs

TEMPLATE_NAME = '_%s-template'
LOGGER = logging.getLogger('create_jobs')

def job_exists(jenkins, name):
    '''Check whether a given job exists

    :param jenkins: Jenkins API connection
    :type jenkins: `autojenkins.Jenkins`
    :param name: Name of job to check
    :type name: `str`

    :return: Whether the job exists
    :rtype: `bool`
    '''

    LOGGER.info('Checking whether job %s exists', name)

    jobs = jenkins.all_jobs()

    for job_name, _ in jobs:
        if job_name == name:
            LOGGER.debug('Job %s found', name)
            return True

    LOGGER.debug('Job %s not found', name)
    return False


def list_branches(remote, pattern):
    '''List refs on a remote repository matching a given pattern

    :param remote: URI of the remote to list
    :type remote: `str`
    :param pattern: Compiled regular expression to run on retrieved refs
        This expression should include a single group, which is extracted and
        returned by this procedure.
    :type pattern: Compiled regular expression

    :return: Yields extracted refs
    :rtype: `iterable` of `str`
    '''

    LOGGER.info('Listing Git branches')

    output = subprocess.check_output(('git', 'ls-remote', remote))
    lines = output.splitlines()

    for line in lines:
        _, name = line.split(None, 1)

        match = pattern.match(name)
        if match:
            name = match.groups()[0]
            LOGGER.debug('Found branch: %s', name)
            yield name


def create_job(jenkins, name, template, branch):
    '''Create a job on the given Jenkins server

    :param jenkins: Jenkins API connection
    :type jenkins: `autojenkins.Jenkins`
    :param name: Name of the new job
    :type name: `str`
    :param template: Name of job to use as a template
    :type template: `str`
    :param branch: Branch to build from
    :type branch: `str`
    '''

    LOGGER.info('Creating job %s for branch %s using template %s',
        name, branch, template)

    declaration = r"<?xml version='1.0' encoding='UTF-8'?>"
    encoding = 'utf-8'

    LOGGER.debug('Retrieving configuration of job %s', template)
    xml = jenkins.get_config_xml(template)

    LOGGER.debug('Rewriting configuration')
    root = etree.fromstring(xml)

    for child in root.getchildren():
        if child.tag == 'disabled':
            LOGGER.debug('Setting "disabled" to "false"')
            child.text = 'false'

        if child.tag == 'scm' \
            and child.get('class') == 'hudson.plugins.git.GitSCM':

            for child2 in child.getchildren():
                if child2.tag == 'branches':
                    for child3 in child2.getchildren():
                        if child3.tag == 'hudson.plugins.git.BranchSpec':
                            for child4 in child3.getchildren():
                                if child4.tag == 'name':
                                    LOGGER.debug('Setting branch to %s',
                                        branch)
                                    child4.text = branch


    new_xml = etree.tostring(root)
    config = '%s\n%s' % (declaration, new_xml.encode(encoding))

    LOGGER.info('Creating job %s', name)

    autojenkins.jobs.requests.post(
        jenkins._build_url(autojenkins.jobs.NEWJOB),
        data=config,
        params={'name': name},
        headers={'Content-Type': 'application/xml'},
        auth=jenkins.auth
    )


def main():
    parser = optparse.OptionParser()

    parser.add_option('-u', '--username', dest='username',
        help='Jenkins username', metavar='USER')
    parser.add_option('-p', '--password', dest='password',
        help='Jenkins password', metavar='PASSWORD')
    parser.add_option('-a', '--address', dest='address',
        help='Jenkins address', metavar='URI')

    options, args = parser.parse_args()

    username = options.username
    password = options.password
    address = options.address or os.environ['JENKINS_URL']

    if (username and not password) or (not username and password):
        raise parser.error('Username and password are not mutually exclusive')

    if len(args) != 2:
        raise parser.error('Missing arguments')

    LOGGER.info('Address: %s', address)

    if username and password:
        LOGGER.info('Username: %s', username)
        auth = (username, password)
    else:
        LOGGER.info('No authentication provided')
        auth = None

    jenkins = autojenkins.Jenkins(address, auth=auth)

    project = args[0]
    LOGGER.info('Project: %s', project)
    remote = args[1]
    LOGGER.info('Remote: %s', remote)

    template = TEMPLATE_NAME % project
    if not job_exists(jenkins, template):
        raise RuntimeError('Missing template job: %s' % template)

    branches = list_branches(remote, re.compile('refs/heads/(.*)'))

    for branch in branches:
        if branch == 'HEAD':
            LOGGER.debug('Skipping HEAD branch')
            continue

        LOGGER.debug('Handling branch %s', branch)

        if not job_exists(jenkins, '%s-%s' % (project, branch)):
            name = '%s-%s' % (project, branch)
            create_job(jenkins, name, template, branch)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    main()
