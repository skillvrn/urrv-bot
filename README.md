# URRV-BOT

Automated notification system for the Rostov Training Center

## CI/CD variables

| Имя переменной | Назначение |
|--------------|-----------|
| `DISCORD_ANNOUNCEMENT_CHANNEL_ID` | ID Discord-канала для уведомлений |
| `DISCORD_ATO_NEWS_CHANNEL_ID` | ID Dicsord-канала для новостей |
| `DISCORD_TOKEN` | Discord token для доступа бота к серверу |
| `DISCORD_WELCOME_CHANNEL_ID` | ID Discord-канала приветствия  |
| `DISCORD_POSITION_ANNOUNCEMENT_CHANNEL_ID` | ID Discord-канала |
| `DOCKER_USERNAME` | Имя пользователя учетной записи в репозитории Dockerhub |
| `DOCKER_PASSWORD` | Пароль паользователя учетной записи в репозитории Dockerhub |
| `FLIGHT_ANNOUNCE_IMAGE_URL` | URL картинки анонсов |
| `PYTHON_VERSION` | Версия python (в Dockerfiles и в CI/CD) |
| `SSH_HOST` | Hostname сервера для подключения по SSH для деплоя |
| `SSH_PORT` | SSH-порт для подключения к серверу с приложением для деплоя |
| `SSH_USERNAME` | Имя SSH-пользователя на сервере с приложением для деплоя |
| `SSH_PRIVATE_KEY` | Приватный SSH-ключ пользователя для подключения к серверу с приложением для деплоя |
| `XR_SITE_URL` | URL xr ivao |

## Gitflow

* Склонировать репозиторий

```bash
git clone git@github.com:skillvrn/urrv-bot.git
```

* Перейти в рабочий каталог и создать ветку разработки

```bash
cd urrv-bot
git checkout -b dev
```

* Внести изменений в исходный код
* После окончания работ добавить информацию в `CHANGELOG.md` в формате:

```
# Changelog

## vX.Y.Z - YYYY/MM/DD
* Первое изменение
* Второе изменение
...

[Предыдущие изменения]
```

* Закомитить изменения

```bash
git commit -am "Название коммита на англ. языке"
```

* Запушить в основной git

```bash
git push -u origin dev
```

* Проверить в actions, что пайплайн выполняется без ошибок
* Создать Pull-request (PR) в репозитории
* Провести код-ревью изменений в PR
* Получить апрув в PR
* Смержить в изменения из dev в main
* Проверить в actions, что пайплайн выполняется без ошибок
* Создать новый релиз с тегом, формат версионирования по semver. Пример: v1.3.2
* Проверить, что прошел деплой на прод
