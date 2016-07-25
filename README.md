# app-deployment-lib
This Python package contains a set of helper functions which can be used to automate deployment of custom applications in Cloud Foundry.

## Features
* Wrapper for Cloud Foundry Command Line Interface: login and target CF API, create service instances, create user provided service instances, push/restage/restart applications, bind applications with services, create service brokers, create organizations and spaces, run custom CF CLI commands and more!
* Upload files to HDFS
* Deploy app to Gearpump
* Create artifact packages of applications using Maven

## Prerequisites
* Some of the helper functions require running Trusted Analytics Platform applications eg. upload of files to HDFS requires running [Uploader](https://github.com/trustedanalytics/uploader) application.
* [CF CLI](https://github.com/cloudfoundry/cli)
* [Maven](https://maven.apache.org/download.cgi)

## Installation
To import the package in your script it is recommended to use [tox](https://pypi.python.org/pypi/tox). Check out [basic tox example](https://testrun.org/tox/latest/#basic-example) or "Example projects" section to learn more!

To use a specific version of `app-deployment-lib` identified by `commit_ID` add the following line to `requirements.txt` file in your project (replace `<commit_ID>` with a commit ID that points to a version you want to use):
```
-e git+git@github.com:trustedanalytics/app-deployment-lib.git@<commit_ID>#egg=app_deployment_lib
```
If you want to use latest version from master branch add the following line:
```
-e git+git@github.com:trustedanalytics/app-deployment-lib.git@master#egg=app_deployment_lib
```
For more details on using PIP and requirements files, check out [the documentation](https://pip.readthedocs.io/en/1.1/requirements.html).


## Example usage

```python
from app_deployment_lib import cf_cli
from app_deployment_lib import cf_helpers

PROJECT_DIR = cf_helpers.get_project_dir()

cf_cli.login(CF_INFO)
cf_cli.create_service('influxdb088', 'free', 'my-influx')
cf_helpers.prepare_package(work_dir=PROJECT_DIR)
cf_helpers.push(work_dir=PROJECT_DIR, options='my-application-name')
```

## Example projects
The following projects support automated deployment which is implemented with usage of python-app-deployment-helpers!
* [Space Shuttle Demo](https://github.com/trustedanalytics/space-shuttle-demo)
* [Dataset Reader Sample](https://github.com/trustedanalytics/dataset-reader-sample)
