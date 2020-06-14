# ThreadBack

The threadback backend is a graphql api.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

## Cloning the Repository

If you haven't already, you will need to clone the `kwilson21/threadback` GitHub repository to your local machine. This can be accomplished by running the following:

```bash
$ git clone git@github.com:kwilson21/threadback.git
```

If you encounter an error at this point, it is likely you have not configured an SSH key with GitHub, to resolve this issue, see [Generating a new SSH key and adding it to the ssh-agent](https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/) for more details

## Setting Up Your Environment

Getting started with threadback, you will need to install Python version 3.8 or above.

You can get the latest version of Python for Windows/Mac here: https://www.python.org/downloads/

Then install poetry

Mac OS X/Linux

```bash
$ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
```

Windows (Using Powershell)

```powershell
$ (Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python
```


## Configuring Environment Variables

To configure your environment variables for this app, create a file called `.env` in the project root directory and set the following variables accordingly

```bash
DEBUG=true
HOST=localhost
PORT=8000
DB_NAME=threadback
MONGODB_URI=
REDIS_URL=
```

## Install Required Packages

If you are using pipenv and are on a dev environment

```bash
$ cd ~/threadback
$ poetry install --dev
```

On a production environment

```bash
$ cd ~/QFEFE-Backend
$ poetry install
```

### Pre commit

We have a configuration for
[pre-commit](https://github.com/pre-commit/pre-commit), to add the hook run the
following command:

```bash
pre-commit install
```

### Installing MySQL

To install MongoDB on Windows, simply follow this links: [MongoDB Community Server Installation](https://www.mongodb.com/try/download/community)

Then install [Robo3T](https://robomongo.org/download)

Then click File -> Connect

In the MongoDB Connections window, click Create. Give the connection a Name and click Save.

### Installing Redis

If you are on Windows, follow these instructions to get WSL set up on your Windows machine: [Windows Subsystem for Linux Installation Guide for Windows 10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

Once you have Ubuntu installed on your Windows machine, open a bash terminal

```bash
$ sudo apt install redis-server
```

Then start the redis-server

```bash
$ sudo service redis-server start
```

## Running the App

Once your environment is set up, you are now ready to run the app and start developing.

To run the app

```bash
$ poetry run app
```
