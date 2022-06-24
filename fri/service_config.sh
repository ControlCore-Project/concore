#!/bin/bash

SERVICES=('upload' 'execute')
for service in "${SERVICES[@]}"
do
	name="name="$service
	path="paths=/"$service
	service_path="url=http://private-ip:8090/"$service
	route_path="http://localhost:8001/services/"$service"/routes"
	plugin_path="http://localhost:8001/services/"$service"/plugins"
	echo "Name is, $name"
	echo "Path is, $path"
	echo "Service path is, $service_path"
	echo "Route path is, $route_path"
	echo "Plugin path is, $plugin_path"
	echo "Creating Service, $service..."
	curl -i -X POST --url http://localhost:8001/services/ --data $name --data $service_path
	echo "Creating route for $service..."
	curl -i -X POST --url $route_path --data $path
	echo "Creating apikey-based authentication for $service..."
	curl -X POST $plugin_path --data "name=key-auth" --data "config.key_names=apikey"
done