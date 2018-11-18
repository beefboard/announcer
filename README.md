# Announcer

Beefboard's notification service

## About

Written in Python, announcer aims to provide a HA notification broadcaster for Beefboard
by ensuring that state is never lost.

By polling the various Beefboard APIs announcer should always broadcast
any pending notifications even if the service was unavailable when
the event was created.

## Features

Currently announcer notifies any admins of beefboard via email any any
posts waiting for approval.

## Development

`python3.7.0` is used for development of announcer.

`pipenv` is used for dependency management, with `mypy` used for
static type checking.

`pipenv install --dev` will install all dependencies for development

### Testing

`pipenv run test` is used to run tests.

TDD has been used to develop announcer, so 100% coverage of testable code
has been completed.
