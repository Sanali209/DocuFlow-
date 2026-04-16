Реализация двунаправленной связи через **одну общую папку** с использованием ID узлов — это классическая модель «Шины данных» (Data Bus) на файлах. Чтобы запросы не перемешивались и каждый знал, что адресовано ему, мы введем строгий нейминг.

### 🏗️ Структура именования файлов

Для исключения коллизий формат имени файла должен быть следующим:

`направление_откого_кому_id.json`

- **Направление:** `REQ` (запрос) или `RES` (ответ).

- **От кого / Кому:** ID узла (например, `LASER_1`, `COORDINATOR`).

- **ID транзакции:** UUID или таймстемп в конце имени для уникальности.


**Примеры:**
- `REQ_LASER1_COORD_1712012345.json` — Лазер 1 просит статус у Координатора.
- `RES_COORD_LASER1_1712012345.json` — Ответ Координатора.

---

### 🤝 Протокол рукопожатия (Handshake & Lifecycle)

Так как у нас одна папка, важно, чтобы узлы не «хватались» за чужие файлы.

#### 1. Инициация (Request)

1. **Узел (LASER_1)** создает файл во временном режиме: `TEMP_REQ_LASER1_COORD_1712012345.json`.

2. Записывает туда тело запроса.

3. **Переименовывает** его в `REQ_LASER1_COORD_1712012345.json`. Это сигнал Координатору: «Файл готов, читай».


#### 2. Обработка (Processing)

1. **Координатор** (Watchdog) видит файл, начинающийся на `REQ` и содержащий в адресате `COORD`.

2. Читает файл, выполняет логику.

3. **Удаляет** файл запроса (подтверждение получения).


#### 3. Ответ (Response)

1. Координатор создает файл `RES_COORD_LASER1_1712012345.json` (с тем же ID `1712012345`).

2. **Узел (LASER_1)**, который всё это время «слушал» папку на предмет файлов `RES` адресованных ему, видит ответ.

3. Забирает данные и **удаляет** файл ответа.


---

### 💻 Пример реализации логики (Python)

Ниже концепт класса для обмена сообщениями, который можно встроить в FastAPI/NiceGUI.

Python

```
import os
import json
import time
from pathlib import Path

class FileBus:
    def __init__(self, node_id, bus_path):
        self.node_id = node_id
        self.bus_path = Path(bus_path)
        self.my_responses = {} # Для хранения ожидаемых ответов

    def send_request(self, target_id, command, data):
        req_id = str(int(time.time() * 1000))
        filename = f"REQ_{self.node_id}_{target_id}_{req_id}.json"
        temp_name = f"TEMP_{filename}"

        payload = {
            "header": {"from": self.node_id, "to": target_id, "id": req_id, "cmd": command},
            "body": data
        }

        # Атомарная запись
        with open(self.bus_path / temp_name, 'w') as f:
            json.dump(payload, f)
        os.rename(self.bus_path / temp_name, self.bus_path / filename)
        return req_id

    def check_for_messages(self):
        """Сканирует папку на наличие заданий для меня"""
        for file in os.listdir(self.bus_path):
            # Если это запрос МНЕ
            if file.startswith(f"REQ_") and f"_{self.node_id}_" in file:
                self.handle_incoming_request(file)

            # Если это ответ МНЕ
            if file.startswith(f"RES_") and f"_{self.node_id}_" in file:
                self.handle_incoming_response(file)

    def handle_incoming_request(self, filename):
        with open(self.bus_path / filename, 'r') as f:
            msg = json.load(f)

        # ... Логика обработки ...
        print(f"Получен запрос: {msg['header']['cmd']}")

        # Удаляем запрос и шлем ответ (аналогично send_request, но с префиксом RES)
        os.remove(self.bus_path / filename)
```

---

### 🛡️ Предохранители

- **Чистка мусора:** Если узел упал и не удалил файл ответа, папка будет засоряться. Координатор должен раз в час удалять файлы старше 5 минут.

- **Идемпотентность:** Если Координатор упал в момент обработки, Узел может переотправить запрос с тем же ID. Координатор должен проверить по своей базе, не выполнял ли он уже это действие.

- **Контроль записи:** На Linux/Samba переименование (`os.rename`) внутри одного раздела происходит мгновенно. Это гарантирует, что другой узел не начнет читать наполовину записанный JSON.
