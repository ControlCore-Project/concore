#build stage
FROM eclipse-temurin:17-jdk-alpine AS builder
WORKDIR /build
RUN apk add --no-cache wget
RUN wget -q "https://search.maven.org/remotecontent?filepath=org/zeromq/jeromq/0.6.0/jeromq-0.6.0.jar" -O /opt/jeromq.jar
COPY *.java .
RUN javac -cp /opt/jeromq.jar *.java

#runtime stage
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app
COPY --from=builder /build/*.class /app/
COPY --from=builder /opt/jeromq.jar /app/jeromq.jar
