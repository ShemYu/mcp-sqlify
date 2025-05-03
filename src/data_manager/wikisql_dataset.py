#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WikiSQL Dataset 管理模組。

負責下載、解析與快取 WikiSQL 資料集。
使用 Hugging Face datasets 庫進行資料集管理。
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import datasets
from datasets import load_dataset, DatasetDict, Dataset
import dotenv

# 載入環境變數
dotenv.load_dotenv()

logger = logging.getLogger(__name__)


class WikiSQLDataset:
    """
    WikiSQL 資料集管理類。

    使用 Hugging Face datasets 庫負責下載、解析與快取 WikiSQL 資料。
    提供便捷的資料存取介面。
    """
    
    # WikiSQL 資料集名稱
    DATASET_NAME = "Salesforce/wikisql"
    
    def __init__(self, data_root: str = None, use_auth_token: bool = False):
        """
        初始化 WikiSQLDataset 實例。
        
        Args:
            data_root: 資料存儲的根目錄，若不指定則使用預設快取目錄
            use_auth_token: 是否使用 Hugging Face 驗證令牙訪問私有或限制存取的資料集
        """
        # 設定資料根目錄
        if data_root is None:
            self.data_root = None  # 使用 datasets 庫的預設快取路徑
        else:
            self.data_root = data_root
            # 確保目錄存在
            os.makedirs(self.data_root, exist_ok=True)
        
        # 從環境變數獲取 Hugging Face 驗證令牌
        self.auth_token = os.environ.get('HUGGING_FACE_AUTH_TOKEN')
        if not self.auth_token and use_auth_token:
            logger.warning("未設置 HUGGING_FACE_AUTH_TOKEN 環境變數，但 use_auth_token 為 True")
        
        # 資料集實例
        self._dataset = None
        
        # 用於儲存載入的資料
        self.data_cache = {}
    
    def _load_dataset(self) -> DatasetDict:
        """
        載入 WikiSQL 資料集。
        
        Returns:
            載入的 DatasetDict 對象
            
        Raises:
            RuntimeError: 載入失敗
        """
        if self._dataset is not None:
            return self._dataset
            
        try:
            logger.info(f"正在使用 Hugging Face datasets 庫載入 WikiSQL 資料集...")
            download_config = None
            
            # 如果指定了自定義路徑，則設置快取目錄
            if self.data_root:
                download_config = datasets.DownloadConfig(
                    cache_dir=self.data_root
                )
                
            # 載入資料集
            self._dataset = load_dataset(
                self.DATASET_NAME,
                token=self.auth_token,  # 新版 datasets 庫使用 token 而非 use_auth_token
                download_config=download_config,
                trust_remote_code=True
            )
            
            logger.info(f"WikiSQL 資料集載入成功，包含分割: {list(self._dataset.keys())}")
            return self._dataset
            
        except Exception as e:
            raise RuntimeError(f"載入 WikiSQL 資料集失敗: {str(e)}")
    
    def download_dataset(self, splits: Optional[List[str]] = None, force_redownload: bool = False) -> Dict[str, str]:
        """
        下載 WikiSQL 資料集。
        
        注意：datasets 庫會自動處理下載與快取，這個方法主要用於確保資料集已經下載。
        
        Args:
            splits: 要下載的資料分割列表，若為 None 則下載所有分割
            force_redownload: 是否強制重新下載（透過清除快取）
            
        Returns:
            包含各分割命名及其快取路徑的字典
            
        Raises:
            RuntimeError: 下載失敗
        """
        try:
            # 如果需要強制重新下載，則清除快取
            if force_redownload and self.data_root:
                logger.info(f"清除 WikiSQL 資料集快取 (強制重新下載)")
                # 使用 datasets 庫的快取管理功能
                # 注意：這某種程度上是內部 API，建議對字在覆蓋在測試中
                datasets.config.HF_DATASETS_CACHE = self.data_root
                datasets.utils.filesystem.rm_tree(datasets.config.HF_DATASETS_CACHE)
                self._dataset = None
            
            # 載入資料集 (由 datasets 庫處理下載)
            dataset_dict = self._load_dataset()
            
            # 確定要下載的分割
            if splits is None:
                splits_to_download = list(dataset_dict.keys())
            else:
                splits_to_download = splits
                # 檢查是否有無效的分割名稱
                invalid_splits = [s for s in splits_to_download if s not in dataset_dict]
                if invalid_splits:
                    raise ValueError(f"無效的分割名稱: {invalid_splits}\n"
                                   f"有效的分割為: {list(dataset_dict.keys())}")
            
            # 通過存取各分割來觸發下載
            results = {}
            for split in splits_to_download:
                # 存取第一個數據點來觸發下載
                _ = dataset_dict[split][0]
                logger.info(f"分割 '{split}' 已成功載入，共 {len(dataset_dict[split])} 個數據點")
                
                # 取得快取資訊 (注意：這也是某種程度上的內部實現細節)
                if hasattr(dataset_dict[split], '_data_files') and dataset_dict[split]._data_files:
                    cache_files = dataset_dict[split]._data_files
                    if cache_files and len(cache_files) > 0:
                        results[split] = cache_files[0]['filename']
                    else:
                        results[split] = f"<內部快取>/{split}"
                else:
                    results[split] = f"<內部快取>/{split}"
            
            return results
                
        except Exception as e:
            raise RuntimeError(f"下載 WikiSQL 資料集失敗: {str(e)}")
    
    def load_split(self, split: str, limit: Optional[int] = None, download_if_missing: bool = True) -> List[Dict[str, Any]]:
        """
        載入指定分割的 WikiSQL 資料。
        
        Args:
            split: 資料分割，可為 'train', 'validation', 'test'
                (注意: 在 Hugging Face datasets 中，'dev' 分割被命名為 'validation')
            limit: 可選的資料數量限制，若為 None 則載入全部
            download_if_missing: 若資料不存在，是否自動下載
            
        Returns:
            資料列表，每個元素是一個資料點的字典
            
        Raises:
            ValueError: 無效的分割名稱
            RuntimeError: 載入失敗
        """
        # 檢查緩存
        cache_key = f"{split}_{limit}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
            
        # 將 'dev' 映射為 'validation'，以符合 HF datasets 的命名規則
        hf_split = 'validation' if split == 'dev' else split
        
        try:
            # 確保資料集已載入
            dataset_dict = self._load_dataset()
            
            # 檢查分割名稱是否有效
            if hf_split not in dataset_dict:
                raise ValueError(f"無效的分割名稱: {split} (HF: {hf_split})\n"
                               f"有效的分割為: {list(dataset_dict.keys())}")
            
            # 取得分割資料
            split_dataset = dataset_dict[hf_split]
            
            # 如果有限制，則只取前 N 個項目
            if limit is not None:
                split_dataset = split_dataset.select(range(min(limit, len(split_dataset))))
            
            # 轉換為 Python 字典列表格式
            data = []
            for item in split_dataset:
                # 注意：手動轉換為字典，因為 Hugging Face Dataset 項目不是標準字典
                example = dict(item)
                # 注意：HF datasets 會將表格索引列轉換為數字類型，所以需要確保該類型符合原始 WikiSQL 的框架
                if 'id' in example and isinstance(example['id'], (int, float)):
                    example['id'] = str(int(example['id']))  # 確保 ID 是字符串形式
                data.append(example)
            
            logger.info(f"已載入 {len(data)} 個 {split} 資料點")
            
            # 儲存到緩存
            self.data_cache[cache_key] = data
            return data
            
        except Exception as e:
            raise RuntimeError(f"載入 {split} 分割失敗: {str(e)}")
    
    def get_example(self, split: str, index: int) -> Dict[str, Any]:
        """
        獲取特定分割中的單個範例。
        
        Args:
            split: 資料分割，可為 'train', 'dev', 或 'test'
            index: 範例索引
            
        Returns:
            該索引的資料範例
            
        Raises:
            IndexError: 索引超出範圍
            ValueError: 無效的分割名稱
            RuntimeError: 載入失敗
        """
        # 轉換分割名稱，符合 Hugging Face datasets 命名規則
        hf_split = 'validation' if split == 'dev' else split
        
        try:
            # 確保資料集已載入
            dataset_dict = self._load_dataset()
            
            # 檢查分割是否有效
            if hf_split not in dataset_dict:
                raise ValueError(f"無效的分割名稱: {split} (HF: {hf_split})\n"
                               f"有效的分割為: {list(dataset_dict.keys())}")
            
            # 檢查索引是否超出範圍
            if index < 0 or index >= len(dataset_dict[hf_split]):
                raise IndexError(f"索引 {index} 超出範圍\n"
                                f"{split} 資料集有 {len(dataset_dict[hf_split])} 個範例")
            
            # 獲取範例並轉換為字典
            example = dict(dataset_dict[hf_split][index])
            
            # 確保 ID 是字符串形式（如果存在）
            if 'id' in example and isinstance(example['id'], (int, float)):
                example['id'] = str(int(example['id']))
                
            return example
            
        except (ValueError, IndexError):
            # 讓這些特定的異常直接傳過
            raise
        except Exception as e:
            raise RuntimeError(f"取得範例失敗: {str(e)}")
    
    def get_table_schema(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """
        從範例中提取表格結構。
        
        Args:
            example: WikiSQL 資料範例
            
        Returns:
            表格結構資訊的字典
            
        Raises:
            KeyError: 範例缺少必要的表格資訊
        """
        if 'table' not in example:
            raise KeyError(f"範例中缺少 'table' 欄位")
            
        table = example['table']
        
        # 確保所有需要的表格欄位都存在
        required_fields = ['header', 'types']
        for field in required_fields:
            if field not in table:
                raise KeyError(f"表格中缺少必要的 '{field}' 欄位")
        
        # 生成唯一的表名
        table_hash = abs(hash(tuple(table['header']))) % 10000
        table_name = f"table_{table_hash}"
        
        return {
            'header': table['header'],
            'types': table['types'],
            'name': table_name
        }
    
    def get_splits_info(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有資料分割的統計資訊。
        
        Returns:
            包含每個分割資訊的字典
            
        Raises:
            RuntimeError: 獲取資訊失敗
        """
        try:
            # 確保資料集已載入
            dataset_dict = self._load_dataset()
            
            # 為每個分割收集資訊
            info = {}
            for split in dataset_dict.keys():
                # 給出在調用串口中顯示的分割名稱（將 'validation' 轉回 'dev'）
                api_split = 'dev' if split == 'validation' else split
                
                # 取得快取資訊（如果可用）
                cache_file = None
                if hasattr(dataset_dict[split], '_data_files') and dataset_dict[split]._data_files:
                    cache_files = dataset_dict[split]._data_files
                    if cache_files and len(cache_files) > 0:
                        cache_file = cache_files[0]['filename']
                
                # 預先存取一項數據來確保已經下載
                try:
                    _ = dataset_dict[split][0]
                    status = 'downloaded'
                except Exception:
                    status = 'loading_error'
                
                info[api_split] = {
                    'examples': len(dataset_dict[split]),
                    'status': status,
                    'hf_split': split,
                    'cache_file': cache_file
                }
            
            return info
            
        except Exception as e:
            raise RuntimeError(f"獲取資料集資訊失敗: {str(e)}")
    
    def search_examples(self, keyword: str, split: str = 'train', limit: int = 5) -> List[Dict[str, Any]]:
        """
        在指定分割中搜索包含關鍵字的範例。
        
        Args:
            keyword: 搜索關鍵字
            split: 要搜索的資料分割
            limit: 最多返回的結果數量
            
        Returns:
            匹配的範例列表
            
        Raises:
            ValueError: 無效的分割名稱
            RuntimeError: 搜索失敗
        """
        try:
            # 轉換分割名稱，符合 Hugging Face datasets 命名規則
            hf_split = 'validation' if split == 'dev' else split
            
            # 確保資料集已載入
            dataset_dict = self._load_dataset()
            
            # 檢查分割是否有效
            if hf_split not in dataset_dict:
                raise ValueError(f"無效的分割名稱: {split} (HF: {hf_split})\n"
                               f"有效的分割為: {list(dataset_dict.keys())}")
            
            # 使用 datasets 庫的過濾功能進行搜索
            # 注意：datasets 支持使用函數進行過濾
            split_dataset = dataset_dict[hf_split]
            
            def filter_fn(example):
                return keyword.lower() in example['question'].lower()
            
            # 進行過濾
            filtered = split_dataset.filter(filter_fn)
            
            # 取得前 N 個結果
            results = []
            for i, item in enumerate(filtered):
                if i >= limit:
                    break
                # 轉換為字典
                example = dict(item)
                # 清理類型
                if 'id' in example and isinstance(example['id'], (int, float)):
                    example['id'] = str(int(example['id']))
                results.append(example)
            
            return results
            
        except ValueError:
            # 讓這個特定異常直接傳過
            raise
        except Exception as e:
            raise RuntimeError(f"搜索範例失敗: {str(e)}")


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 示範使用
    dataset = WikiSQLDataset()
    
    # 獲取資料集資訊
    print("資料集資訊:")
    try:
        info = dataset.get_splits_info()
        for split, split_info in info.items():
            print(f"{split}: {split_info}")
        
        # 下載資料集
        print("\n確保資料集已下載:")
        download_info = dataset.download_dataset()
        for split, path in download_info.items():
            print(f"{split}: {path}")
        
        # 載入少量樣本
        print("\n載入前 3 個樣本:")
        samples = dataset.load_split('train', limit=3)
        
        for i, sample in enumerate(samples):
            print(f"\n樣本 {i+1}:")
            print(f"問題: {sample['question']}")
            print(f"表頭: {sample['table']['header']}")
            if 'sql' in sample and 'human_readable' in sample['sql']:
                print(f"SQL: {sample['sql']['human_readable']}")
            elif 'sql' in sample:
                print(f"SQL: {sample['sql']}")
            
        # 搜索範例
        print("\n搜索範例:")
        keyword = "who"
        search_results = dataset.search_examples(keyword, 'train', limit=2)
        print(f"搜索 '{keyword}' 結果: {len(search_results)} 項")
        for i, result in enumerate(search_results):
            print(f"\u7d50果 {i+1}: {result['question']}")
        
    except Exception as e:
        print(f"\u9047到錯誤: {str(e)}")
