#!/usr/bin/env python

import argparse
import enum
import json
import os
import re
import sys
import typing

import github
import yaml
from colorama import Fore, colorama_text

__all__ = [
    "Status", "Result", "get_workflow_result", "get_all_workflow_results",
    "results_from_result_list", "report_results_summary",
    "attempt_to_reactivate", "output_link_to_inactive",
    "output_link_to_error", "get_token", "make_parser", "main"
]

from .version import short_version

class Status(enum.Enum):
    OK = Fore.GREEN
    INACTIVATED = Fore.YELLOW
    FAILED = Fore.RED


class Result(typing.NamedTuple):
    repo: str
    workflow_name: str
    status: Status
    workflow: github.Workflow.Workflow
    last_scheduled_run: github.WorkflowRun.WorkflowRun

    @property
    def output_url(self):
        if self.status is not Status.INACTIVATED:
            return self.last_scheduled_run.html_url

        html_url = self.workflow.html_url
        repo = self.repo
        start = f"https://github.com/{repo}/blob"
        end = self.workflow.path
        if not (html_url.startswith(start) and html_url.endswith(end)):
            url = ("Unable to get actions URL for action at:\n  "
                   + html_url)
        else:
            file = end.split('/')[-1]
            url = f"https://github.com/{repo}/actions/workflows/{file}"

        return url

    def output_line(self):
        text = {Status.OK: "OK", Status.INACTIVATED: "INACTIVE",
                Status.FAILED: "FAIL"}[self.status]
        stylized =f"{self.status.value}{text}{Fore.RESET}"
        return f"{self.repo}: {self.workflow_name}: {stylized}"


def get_workflow_result(repo, workflow_name):
    workflow = repo.get_workflow(workflow_name)
    if workflow.state != "active":
        status = Status.INACTIVATED
        last_scheduled_run = None
    else:
        last_scheduled_run = next(iter(workflow.get_runs(event='schedule')))
        if last_scheduled_run.conclusion != "success":
            status = Status.FAILED
        else:
            status = Status.OK

    return Result(
        repo=repo.full_name,
        workflow_name=workflow_name,
        status=status,
        workflow=workflow,
        last_scheduled_run=last_scheduled_run
    )

def get_all_workflow_results(gh, workflow_dict):
    for repo_name, workflow_list in workflow_dict.items():
        repo = gh.get_repo(repo_name)
        for workflow_name in workflow_list:
            result = get_workflow_result(repo, workflow_name)
            yield result

def results_from_result_list(result_list):
    results = {Status.OK: [], Status.INACTIVATED: [], Status.FAILED: []}
    for result in result_list:
        results[result.status].append(result)
    return results


def report_results_summary(results):
    total = sum(len(ll) for ll in results.values())
    print(f"\nChecked {total} workflows. "
          f"{Status.OK.value}{len(results[Status.OK])} passing. {Fore.RESET}"
          f"{Status.INACTIVATED.value}{len(results[Status.INACTIVATED])} "
          f"inactive.{Fore.RESET} "
          f"{Status.FAILED.value}{len(results[Status.FAILED])} "
          f"failing.{Fore.RESET}")

def attempt_to_reactivate(result):
    ...

def output_link_to_inactive(inactives):
    # unfortuately, we kind of have to guess here; the URL we want isn't
    # included in API information
    print("\nLINKS TO INACTIVE WORKFLOWS")
    for result in inactives:
        print(f"* {result.repo}:{result.workflow_name} page:\n"
              f"{result.output_url}")

def output_link_to_error(failed):
    print("\nLINKS TO FAILED RUNS")
    for result in failed:
        print(f"* {result.repo}:{result.workflow_name} failure: "
              f"\n  {result.output_url}")

def get_token(arg_token, workflow_dict):
    # order of precedence (first listed trumps anything below)
    # 1. CLI argument
    # 2. yaml config
    # 3. env var GITHUB_TOKEN
    token = None
    if 'token' in workflow_dict:
        token = workflow_dict.pop('token')
    if arg_token:
        token = arg_token
    if not token:
        token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("Missing 'token' parameter")
    return token

def make_parser():
    parser = argparse.ArgumentParser(
        prog="eshgham",
        description=(
            "ESHGHAM: The Executive Summarizer of Health for GitHub "
            "Actions Monitoring. "
            "A dashboard for your neglected GitHub Actions "
            f"workflows. Version {short_version}.")
    )
    parser.add_argument(
        'workflows_yaml', type=str,
        help=(
            "Workflows in YAML format. This is provided with repository "
            "'owner/repo_name' as a string key, and workflow filename as "
            "the value. The special key 'token' may be used for the "
            "GitHub personal access token."
        )
    )
    parser.add_argument(
        '--token', type=str,
        help=(
            "GitHub personal access token. May also be provided using "
            "'token' as a key in the workflow YAML file, or in the "
            "environment variable `GITHUB_TOKEN`. The command argument "
            "takes precedence, followed by the YAML specification."
        )
    )
    parser.add_argument(
        '--json', action="store_const", dest="runtype", const="json",
        default="color"
    )
    return parser

def output_color(result_iterator):
    result_list = []
    for result in result_iterator:
        result_list.append(result)
        with colorama_text():
            print(result.output_line())

    results = results_from_result_list(result_list)
    report_results_summary(results)

    if inactives := results[Status.INACTIVATED]:
        output_link_to_inactive(inactives)
        ... # TODO: attempt to reactivate

    if failures := results[Status.FAILED]:
        output_link_to_error(failures)

    if failures or inactive:
        return 1

    return 0


def output_json(result_iterator):
    results = results_from_result_list(list(result_iterator))
    def workflow_info(workflow):
        return {
            'repo': workflow.repo,
            'workflow_name': workflow.workflow_name,
            'url': workflow.output_url,
        }

    json_ready = {
        status.name: [workflow_info(w) for w in workflows]
        for status, workflows in results.items()
    }

    print(json.dumps(json_ready))




def main():
    parser = make_parser()
    args = parser.parse_args()
    with open(args.workflows_yaml) as file:
        workflow_dict = yaml.load(file, Loader=yaml.FullLoader)

    token = get_token(args.token, workflow_dict)
    gh = github.Github(token)

    output = {
        'json': output_json,
        'color': output_color,
    }[args.runtype]

    retval = output(get_all_workflow_results(gh, workflow_dict)) or 0
    exit(retval)


if __name__ == "__main__":
    main()
