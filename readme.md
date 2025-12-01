# Лицензия: Поиск номеров (License Plate Search)

Проект: Телеграм‑бот, который отвечает на городские/региональные запросы по России и возвращает:
- региональные коды автомобильных номеров
- телефонные коды городов
- карту с указанием местоположения города и контекстом по всей России (Yandex Static Maps)

中文简介：一个支持俄语/中文的俄罗斯城市/地区查询 Telegram 机器人，返回车牌区域代码、电话区号，并展示城市在俄罗斯联邦中的地理位置（Yandex 静态地图）。

---

## Архитектура (Architecture)

- `bot/main.py` — точка входа, хэндлеры команд и текста、异步地理编码/地图生成/语音合成
- `bot/nlp.py` — 意图解析：城市→车牌、车牌→地区、城市→电话、电话→城市
- `bot/db.py` — SQLite 架构与数据灌库：
  - `seed_full_regions` 全国地区名
  - `seed_auto_codes_full` 地区→车牌代码完整映射
  - `seed_cities_full` 常见城市→所属地区
  - `seed_phone_codes_capitals` 省会城市电话区号（兼容地理编码补坐标）
  - 查询函数：`find_city_by_name`、`find_region_by_auto_code`、`list_auto_codes_by_region`、`find_city_by_phone_code` 等
- `bot/maps.py` — 地图生成（Yandex 单源）：
  - `generate_city_dual_map` 左侧全国上下文 (z=3) + 右侧城市放大 (z=11)
  - `generate_city_focus_map` 城市聚焦 (z=10)
  - `generate_russia_location_map` 全国位置图 (z=3)
- `bot/geocode.py` — OSM Nominatim 地理编码（用于补全坐标/边界）
- `bot/reply_templates.py` — 文本格式化
- `bot/tts.py` — 简单 TTS（本地 wav）
- `bot/config.py` — 配置与数据路径

运行时策略：
- 地图请求采用 Yandex 静态地图；失败时使用本地占位图，避免 OSM 瓦片封锁
- 阻塞 I/O（地理编码、地图下载、TTS）均在后台线程执行，避免消息排队
- 图片上传失败回退为文档发送，保证弱网下可见

---

## Установка и запуск (Setup & Run)

Windows PowerShell：

```powershell
# 1) 创建并激活虚拟环境（可选）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) 安装依赖
pip install -r requirements.txt

# 3) 设置 Telegram Bot 令牌
$env:TELEGRAM_BOT_TOKEN="<你的Bot令牌>"

# 4) 启动机器人
python -m bot.main
```

Linux/macOS（示例）：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="<your_bot_token>"
python -m bot.main
```

自检模式（不联网发图，仅测试意图解析）：

```bash
python -m bot.main --selftest
```

---

## Использование (Usage)

示例输入：
- `Москва номер региона` → 返回城市、所属地区及其所有车牌区域代码，并附带双窗地图
- `199 какой регион` → 返回地区及其车牌区域代码，并附带该地区首府定位地图
- `812 какой город` → 返回城市及电话区号，并附带双窗地图

支持中文输入，例如：
- `莫斯科车牌代码`
- `199 是哪个地区`
- `圣彼得堡电话区号`

---

## Переменные окружения (Environment)

- `TELEGRAM_BOT_TOKEN` — 你的 Telegram Bot 令牌（必需）
- 代理环境变量建议清理，以免 httpx 读取无效代理导致错误（应用内部已做防护）：`HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`、`SOCKS_PROXY` 等

---

## Технические детали (Technical Notes)

- 地图：Yandex Static Maps（`ll`,`z`,`size`,`pt`），左侧全国视图 z=3，右侧城市视图 z=11
- 数据：
  - 地区→车牌代码完整映射（包含重复/扩展代码，如 177/197/199/777 等）
  - 省会城市电话区号覆盖
  - 常见城市→所属地区映射，未包含坐标时运行期使用地理编码补充
- 发送：优先 `reply_photo`，失败回退 `reply_document`
- 存储：SQLite（默认在 `bot/config.py` 配置的数据目录下）

---

## Троблшутинг (Troubleshooting)

- 图片不显示/延迟：
  - 弱网络下地图下载或上传可能超时，已缩短超时并加入回退；仍不稳定时会以文档发送
- 启动报错包含代理 scheme：
  - 清理环境代理变量或在 `run_bot()` 处保持禁用；当前项目已显式禁止环境代理参与 httpx 请求
- OSM 瓦片封锁：
  - 已移除 OSM 瓦片拼接回退，避免出现“Access blocked”图片

---

