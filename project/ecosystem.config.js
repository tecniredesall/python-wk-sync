module.exports = {
  apps : [
   {
      name: "fastapi",
      cwd: ".",
      script: "/usr/bin/python3",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --reload --debug",
      watch: false,
      interpreter: "",
      max_memory_restart: "1G",
    },
    {
      
      name: "worker",
      cwd: "",
      script: "/usr/bin/python3",
      args: "-m celery worker --app=worker.main.celery --loglevel=info --logfile=logs/celery-worker.log -Q 'celery,pending_actions,trummodity_services,federation_services' --pool=gevent --concurrency=100",
      watch: false,
      interpreter: "",
      max_memory_restart: "1G"
    },
    {
      name: "beat",
      cwd: ".",
      script: "/usr/bin/python3",
      args:
        "-m celery beat --app=worker.main.celery --loglevel=info --logfile=logs/celery-beat.log",
      watch: false,
      interpreter: "",
      max_memory_restart: "1G"
    },
    {
      name: "flower",
      cwd: ".",
      script: "/usr/bin/python3",
      args:
      "-m celery flower --app=worker.main.celery --port=5555 --broker=amqp://dev:dev@127.0.0.1:5672",
      watch: false,
      interpreter: "",
      max_memory_restart: "1G"
    },
    {
      name: "ConsumerRabbitGlobal",
      cwd: ".",
      script: "/usr/bin/python3",
      args: "/var/www/worker-sync/project/consumer.py",
      out_file: "/var/www/worker-sync/project/logs/consumer.log",
      error_file: "/var/www/worker-sync/project/logs/consumer_error.log",
      restart_delay:800,
      watch: false,
      interpreter: "",
      max_restarts: 10,
      max_memory_restart: "1G"
    }
  ]
};
