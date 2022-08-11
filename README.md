# Puffer Python
## Prerequisites

* Python 3.7
* MySQL 8.0
* Docker (optional)

## Getting Started

### Install Python and Libraries

Make sure that Python 3.7 is accessible via `python`.

```bash
# create virtual environment
python -m venv venv

# activate virtual environment
source venv/bin/activate

# upgrade pip
pip install --upgrade pip

# install libraries
pip install -r requirements.txt
```

### Run MySQL using Docker (optional)

* Run without persistent data

```bash
docker run \
    -e MYSQL_DATABASE=database \
    -e MYSQL_ROOT_PASSWORD=secret \
    -p 3306:3306 \
    mysql:8.0 \
;
```

* Run with persistent data

```bash
docker run \
    -e MYSQL_DATABASE=database \
    -e MYSQL_ROOT_PASSWORD=secret \
    -p 3306:3306 \
    -v $(pwd)/data:/var/lib/mysql
    mysql:8.0 \
;
```

### Do Database Migrations

```bash
flask db upgrade
```

### Copy Environment File

```bash
cp .env.test .env
```

### Run

```bash
flask run
```

Check http://127.0.0.1:5000/swagger

## Lint

### Lint Local Files

See errors/warnings before 

```bash
git --no-pager diff --name-only origin/master... \
    | grep .py \
    | xargs pylint --errors-only \
;
```

### Ignore

* Add an ignore comment to the command

```python
a = b  # pylint:disable=...
```
* Add an ignore comment to the top of a file

```python
# pylint:disable=...

from flask import Flask
...
```

* Add an ignore comment to `pylintrc`

```bash
# ...
# --enable=similarities". If you want to run only the classes checker, but have
# no Warning level messages displayed, use "--disable=all --enable=classes
# --disable=W".
disable=print-statement,
        parameter-unpacking,
        unpacking-in-except,
        old-raise-syntax,
        # ...
        # new code
```

## Test

* Test everything

```bash
pytest \
    --disable-warnings \
;
```

* Test and stop at the first error

```bash
pytest \
    --disable-warnings \
    --exitfirst \
;
```

* Test failed cases

```bash
pytest \
    --disable-warnings \
    --last-failed \
;
```
