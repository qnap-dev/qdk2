#!/usr/bin/env python

from os.path import (join as pjoin,
                     exists as pexists
                     )
from settings import Settings
from exception import ControlFileSyntaxError, ChangelogFileSyntaxError
from textwrap import TextWrapper
from time import gmtime, strftime
import re
# from log import info


class File(object):
    def lint(self):
        self.parse()

    def parse():
        pass


class ControlFile(File):
    def __init__(self, qpkg_dir='.'):
        self._filename = pjoin(qpkg_dir, Settings.CONTROL_PATH, 'control')
        self._parsed = False
        self._packages = {}
        self._source = None

    def new_package(self, section):
        if len(section) == 0:
            return
        if 'source' in section:
            if self._source is not None:
                raise ControlFileSyntaxError('source section > 1')
            self._source = section.copy()
        elif 'package' in section:
            package_name = section['package'] + '_' + section['architecture']
            if package_name in self._packages:
                raise ControlFileSyntaxError('duplicate package name ' +
                                             package_name)
            self._packages[package_name] = section.copy()
        else:
            raise ControlFileSyntaxError(
                'Package and source section not found')

    def parse(self):
        if self._parsed:
            return
        self._parsed = True
        with open(self._filename, 'r') as fp:
            k, v = '', ''
            linenum = 0
            section = {}
            for line in fp:
                linenum += 1
                # new package
                if len(line.strip()) == 0:
                    self.new_package(section)
                    k, v = '', ''
                    section.clear()
                    continue
                # comment
                if line.startswith('#'):
                    continue
                # continue line
                if line.startswith(' '):
                    v += line.rstrip()
                    section[k] = v
                    continue
                # new field
                fields = line.split(':', 1)
                if len(fields) == 2:
                    v = fields[1].strip()
                k = fields[0].lower()
                section[k] = v
            self.new_package(section)

    @property
    def source(self):
        self.parse()
        return self._source

    @property
    def packages(self):
        self.parse()
        return self._packages

    @property
    def filename(self):
        return self._filename


class ChangelogFile(File):
    ''' Example: Note the space prefix and empty line
    foo (1.28.2)

      * merge from upstream (required at least one line)
      * ... (optional)

     -- Doro Wu <fcwut.tw@gmail.com>  Tue, 22 Apr 2014 15:14:54 +0800

    foo (1.28.1)
    '''
    TITLE_REOBJ = re.compile(r"""(\S+) \((\S+)\).*""")
    AUTHOR_REOBJ = re.compile(r""" -- (.*) <(.*)> (.*)""")

    def __init__(self, qpkg_dir='.'):
        self._filename = pjoin(qpkg_dir, Settings.CONTROL_PATH, 'changelog')
        self._parsed = False
        self._logs = []
        self._package_name = None
        self._lineno = 0

    def _new_log(self, line):
        reobj = self.__class__.TITLE_REOBJ.match(line)
        if reobj is None:
            raise ChangelogFileSyntaxError(
                self._filename, self._lineno,
                'This line must compose "package_name (version)')
        package_name = reobj.group(1)
        if self._package_name is not None and \
                self._package_name != package_name:
            raise ChangelogFileSyntaxError(
                self._filename, self._lineno,
                'package name mismatched')
        self._package_name = package_name
        version = reobj.group(2)
        return {'version': version}

    def _append_message(self, log, line):
        if 'message' not in log:
            log['message'] = []
        line = line.strip()
        if line[0] == '*':
            log['message'].append(line)
        else:
            if len(log['message']) <= 0:
                raise ChangelogFileSyntaxError(
                    self._filename, self._lineno,
                    'Message must with the format of "  * your message"')
            log['message'][-1] += ' ' + line
        return log

    def _append_author(self, log, line):
        try:
            reobj = self.__class__.AUTHOR_REOBJ.match(line)
            author, email, time = reobj.groups()
            log['author'] = author
            log['email'] = email
            log['time'] = time
        except (ValueError, ChangelogFileSyntaxError):
            raise ChangelogFileSyntaxError(
                self._filename, self._lineno,
                'Signaure must format as " -- author <email> time"')
        self._logs.append(log.copy())
        return log

    def parse(self):
        TITLE, MSG, AUTHOR = range(3)
        if self._parsed:
            return
        self._parsed = True
        if not pexists(self._filename):
            return
        try:
            fp = open(self._filename, 'r')
            block_type = TITLE
            log = {}
            for line in fp:
                self._lineno += 1
                line = line.rstrip()
                # empty line
                if len(line.strip()) == 0:
                    continue
                # message line
                if line.startswith('  '):
                    if block_type != MSG:
                        raise ChangelogFileSyntaxError(
                            self._filename, self._lineno,
                            'This line expects as log message. Message lines '
                            'must start with 2 spaces')
                    log = self._append_message(log, line)
                    continue
                # author
                if line.startswith(' '):
                    if block_type != MSG:
                        raise ChangelogFileSyntaxError(
                            self._filename, self._lineno,
                            'It must have any log message')
                    self._append_author(log, line)
                    block_type = TITLE
                    log.clear()
                    continue
                # new log
                if line[0] != ' ':
                    if block_type != TITLE:
                        raise ChangelogFileSyntaxError(
                            self._filename, self._lineno,
                            'This line must start with package name')
                    log = self._new_log(line)
                    block_type = MSG
                    continue
                raise ChangelogFileSyntaxError(
                    self._filename, self._lineno,
                    'This line must start with package name')
            if len(log) != 0:
                raise ChangelogFileSyntaxError(
                    self._filename, self._lineno,
                    'Unfinished block')
        except OSError:
            pass
        finally:
            fp.close()

    def format(self, **kargs):
        self.parse()
        if self._package_name is not None:
            kargs['package_name'] = self._package_name
        if 'version' not in kargs:
            if len(self.logs) > 0:
                version = self.logs[0]['version']
                reobj = re.match(r"""(.*)(\d+)$""", version)
                if reobj is None:
                    version += '~1'
                else:
                    version = reobj.group(1) + str(int(reobj.group(2)) + 1)
            else:
                version = '1.0'
            kargs['version'] = version
        title = '{package_name} ({version})'.format(**kargs)
        messages = '  * '
        wrapper = TextWrapper(width=80, initial_indent='  * ',
                              subsequent_indent='    ')
        if 'messages' in kargs:
            messages = []
            for message in kargs['messages']:
                messages.append(wrapper.fill(message))
            messages = '\n'.join(messages)
        kargs['time'] = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        tailer = ' -- {author} <{email}>  {time}'.format(**kargs)
        return title + '\n\n' + messages + '\n\n' + tailer + '\n\n'

    @property
    def logs(self):
        self.parse()
        return self._logs

    @property
    def package_name(self):
        self.parse()
        return self._package_name

    @property
    def version(self):
        self.parse()
        if len(self._logs) == 0:
            raise ChangelogFileSyntaxError(self._filename, self._lineno,
                    'Changlog can\'t be empty')
        return self._logs[0]['version']

    @property
    def filename(self):
        return self._filename


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
