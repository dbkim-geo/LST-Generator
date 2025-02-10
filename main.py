import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from osgeo import gdal, ogr
import numpy as np
import os
from tkinter.ttk import Progressbar

class LSTGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LST 생성 프로그램")
        self.root.geometry("400x650")

        self.band4_path = tk.StringVar()
        self.band5_path = tk.StringVar()
        self.band10_path = tk.StringVar()
        self.bqa_path = tk.StringVar()
        self.shapefile_path = tk.StringVar()
        self.save_path = tk.StringVar()
        self.mask_clouds = tk.BooleanVar()

        # MTL 파라미터 기본값 설정
        self.ml = tk.DoubleVar(value=3.3420E-04)
        self.al = tk.DoubleVar(value=0.10000)
        self.k1 = tk.DoubleVar(value=774.8853)
        self.k2 = tk.DoubleVar(value=1321.0789)

        # 파일 선택 버튼
        tk.Button(root, text="📂 Band 4 (RED) 선택", command=lambda: self.load_file(self.band4_path)).pack(pady=5)
        self.band4_label = tk.Label(root, textvariable=self.band4_path, wraplength=380)
        self.band4_label.pack(pady=5)
        
        tk.Button(root, text="📂 Band 5 (NIR) 선택", command=lambda: self.load_file(self.band5_path)).pack(pady=5)
        self.band5_label = tk.Label(root, textvariable=self.band5_path, wraplength=380)
        self.band5_label.pack(pady=5)
        
        tk.Button(root, text="📂 Band 10 (TIR) 선택", command=lambda: self.load_file(self.band10_path)).pack(pady=5)
        self.band10_label = tk.Label(root, textvariable=self.band10_path, wraplength=380)
        self.band10_label.pack(pady=5)
        
        tk.Button(root, text="📂 QA Band 선택 (BQA)", command=lambda: self.load_file(self.bqa_path)).pack(pady=5)
        self.bqa_label = tk.Label(root, textvariable=self.bqa_path, wraplength=380)
        self.bqa_label.pack(pady=5)
        
        tk.Button(root, text="📂 Shapefile 선택", command=lambda: self.load_file(self.shapefile_path, [("Shapefile", "*.shp")])).pack(pady=5)
        self.shapefile_label = tk.Label(root, textvariable=self.shapefile_path, wraplength=380)
        self.shapefile_label.pack(pady=5)
        
        # 구름 마스킹 체크박스
        tk.Checkbutton(root, text="☁ 구름 마스킹 적용", variable=self.mask_clouds).pack(pady=5)
        
        # LST 계산 버튼
        self.process_button = tk.Button(root, text="⚡ LST 계산 시작", command=self.start_lst_process)
        self.process_button.pack(pady=10)
        
        # 진행 상태 표시 (프로그레스 바)
        self.progress = Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(pady=5)
        
        # 결과 저장 버튼
        self.save_button = tk.Button(root, text="💾 결과 저장", state=tk.DISABLED, command=self.save_result)
        self.save_button.pack(pady=10)
        self.save_label = tk.Label(root, textvariable=self.save_path, wraplength=380)
        self.save_label.pack(pady=5)

    def load_file(self, path_var, file_types=[("TIFF Files", "*.tif")]):
        initial_dir = os.getcwd()
        filename = filedialog.askopenfilename(initialdir=initial_dir, filetypes=file_types)
        if filename:
            path_var.set(filename)


    def start_lst_process(self):
        if not self.band4_path.get() or not self.band5_path.get() or not self.band10_path.get() or not self.shapefile_path.get():
            messagebox.showerror("오류", "모든 밴드 파일과 Shapefile을 선택해주세요!")
            return
        
        self.process_button.config(state=tk.DISABLED)
        self.progress.start()
        threading.Thread(target=self.calculate_lst, daemon=True).start()

    def clip_raster(self, raster_path, shapefile_path):
        ds = gdal.Open(raster_path)
        clipped_ds = gdal.Warp("", ds, cutlineDSName=shapefile_path, cropToCutline=True, format="VRT")
        return clipped_ds


    def calculate_lst(self):
        try:
            dataset_b4 = self.clip_raster(self.band4_path.get(), self.shapefile_path.get())
            dataset_b5 = self.clip_raster(self.band5_path.get(), self.shapefile_path.get())
            dataset_b10 = self.clip_raster(self.band10_path.get(), self.shapefile_path.get())

            # Band 10 기준으로 좌표 정보 저장
            self.projection = dataset_b10.GetProjection()
            self.geotransform = dataset_b10.GetGeoTransform()

            band4 = dataset_b4.GetRasterBand(1).ReadAsArray().astype(np.float32)
            band5 = dataset_b5.GetRasterBand(1).ReadAsArray().astype(np.float32)
            band10 = dataset_b10.GetRasterBand(1).ReadAsArray().astype(np.float32)

            # MTL 값 가져오기
            ML = self.ml.get()
            AL = self.al.get()
            K1 = self.k1.get()
            K2 = self.k2.get()

            # TOA 방사휘도 계산
            L = ML * band10 + AL

            # TOA 밝기온도 변환
            T = K2 / np.log((K1 / L) + 1)

            # NDVI 및 방사율 계산
            NDVI = np.where((band5 + band4) == 0, 0, (band5 - band4) / (band5 + band4))  # 0으로 나누는 경우 방지
            NDVI = np.clip(NDVI, -1, 1)  # NDVI 값이 정상 범위 유지
            emissivity = 0.004 * NDVI + 0.986
        
            # 최종 LST 계산
            LST = T / (1 + (10.9e-6 * T / 1.4388e-2) * np.log(emissivity))
            
            # 150 이하의 값은 NaN 처리
            LST[LST <= 150] = np.nan
            
            self.result = LST  # 결과 저장
            self.progress.stop()
            self.save_button.config(state=tk.NORMAL)
            messagebox.showinfo("완료", "LST 계산 완료!")
        except Exception as e:
            messagebox.showerror("오류", f"처리 중 오류 발생: {e}")
        finally:
            self.process_button.config(state=tk.NORMAL)

    def save_result(self):
        initial_dir = os.getcwd()
        save_path = filedialog.asksaveasfilename(initialdir=initial_dir, defaultextension=".tif", filetypes=[("TIFF Files", "*.tif")])
        if save_path:
            driver = gdal.GetDriverByName("GTiff")
            out_dataset = driver.Create(save_path, self.result.shape[1], self.result.shape[0], 1, gdal.GDT_Float32)
            out_dataset.SetProjection(self.projection)  # 좌표계 적용
            out_dataset.SetGeoTransform(self.geotransform)  # 위치 정보 적용
            out_band = out_dataset.GetRasterBand(1)
            out_band.WriteArray(self.result)
            out_dataset.FlushCache()
            self.save_path.set(save_path)
            self.save_label.config(text=f"저장된 파일: {save_path}")
            messagebox.showinfo("저장 완료", "LST TIFF 저장 완료!")

if __name__ == "__main__":
    root = tk.Tk()
    app = LSTGeneratorApp(root)
    root.mainloop()
