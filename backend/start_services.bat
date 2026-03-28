@echo off
set JAVA_HOME=C:\Users\CC\.jdks\corretto-19.0.2
set PATH=%JAVA_HOME%\bin;%PATH%
cd /d D:\code\market\backend

start "" mvn spring-boot:run -pl gateway-service -Dspring-boot.run.jvmArguments="-Dserver.port=8080"
timeout /t 10 /nobreak > NUL

start "" mvn spring-boot:run -pl user-service -Dspring-boot.run.jvmArguments="-Dserver.port=8081"
start "" mvn spring-boot:run -pl product-service -Dspring-boot.run.jvmArguments="-Dserver.port=8082"
start "" mvn spring-boot:run -pl order-service -Dspring-boot.run.jvmArguments="-Dserver.port=8083"
start "" mvn spring-boot:run -pl recommendation-service -Dspring-boot.run.jvmArguments="-Dserver.port=8084"
start "" mvn spring-boot:run -pl search-service -Dspring-boot.run.jvmArguments="-Dserver.port=8085"
start "" mvn spring-boot:run -pl payment-service -Dspring-boot.run.jvmArguments="-Dserver.port=8086"