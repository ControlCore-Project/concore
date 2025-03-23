# Install Docker:-

Open Terminal and run the following commands:-

```
$ sudo apt-get update
$ sudo apt-get install curl
$ curl -fsSL https://get.docker.com/ | sh
```

Optional command:- To run docker commands without sudo

```
$ sudo usermod -aG docker <system_username>
```

The above command adds the system username to the docker group. Restart the system to complete the process.

After restart, run

```
$ sudo service docker start
```

# Building FRI Container

Now, we elaborate on building FRI as a container, together with the Kong API Gateway.

Connect to the Server VM, assuming x.x.x.x to be the IP address of your server.

```
$ ssh -i "controlcore.pem" ubuntu@x.x.x.x
```

Perform Git clone if this is the first time you are configuring the Server

```
$ git clone git@github.com/ControlCore-Project/concore.git
```

First build & run the Docker Container of the FRI.

```
$ git pull

$ cd fri

$ docker build -t fri .

$ docker run -d --name fri -p 8090:8080 fri
```

# Running Control-Core FRI with Kong as containers

If you are already running FRI, make sure to stop and clear existing FRI containers as they will likely conflict with the port. If there is a Kong gateway running in default ports, stop and clear it too.

```
$ docker stop fri
$ docker rm fri
$ docker stop kong
$ docker rm kong
$ docker stop kong-database
$ docker rm kong-database
```

Start and configure PostgreSQL container for Kong API.

```
$ docker run -d --name kong-database \
                -p 5432:5432 \
                -e POSTGRES_USER=kong \
                -e POSTGRES_DB=kong \
                -e POSTGRES_PASSWORD=kong \
                postgres:13
```

Run the Kong migrations for PostgreSQL.

```
$ docker run --rm \
    --link kong-database:kong-database \
    -e "KONG_DATABASE=postgres" \
    -e "KONG_PG_HOST=kong-database" \
    -e "KONG_PG_USER=kong" \
    -e "KONG_PG_PASSWORD=kong" \
    kong/kong-gateway:latest kong migrations bootstrap
```

Start Kong

```
$ docker run -d --name kong \
    --link kong-database:kong-database \
    -e "KONG_DATABASE=postgres" \
    -e "KONG_PG_HOST=kong-database" \
    -e "KONG_PG_USER=kong" \
    -e "KONG_PG_PASSWORD=kong" \
    -e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
    -e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
    -e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
    -e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
    -e "KONG_ADMIN_LISTEN=0.0.0.0:8001, 0.0.0.0:8444 ssl" \
    -p 80:8000 \
    -p 8443:8443 \
    -p 8001:8001 \
    -p 8444:8444 \
    kong/kong-gateway:latest
```

Start FRI container

```
$ nohup sudo docker run --name fri -p 8090:8080 fri > controlcore.out &
```

Define Kong Service and Route.

First, configure a Kong service, replacing the variable "private-ip" with the private IP address of your server below.

```
$ curl -i -X POST --url http://localhost:8001/services/ --data 'name=fri' --data 'url=http://private-ip:8090'
```

Then configure a route to the service

```
$ curl -i -X POST --url http://localhost:8001/services/fri/routes --data 'paths=/'
```

Now, controlcore.org is routed through the Kong APIs.

# Troubleshooting the FRI

Connect to the Server VM

```
$ ssh -i "controlcore.pem" ubuntu@x.x.x.x
```

Check the Server logs.

```
$ tail -f controlcore.out
```

or

```
$ docker logs fri -f
```

Find the FRI docker container

```
$ docker ps
```

CONTAINER ID        IMAGE               COMMAND              CREATED             STATUS              PORTS                NAMES dfdd3b3d3308        fri            "python main.py"   38 minutes ago      Up 38 minutes       0.0.0.0:80->80/tcp   fri

Access the container

```
$ docker exec -it dfdd /bin/bash
```

