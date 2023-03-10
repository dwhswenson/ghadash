# ghadash

*A dashboard to check on the status of your neglected GitHub Actions
Workflows.*

Do you have a lot of GitHub repositories? Things you where you like to keep the
projects alive, even if they aren't very active?

Do you worry that you'll miss one of the warning emails GitHub sends you when a
scheduled workflow becomes inactive? Have you missed them before, only
discovering that CI hadn't been running for months after a user complained
about incompatibility with a new release of a dependency?

**Then ghadash is for you!**

ghadash is a little command line utility to check on your scheduled workflows.

Here's what it looks like in practice:

![The command ghadash config.yaml tells if your GitHub actions are inactive or
failing](ghadash.gif)

## Installation

Coming soon to a Python Package Index near you!

<!-- 
python -m pip install ghadash
-->

## Usage

```text
usage: ghadash [-h] [--token TOKEN] workflows_yaml

A dashboard for your neglected GitHub Actions workflows. Version 0.0.1.dev0.

positional arguments:
  workflows_yaml  Workflows in YAML format. This is provided with repository
                  'owner/repo_name' as a string key, and workflow filename as
                  the value. The special key 'token' may be used for the
                  GitHub personal access token.

options:
  -h, --help      show this help message and exit
  --token TOKEN   GitHub personal access token. May also be provided using
                  'token' as a key in the workflow YAML file, or in the
                  environment variable `GITHUB_TOKEN`. The command argument
                  takes precedence, followed by the YAML specification.
```

## YAML config

The YAML config is a mapping of repository names to lists of workflow YAML file
names. It also allows (optionally) the key `token`, which would have the value
of your GitHub personal access token.

Here's my config file, for illustration (obviously, my GitHub token is removed).

```yaml
openpathsampling/openpathsampling:
  - tests.yml
  - check-openmm-rc.yml
openpathsampling/openpathsampling-cli:
  - test-suite.yml
openpathsampling/ops_tutorial:
  - ci.yml
openpathsampling/ops_additional_examples:
  - tests.yml
dwhswenson/contact_map:
  - unit-tests.yml
dwhswenson/autorelease:
  - unit-tests.yml
dwhswenson/ops-storage-notebooks:
  - tests.yml
dwhswenson/conda-rc-check:
  - example_use.yml
dwhswenson/plugcli:
  - ci.yml
# I'm okay with these being inactive, but maybe I'll activate them again
# someday
#dwhswenson/ghcontribs:
  #- tests.yml
#dwhswenson/fabulous-paths:
  #- tests.yml
token: ghp_<blahblahblah>
```
