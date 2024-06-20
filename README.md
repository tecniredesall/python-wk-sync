# Project features
- [FastAPI](https://fastapi.tiangolo.com/)
- Python3+
- Docker
- celery4+

## Good practices

[Pepe 8](https://www.python.org/dev/peps/pep-0008/) Style Guide for Python Code

- Variables snake_case
- Functions lower_case
- Methods lower_case
- Constants UPPER_CASE
- Instances UPPER_CASE
- Class UpperCase

## Asynchronous Tasks with FastAPI and Celery

Example of how to handle background processes with FastAPI, Celery, and Docker.

## Want to learn how to build this?

Check out the [post](https://testdriven.io/blog/fastapi-and-celery/).

## Docker
For the project you only need to install docker.
   - [Install docker](https://docs.docker.com/get-docker/)
   - [Install docker-compose](https://docs.docker.com/compose/install/)

## Want to use this project?
Spin up the containers:

```sh
docker-compose up -d --build
```

Open your browser to [http://localhost:8004/docs](http://localhost:8004/docs) to view the app or to [http://localhost:5556](http://localhost:5556) to view the Flower dashboard.

Trigger a new task:

```sh
curl http://localhost:8004/tasks -H "Content-Type: application/json" --data '{"type": 0}'
```

Check the status:

```sh
curl http://localhost:8004/tasks/<TASK_ID>
```

## How to run the tests?
### Run tests with the project running in docker
Run all test
```sh
docker-compose exec web python -m pytest -k .
```
Run a specific method
```sh
docker-compose exec web python -m pytest -k "test_task and not test_home”
```

### Run tests with the project running without docker
Run all test
```sh
pytest -v tests
```
Run a specific module
```sh
pytest tests/test_federation.py
```

Run a specific method
```sh
pytest -v tests/test_federation.py::test_get_updates_federation
```
