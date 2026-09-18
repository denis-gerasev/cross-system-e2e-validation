#!/usr/bin/env bash

cd react-shopping-cart
# Выходим сразу, если какая-то команда завершится ошибкой (кроме самого теста)
set -e

PORT=3000 # Укажите порт, на котором запускается ваш npm-сайт

# Функция очистки: убивает фоновый процесс Node.js при любом завершении скрипта
cleanup() {
  if [ -n "$NPM_PID" ]; then
    echo "Остановка npm-сервера (PID: $NPM_PID)..."
    kill "$NPM_PID" 2>/dev/null || true
    wait "$NPM_PID" 2>/dev/null || true
  fi
}

# Регистрируем ловушку: функция cleanup выполнится при выходе (EXIT),
# прерывании (INT/Ctrl+C) или завершении (TERM) скрипта
trap cleanup EXIT INT TERM

echo "Запуск npm сайта..."
# Запускаем в фоне (&) и перенаправляем вывод, чтобы логи сервера не мешали тестам

npm start > npm_server.log 2>&1 &
NPM_PID=$!

echo "Ожидание запуска сервера на порту $PORT..."
# Цикл проверяет доступность порта (требуется утилита nc или curl)
while ! nc -z localhost $PORT >/dev/null 2>&1; do
  sleep 1
done

echo "Сервер готов. Запуск pytest..."
cd ../
# Отключаем 'set -e', чтобы скрипт не упал до вызова cleanup, если тесты провалятся
set +e
pytest
TEST_EXIT_CODE=$?

# Возвращаем код ответа pytest, чтобы CI/CD понимал, прошли тесты или нет
exit $TEST_EXIT_CODE
