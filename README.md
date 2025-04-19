# URRV-BOT

Automated notification system for the Rostov Training Center

## CI/CD variables

| Имя переменной | Назначение |
|--------------|-----------|
| `DISCORD_ANNOUNCEMENT_CHANNEL_ID` | ID Discord-канала для уведомлений |
| `DISCORD_ATO_NEWS_CHANNEL_ID` | ID Dicsord-канала для новостей |
| `DISCORD_TOKEN` | Discord token для доступа бота к серверу |
| `DISCORD_WELCOME_CHANNEL_ID` | ID Discord-канала приветствия  |
| `DOCKER_USERNAME` | Имя пользователя учетной записи в репозитории Dockerhub |
| `DOCKER_PASSWORD` | Пароль паользователя учетной записи в репозитории Dockerhub |
| `SSH_HOST` | Hostname сервера для подключения по SSH для деплоя |
| `SSH_PORT` | SSH-порт для подключения к серверу с приложением для деплоя |
| `SSH_USERNAME` | Имя SSH-пользователя на сервере с приложением для деплоя |
| `SSH_PRIVATE_KEY` | Приватный SSH-ключ пользователя для подключения к серверу с приложением для деплоя |

## Gitflow

* Работу вести в фича-ветках
* После окончания работ добавить информацию в `CHANGELOG.md`
* Запушить в основной git
* Создать Pull-request
* Смержить в ветку main
* Создать новый релиз с тегом, формат версионирования по semver. Пример: v1.3.2
