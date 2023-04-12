## Local Development

```
git clone https://github.com/gnaguerrer/server-hydroponic
cd server-hydroponic
git checkout feature/predictions
docker compose -f "docker-compose.yml" up -d --build
```

Then, visit localhost:3000 for Grafana, localhost:8086 for InfluxDB and localhost:15672 for RabbitMQ.

To enabled SMS add a `setup.env` file into `/analytics` with your Twilio credentials

```
account_sid=<your account sid>
auth_token=<your token>
```
