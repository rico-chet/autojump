#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shlex
import shutil
import subprocess
import sys

sys.path.append(os.path.join(os.getcwd(), 'bin'))  # noqa


def _create(path):
    os.makedirs(path, exist_ok=True)
    return path


def test_autojump_returns_stable_results(tmpdir):
    base = str(tmpdir)
    join = os.path.join
    bash = shutil.which('bash')

    environment = os.environ
    environment['HOME'] = base
    environment['SHELL'] = bash

    def install_subject():
        subprocess.run(['make', 'install'], check=True, env=environment, capture_output=True)

    subject_path = f'{os.getcwd()}/bin/autojump'
    subject_initializer_path = f'{os.getcwd()}/bin/autojump.sh'

    def autojump(*args):
        shcmd = ' '.join([
            'source',
            shlex.quote(subject_initializer_path), ';',
            shlex.quote(subject_path), ' '.join(map(str, args)),
        ])

        result = subprocess.run(
            shcmd, executable='/bin/bash',
            env=environment,
            capture_output=True,
            shell=True,
        )
        if result.returncode == 0:
            return result
        else:
            print()
            print(f'stdout: {result.stdout}')
            print(f'stderr: {result.stderr}')
            result.check_returncode()

    def add_to_db(path, weight_bump=0):
        autojump('--add', path)
        if weight_bump > 0:
            try:
                oldpwd = os.getcwd()
                os.chdir(path)
                autojump('--increase', weight_bump)
            finally:
                os.chdir(oldpwd)

    install_subject()

    add_to_db(_create(join(tmpdir, 'foo')), weight_bump=1)
    add_to_db(_create(join(tmpdir, 'foobar')), weight_bump=2)
    add_to_db(_create(join(tmpdir, 'foobarbar')), weight_bump=3)

    run_results = autojump('--complete', 'foo')
    run_lines = run_results.stdout.decode('utf-8').splitlines()

    assert run_lines == [
        f"foo__1__{join(tmpdir, 'foobarbar')}",
        f"foo__2__{join(tmpdir, 'foobar')}",
        f"foo__3__{join(tmpdir, 'foo')}",
    ]
