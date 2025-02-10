# 🌍 LST-Generator (Landsat Surface Temperature 계산기) 🚀

LST-Generator는 **Landsat Collection 2 Level 1 데이터**를 사용하여 **지표면 온도(LST)** 를 계산하는 Python 기반 GUI 응용 프로그램입니다.  
**GDAL, NumPy, Tkinter** 를 활용하여 위성 데이터를 처리하고, 구름 마스킹을 적용한 후 최종 결과를 **GeoTIFF** 파일로 저장합니다.

---

## 📌 주요 기능

✅ **GUI 기반 위성 영상 처리** (Tkinter)  
✅ **Landsat Collection 2 Level 1 기반 LST 계산**  
✅ **F-Mask 적용 (구름 & 구름 그림자 제거)**  
✅ **GeoTIFF 파일 입력 및 출력 지원**  
✅ **Shapefile(.shp) 선택 후 관심지역(ROI)만 자르기**  
✅ **EXE 패키징 가능 (PyInstaller)**  

---

## 🔧 설치 방법

### 1️⃣ 가상 환경 생성 및 활성화
```sh
python -m venv lstgen
lstgen\Scripts\activate  # Windows
```

### 2️⃣ 필수 패키지 설치
```sh
pip install -r requirements.txt
```

### 3️⃣ GDAL 설치 (Windows)
GDAL은 별도로 설치해야 합니다.  
GDAL `.whl` 파일을 다운로드 후 설치하세요.
GDAL .whl 파일은 [GitHub Releases](https://github.com/user-attachments/files/18733522/GDAL-3.2.3-cp38-cp38-win_amd64.zip) 페이지에서 다운로드, 압축 해제 후 설치하 세요

```sh
pip install GDAL-3.2.3-cp38-cp38-win_amd64.whl
```

---

## ▶ 실행 방법
```sh
python main.py
```
또는, EXE 패키징 후 실행 파일 사용!

---

## 🔥 EXE 패키징 방법 (Windows)
아래 명령어를 실행하면 **단일 EXE 파일(`LST_Generator.exe`)** 이 생성됩니다.
```sh
pyinstaller --onefile --windowed --name=LST_Generator ^
    --hidden-import=osgeo ^
    --add-binary "lstgen\Lib\site-packages\osgeo;osgeo" main.py
```
📌 **생성된 실행 파일 경로:** `dist/LST_Generator.exe`  

---

## ☁️ 구름 마스킹 (F-Mask) 적용 방식
Landsat QA Band를 사용하여 **구름 및 그림자 제거**  
| 비트 위치 | 마스킹 값 | 설명 |
|----------|---------|------|
| 3        | `8`  | 구름 그림자(Cloud Shadow) |
| 5        | `32` | 구름(Cloud) |

✅ **마스킹 조건:**  
```python
cloud_mask = ((bqa & (1 << 3)) != 0) | ((bqa & (1 << 5)) != 0)
```
✅ **결과:**  
- 구름(Cloud) 및 구름 그림자(Shadow) 제거  
- 물(Water) 및 눈(Snow)은 유지!  
