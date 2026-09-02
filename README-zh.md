[English](README.md) | [繁體中文](README-zh.md)

# Amazon 配送營運分析 

> **專案簡介**  
> 本專案使用 Kaggle 的 Amazon 配送資料集，模擬電商/物流團隊如何將**模糊的商業問題**一步步轉化為**具體的數據分析**、**KPI 指標體系**與**營運決策建議**。專案重點在於分析邏輯、假設驗證、資料品質管制與營運可行性評估，而非單純套用模型。
> 
> 📊 **簡報版本 (Slide Deck)**：本專案同時包含透過 **OpenSlide** (React Slide Framework) 開發的互動簡報，方便觀看此專案的人可以快速掌握專案內容。

---

## 1. 資料來源 (Data Source)

- **資料來源**：[Kaggle - Amazon Delivery Dataset](https://www.kaggle.com/datasets/sujalsuthar/amazon-delivery-dataset/data)
- **資料規模**：超過 43,000 筆配送紀錄，包含訂單細節、配送員評分、天氣、交通狀況及配送耗時等維度。

---

## 2. 商業問題與分析流程 (Business Problem & Workflow)

### 2.1 從模糊商業問題 ➡️ 具體數據分析
* **原始商業問題**：營運團隊發現「部分訂單配送耗時過長」，在營運資源有限的情況下，應該優先改善哪一個配送環節？
* **轉化後的分析問題**：
  1. **長時間配送集中在哪裡？** 比較區域 (Area)、交通 (Traffic)、時段 (Pickup Period)、距離 (Distance)、天氣 (Weather) 與品類 (Category) 的配送時間分布。
  2. **觀察到的群組差異是否具實質營運意義？** 檢查樣本數、中位數、IQR 與長時間配送比例（P75），避免僅依賴統計顯著性。
  3. **極端區域差異能否被已知因素解釋？** 以 Semi-Urban 為重點，檢驗交通與距離等變數組成。
  4. **納入其他已知因素後，關聯是否仍穩定？** 透過多變量 OLS 迴歸模型（輔以 HC3 穩健標準誤）控制混淆因子。
  5. **哪個因素最值得優先採取下一步行動？** 結合效應大小、數據穩定性與營運可介入性，決定優先調查項目與實驗規劃。

### 2.2 分析思考流程
```
[模糊商業問題] 配送耗時過長，資源該優先投入何處？
       ↓
[KPI與指標定義] 主要 KPI: Delivery Time (中位數/IQR) | 輔助: P75 長時間配送率
       ↓
[資料品質清理] 清理 4.3 萬筆紀錄 (座標異常/跨午夜/評分範圍/不隨意推補)
       ↓
[探索與群組比較] 鎖定配送耗時顯著偏高的 Semi-Urban 區域
       ↓
[多變量關聯控制] OLS + HC3 穩健標準誤 (排除 Traffic/Distance/Category 混淆)
       ↓
[營運決策與建議] 優先 Semi-Urban 流程診斷，採低風險小規模實驗驗證
```

---

## 3. KPI 與指標定義 (KPI & Metrics)

為避免傳統平均數易受極端值干擾，本分析採用複合指標體系：
* **主要 KPI：`Delivery_Time`（配送總耗時，分鐘）**
  * 衡量每筆配送時間，以**中位數 (Median)**、**四分位距 (IQR)** 及全分布形態為核心比較基準。
* **輔助指標：`Long-Duration Delivery Rate`（長時間配送比例）**
  * 將高於 overall 第 75 百分位（160 分鐘）的紀錄定義為長時間配送，用於評估極端延誤風險。（*備註：資料無 SLA 或承諾 ETA，此門檻為相對分析基準非逾期標準*）。

---

## 4. 資料清理與品質管制 (Data Quality & Cleaning)

為維持資料真偽與後續分析品質，清理邏輯集中於 `src/data_preparation.py`：
* **評分異常**：發現 53 筆 Rating 超過 1–5 範圍，設為 NA 並保留配送紀錄。
* **跨午夜時間校正**：修正 828 筆跨午夜的 Pickup timestamp 邏輯。
* **地理座標校正**：識別 3,693 筆 0 原點座標與符號錯誤；在距離計算時排除，避免距離估計偏誤，但不隨意刪除整筆訂單資料。
* **缺失值處理**：文字形式缺失（如 "NaN"）統一轉為真正的 NA，不進行盲目推補 (Imputation)。

---

## 5. 資料分析與核心發現 (Data Analysis & Key Insights)

1. **Semi-Urban 區域存在顯著效能瓶頸**
   * Semi-Urban 配送時間中位數達 **245 分鐘**（Urban / Metropolitan 僅約 125–126 分鐘），且有 **94.7%** 的紀錄高於長時間配送門檻（160 分鐘）。
2. **交通與距離不足以解釋區域差距**
   * 即使在同等交通堵塞 (Jam) 條件下比較，Semi-Urban 依然顯著較慢。
   * 多變量迴歸控制 Distance、Traffic、Period、Weather 與 Category 後，Semi-Urban 仍相對其他區域高出約 **102 分鐘**（95% CI: 96–108 分鐘），支持存在未被紀錄的區域流程瓶頸（如派單規則、備貨等待、路線設計等）。
3. **生鮮品類 (Grocery) 具獨立流程特徵**
   * 非 Grocery 類別配送時間比 Grocery 高出 103–106 分鐘，提示生鮮可能採用獨立速配鏈條，後續診斷應分層處理。

---

## 6. 結論與商業建議 (Decision & Actionable Recommendations)

* **優先行動**：將 **Semi-Urban 設為第一階段流程診斷區域**。建議補充「等待派單、備貨等待、實際行駛、交付時間」分段資料，而非直接全面增加人力。
* **避免無效決策**：時段 (Pickup Period) 效果對 Traffic 變數敏感且資料重疊度高，不建議直接據此調整人力班表 (Staffing)。
* **驗證與擴展策略 (Rollout)**：在不影響總單量的前提下，先針對 Semi-Urban 進行小規模 route/pickup/dispatch 試驗，以 `Delivery_Time` 中位數、P75 與每單成本 (Cost per delivery) 作為評估指標，驗證有效後再擴大實施。

---

## 📊 簡報版本 (Slide Deck)

本專案將分析精華製作成視覺化動態簡報（基於 OpenSlide 框架開發並導出為獨立 HTML），方便快速展示與閱讀：

* **開啟方式**：直接進入 [`slides/`](slides/) 目錄，點擊並透過任何主流瀏覽器（如 Chrome, Safari, Edge）開啟 HTML 檔案即可：
  * 中文版簡報：[`slides/amazon-delivery-analysis-zh.html`](slides/amazon-delivery-analysis-zh.html)
  * 英文版簡報：[`slides/amazon-delivery-analysis-en.html`](slides/amazon-delivery-analysis-en.html)

---

## 📂 專案檔案結構 (Project Structure)

* [`README-zh.md`](README-zh.md)：中文專案總覽（本檔案）
* [`README.md`](README.md)：英文專案總覽
* [`amazon_delivery_revised_zh.ipynb`](amazon_delivery_revised_zh.ipynb)：完整中文分析 Jupyter Notebook
* [`amazon_delivery_revised_en.ipynb`](amazon_delivery_revised_en.ipynb)：完整英文分析 Jupyter Notebook
* [`src/data_preparation.py`](src/data_preparation.py)：資料清理與特徵工程模組
* [`slides/`](slides/)：簡報檔 HTML（中文與英文版本）
