FROM openjdk:17-jdk-alpine

WORKDIR /app

# Only copy the JAR if it exists
COPY ./target/concore-0.0.1-SNAPSHOT.jar /app/concore.jar || true

# Ensure the JAR file is executable if present
RUN [ -f /app/concore.jar ] && chmod +x /app/concore.jar || true

EXPOSE 3000

# Run Java app only if the JAR exists, otherwise do nothing
CMD ["/bin/sh", "-c", "if [ -f /app/concore.jar ]; then java -jar /app/concore.jar; else echo 'No Java application found, exiting'; fi"]
