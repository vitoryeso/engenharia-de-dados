## Comandos utilizados
```bash
docker build -f Dockerfile.client -t vitoryeso/clientetcp:v1 .
docker build -f Dockerfile.server -t vitoryeso/servidortcp:v1 .

docker run -it -t vitoryeso/servidortcp:v1
docker run -it -t vitoryeso/clientetcp:v1 172.17.0.2

docker login
docker push vitoryeso/servidortcp:v1
docker push vitoryeso/clientetcp:v1
```

