# The Control-Core FRI for Closed-Loop Neuromodulation Control Systems

The Control-Core File Receiving Interface (FRI) is built with is Python-3.10. It is the core component that makes the distributed executions a reality in the Control-Core framework.

# Install Dependencies

Install Jupyter lab
````
$ pip install jupyterlab
````

# Running the FRI and a quick test.

To run the FRI as a server:
````
$ cd conore

$ git checkout dev

$ cd server

$ python3 main.py
````

To test:
````
$ cd ..

$ python3 test.py
````

# Building FRI Container

Now, we elaborate on building FRI as a container, together with the Kong API Gateway.

Connect to the Server VM, assuming x.x.x.x to be the IP address of your server.
````
$ ssh -i "controlcore.pem" ubuntu@x.x.x.x
````
Perform Git clone if this is the first time you are configuring the Server
````
$ git clone git@github.com/ControlCore-Project/concore.git
````

First build the Docker Container of the FRI.
````
$ git pull

$ sudo docker build -t fri .
````

# Running Control-Core FRI with Kong as containers

If you are already running FRI, make sure to stop and clear existing FRI container as it is likely conflict with the port. If there is Kong gateway running in default ports, stop and clear it too.
````
$ docker stop fri
$ docker rm fri
$ docker stop kong
$ docker rm kong
````

Start and configure Cassandra container for Kong API.
````
$ docker run -d --name kong-database \
                -p 9042:9042 \
                cassandra:3


$ docker run --rm \
    --link kong-database:kong-database \
    -e "KONG_DATABASE=cassandra" \
    -e "KONG_PG_HOST=kong-database" \
    -e "KONG_PG_USER=kong" \
    -e "KONG_PG_PASSWORD=kong" \
    -e "KONG_CASSANDRA_CONTACT_POINTS=kong-database" \
    kong kong migrations bootstrap
````

Start Kong
````
$ docker run -d --name kong \
    --link kong-database:kong-database \
    -e "KONG_DATABASE=cassandra" \
    -e "KONG_PG_HOST=kong-database" \
    -e "KONG_PG_PASSWORD=kong" \
    -e "KONG_CASSANDRA_CONTACT_POINTS=kong-database" \
    -e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
    -e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
    -e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
    -e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
    -e "KONG_ADMIN_LISTEN=0.0.0.0:8001, 0.0.0.0:8444 ssl" \
    -p 80:8000 \
    -p 8443:8443 \
    -p 8001:8001 \
    -p 8444:8444 \
    kong
````

Start FRI container
````
$ nohup sudo docker run --name fri -p 8090:8081 fri > controlcore.out &
````

Delete if there is a previously configured Kong service. If not, skip this step. First you need to find the ID-VALUE for the route with a GET command before deleting the route and service.
````
$ curl -X GET "http://localhost:8001/services/fri/routes"
````
Use the ID output from above to issue the delete command as below (issue this only if you have a previous conflicting service definiton in kong. Otherwise, skip this step):
````
$ curl -X DELETE "http://localhost:8001/services/fri/routes/ID-VALUE"

$ curl -X DELETE "http://localhost:8001/services/fri/"
````

Define Kong Service and Route.

First Configure a Kong service, replacing the variable "private-ip" with the private IP address of your server below.
````
$ curl -i -X POST --url http://localhost:8001/services/ --data 'name=fri' --data 'url=http://private-ip:8090'
````
Then configure route to the service
````
$ curl -i -X POST --url http://localhost:8001/services/fri/routes --data 'paths=/'
````

Now, controlcore.org is routed through the Kong APIs.


# Troubleshooting the FRI

Connect to the Server VM
````
$ ssh -i "controlcore.pem" ubuntu@x.x.x.x
````
Check the Server logs.
````
$ tail -f controlcore.out
````
or
````
$ sudo docker logs fri -f
````
Find the FRI docker container
````
$ sudo docker ps
````
CONTAINER ID        IMAGE               COMMAND              CREATED             STATUS              PORTS                NAMES
dfdd3b3d3308        fri            "python main.py"   38 minutes ago      Up 38 minutes       0.0.0.0:80->80/tcp   fri

Access the container
````
$ sudo docker exec -it dfdd /bin/bash
````



# Citing the CONTROL-CORE FRI

If you use the CONTROL-CORE FRI in your research, please cite the below paper:

* Kathiravelu, P., Arnold, M., Fleischer, J., Yao, Y., Awasthi, S., Goel, A. K., Branen, A., Sarikhani, P., Kumar, G., Kothare, M. V., and Mahmoudi, B. **CONTROL-CORE: A Framework for Simulation and Design of Closed-Loop Peripheral Neuromodulation Control Systems**. In IEEE Access. March 2022. https://doi.org/10.1109/ACCESS.2022.3161471 
