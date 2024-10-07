# Oklink 區塊鏈數據擷取工具

這個專案是一個用於從 Oklink API 擷取區塊鏈交易數據的工具。它支持多個區塊鏈（如以太坊、比特幣和波場），並將數據保存為 CSV 和 JSON 格式。

## 功能

- 擷取最新的區塊交易數據
- 支持多個區塊鏈（ETH、BTC、TRON）
- 將數據保存為 CSV 和 JSON 格式
- 異步處理提高效率
- 靈活的錯誤處理和日誌記錄
- 自動速率限制，確保符合 API 使用規範

## 安裝

1. 克隆此存儲庫：
   ```
   git clone https://github.com/yourusername/oklink-data-extractor.git
   cd oklink-data-extractor
   ```

2. 創建並激活虛擬環境：
   ```
   python -m venv venv
   source venv/bin/activate  
   # 在 Windows 上使用 `venv\Scripts\activate`
   ```

3. 安裝依賴：
   ```
   pip install -r requirements.txt
   ```

4. 複製 `.env.example` 文件並重命名為 `.env`，然後填入您的 Oklink API 密鑰。

## 使用方法

運行主程式：

```
python main.py
```

這將擷取最新的區塊交易數據並保存到 `data/{chain}/csv/` 和 `data/{chain}/json/` 目錄中，其中 `{chain}` 是區塊鏈的名稱（如 eth、btc、tron）。每個交易將被保存為單獨的文件，文件名包含區塊鏈名稱、日期和區塊號碼。


### 清理數據

要清除所有生成的 CSV 和 JSON 文件（不包括 .gitkeep）：

```
python clean_data.py
```

## 運行測試

要運行測試套件：

```
pytest tests/
```

## 專案結構

```
oklink_project/
│
├── src/
│   ├── services/
│   │   ├── base_service.py
│   │   ├── eth_service.py
│   │   ├── btc_service.py
│   │   └── tron_service.py
│   ├── utils/
│   │   ├── utils.py
│   │   └── rate_limiter.py
│   ├── factory.py
│   └── config.py
│
├── tests/
│   ├── test_services.py
│   └── test_utils.py
│
├── data/
│   ├── csv/
│   └── json/
│
├── .env
├── .env.example
├── requirements.txt
├── main.py
├── clean_data.py
└── README.md
```

## API 使用注意事項

本工具遵守 Oklink API 的使用限制，具體為：

- 單一 API key 每秒不能發送超過 5 次請求。
- 已實現自動速率限制以確保不超過此限制。

## 錯誤處理

程式包含全面的錯誤處理機制。所有錯誤都會被記錄到日誌文件中，您可以在 `logs/` 目錄下找到這些日誌。
