#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

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
        subprocess.check_output(
            ['make', 'install'], env=environment, text=True,
        )

    subject_path = f'{os.getcwd()}/bin/autojump'
    subject_initializer_path = f'{os.getcwd()}/bin/autojump.sh'

    def autojump(*args):
        shcmd = ' '.join(
            [
                'source',
                shlex.quote(subject_initializer_path),
                ';',
                shlex.quote(subject_path),
                ' '.join(map(str, args)),
            ],
        )

        result = subprocess.run(
            shcmd,
            executable='/bin/bash',
            env=environment,
            capture_output=True,
            shell=True,
            text=True,
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
    run_lines = run_results.stdout.splitlines()

    assert run_lines == [
        f"foo__1__{join(tmpdir, 'foobarbar')}",
        f"foo__2__{join(tmpdir, 'foobar')}",
        f"foo__3__{join(tmpdir, 'foo')}",
    ]


def test_jc_jumps_to_child_match(tmpdir):
    tmpdir = Path(tmpdir)
    base = str(tmpdir)
    bash = shutil.which('bash')

    environment = os.environ
    environment['HOME'] = base
    environment['SHELL'] = bash

    def install_subject():
        subprocess.run(
            ['make', 'install'], check=True, env=environment, capture_output=True,
        )

    subject_path = f'{os.getcwd()}/bin/autojump'
    subject_initializer_path = f'{os.getcwd()}/bin/autojump.sh'

    def autojump(*args):
        shcmd = ' '.join(
            [
                'source',
                shlex.quote(subject_initializer_path),
                ';',
                shlex.quote(subject_path),
                ' '.join(map(str, args)),
            ],
        )

        result = subprocess.run(
            shcmd,
            executable='/bin/bash',
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

    def jc_and_pwd(working_directory, *args):
        shcmd = ' '.join(
            [
                'source',
                shlex.quote(subject_initializer_path),
                ';',
                'cd',
                shlex.quote(str(working_directory)),
                '&&'
                'jc',
                ' '.join(map(str, args)),
                '&&',
                'pwd',
            ],
        )

        bash = shutil.which('bash')
        if not bash:
            raise Exception('`bash` not found')

        result = subprocess.run(
            shcmd,
            executable=bash,
            env=environment,
            capture_output=True,
            shell=True,
            text=True,
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

    add_to_db(_create(tmpdir / 'foo'), weight_bump=1)
    add_to_db(_create(tmpdir / 'foo' / 'bar'), weight_bump=1)
    add_to_db(_create(tmpdir / 'foo' / 'baz'), weight_bump=1)
    add_to_db(_create(tmpdir / 'baz'))
    add_to_db(_create(tmpdir / 'baz' / 'bar'))
    add_to_db(_create(tmpdir / 'baz' / 'baz'))

    run_results = jc_and_pwd(tmpdir / 'baz', 'bar')
    run_lines = run_results.stdout.splitlines()

    # TODO: Make this a strict check once the duplication is fixed.
    assert set(run_lines) == set([
        str(tmpdir / 'baz' / 'bar'),
    ])
