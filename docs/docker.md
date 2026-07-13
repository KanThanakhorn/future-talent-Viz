# Build และรันด้วย Docker

Docker image ใช้ Python 3.14.6 slim-bookworm แบบ multi-stage มี Poppler, Tesseract ภาษาไทย/อังกฤษ และ ONNX Runtime จาก Python dependencies ตัว image ไม่รวม dataset, SQLite database หรือ model cache; ทั้งหมด mount จาก host ตอน runtime

## 1. ตรวจ Docker

```bash
docker version
docker compose version
```

ถ้าเจอ `permission denied ... /var/run/docker.sock` ให้เติม `sudo` หน้า Docker commands ในคู่มือนี้ เช่น `sudo docker compose build --pull`

## 2. กำหนด UID/GID

Compose ตั้งค่า default เป็น `1000:1000` ซึ่งตรงกับผู้ใช้ทั่วไปบน Ubuntu หาก UID ต่างออกไปให้ export ก่อนรัน:

```bash
export DOCKER_UID="$(id -u)"
export DOCKER_GID="$(id -g)"
```

ค่านี้ทำให้ process ที่ไม่ใช่ root ใน container เขียน `./data` บน host ได้

## 3. Build image

```bash
docker compose build --pull
```

`--pull` ตรวจ base image ใหม่ก่อน build ผลลัพธ์มีชื่อ `future-ready-talent:local` ตรวจได้ด้วย:

```bash
docker image ls future-ready-talent
```

หากต้องการ build สะอาดทั้งหมด:

```bash
docker compose build --pull --no-cache
```

## 4. เตรียมฐานข้อมูลและ model index

รัน ingestion ก่อนหนึ่งครั้ง:

```bash
docker compose run --rm app python -m app.ingest
```

จากนั้นสร้าง multilingual embedding index คำสั่งนี้จะดาวน์โหลด ONNX model ครั้งแรกและเก็บใน `./data/model-cache`:

```bash
docker compose run --rm app python -m app.reindex_embeddings
```

ถ้าเอกสารเปลี่ยน ให้รันสองคำสั่งนี้ใหม่ตามลำดับ Index เก่าจะไม่ถูก activate จนกว่า vector ใหม่จะตรวจครบทุก chunk

## 5. เปิดระบบ

```bash
docker compose up -d
docker compose ps
docker compose logs -f app
```

เปิด `http://localhost:8000` และตรวจ health:

```bash
curl --fail http://localhost:8000/api/health
```

หยุดดู log ด้วย `Ctrl+C` โดย container ยังทำงานอยู่

## 6. หยุดหรือ rebuild

```bash
docker compose down
```

หลังแก้โค้ด:

```bash
docker compose build --pull
docker compose up -d --force-recreate
```

ดูสาเหตุเมื่อ container ไม่ healthy:

```bash
docker compose ps
docker compose logs --tail=200 app
docker compose run --rm app python -m app.ingest --help
```

## Build โดยไม่ใช้ Compose

```bash
docker build --pull -t future-ready-talent:local .
```

การรันตรงด้วย `docker run` ต้อง mount ทั้ง `data` และ dataset เอง ดังนั้นสำหรับโปรเจกต์นี้แนะนำ Compose เพื่อลดโอกาสระบุ path หรือ permission ผิด
