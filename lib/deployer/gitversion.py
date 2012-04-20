#!/usr/bin/env python
"""
This module will calculate a verion number based on the git status
of the current project.

It assumes that the branch names follow a convention where there is
a single integration branch, a single production branch and release
branches are prefixed with 'RELEASE'.  In addition this relies on
tags marked SIGNOFF to calculate production versions.  The specific
names for the integration and production branches can be specified as
"""

from subprocess import call, Popen, PIPE
import re
import datetime
import time

EMPTY_STRING = lambda value: value != ''
STRING_STRIPPER = lambda value: value.strip()

DESCRIPTION = 'Generate a version from the git status'

def format_version(raw_version):
    """
    Format the date portion of a version from a raw date string of format YYYY-mm-dd.
    The final version will be: Y.[m]m.[d]d
    """
    parts = raw_version.split('-')
    parts[1] = parts[1][-1] if parts[1][0] == '0' else parts[1]
    parts[2] = parts[2][-1] if parts[2][0] == '0' else parts[2]
    return '.'.join([parts[0][-1], parts[1], parts[2]])

def get_integration_version():
    """
    Construct the version for an integration release.  The format is:
    Y.[m]m.[d]d-dev.{s} where the year, month and day are derived from the
    next release date and the snapshot version is the timestamp of the last 
    commit.
    """
    try:
        branches_proc = Popen('git branch --list RELEASE*',
                shell=True, stdout=PIPE)
        branches = branches_proc.communicate()[0].split('\n')
        base = sorted(filter(EMPTY_STRING, map(STRING_STRIPPER, branches)))[-1]
        release_date = re.match('^.*RELEASE-(.*)', base).group(1)
        split_date = [value[-1] if value[0] == '0' else value for value in
                release_date.split('-')]
        current_release_date = datetime.date(*map(int, split_date))
        next_release_date = current_release_date + datetime.timedelta(days=14)
        version = format_version(next_release_date.strftime('%Y-%m-%d'))
    except IndexError:
        version = '0.0.1'
    log_message = Popen('git log -1 --date=raw', stdout=PIPE,
            shell=True).communicate()[0]
    snapshot = re.search(r""".*\n.*\nDate:.*?(\d+) .*\n.*""",
            log_message).group(1)
    return "{0}-dev.{1}".format(version, snapshot)

def get_beta_version(release_name, date_string):
    """
    Construct the version for a beta (staging) release.  The format is 
    Y.[m]m.[d]d-beta.[count] where the date portion is constructed from
    the branch name and the count is the number of commits since the
    release branch was originally cut.
    """
    git_log_cmd = 'git log {0}{1} --not integration --oneline'
    git_log_cmd = git_log_cmd.format(release_name, date_string)
    log_proc = Popen(git_log_cmd, stdout=PIPE, shell=True)
    commit_counter = Popen('wc -l', stdin=log_proc.stdout, 
            stdout=PIPE, shell=True)
    log_proc.stdout.close()
    beta_version = "-{0}".format(commit_counter.communicate()[0].strip())
    if beta_version == '-0':
        beta_version = ''
    return "{0}-beta.{1}".format(format_version(date_string), beta_version)

def fetch():
    """
    Update git repo to latest from origin.
    """
    call('git fetch', shell=True)


def get_version(integration='integration', production='production'):
    """
    Construct the version for a project based on the current git status.
    This assumes that the branch names follow a convention where there is
    a single integration branch, a single production branch and release
    branches are prefixed with 'RELEASE'.  In addition this relies on
    tags marked SIGNOFF to calculate production versions.  The specific
    names for the integration and production branches can be specified as
    arguments to this function.
    """
    branch_cmd = Popen('git branch', stdout=PIPE, shell=True)
    current_branch_proc = Popen('grep -e ^*', stdin=branch_cmd.stdout, 
            stdout=PIPE, shell=True)
    branch_cmd.stdout.close()
    branch_name = current_branch_proc.communicate()[0]
    feature_branch = re.match('^.*JIRA-(\w+)-(.*)', branch_name)
    if feature_branch is not None:
        return "{0}.{1}".format(feature_branch.group(2),
                feature_branch.group(1))

    if re.match('^.*{0}$'.format(integration), branch_name) is not None:
        return get_integration_version()

    release_branch = re.match('^.*(RELEASE-)(.*)', branch_name)
    if release_branch is not None:
        return get_beta_version(release_branch.group(1), 
                release_branch.group(2))

    if re.match('.*{0}$'.format(production), branch_name) is None:
        raise ValueError('What the hell branch are you on?')

    log_proc = Popen('git log --oneline -n 5', stdout=PIPE, shell=True)
    output = log_proc.communicate()[0]
    for i in output.split('\n'):
        release_signoff = re.match("^.*RELEASE-(.*)-SIGNOFF-.*$", i)
        if release_signoff is None:
            continue
        return format_version(release_signoff.group(1))

def main():
    """
    Entry point for the CLI
    """
    from clint.textui import colored

    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('-p', action='store', dest='production',
            default='production', 
            help='The name of the production branch, e.g., master')
    parser.add_argument('-i', action='store', dest='integration',
            default='integration',
            help='The name of the integration branch')
    parser.add_argument('-F', action='store_false', dest='fetch', default=True,
            help="Don't first execute 'git fetch' (defaults to False)")
    args = parser.parse_args()
    if args.fetch:
        print colored.green('Fetching latest changes from origin')
        fetch()
    version = get_version(integration=args.integration,
            production=args.production)
    print "{0} {1}".format(colored.blue("Current version is:"), version.strip())


if __name__ == '__main__':
    main()
