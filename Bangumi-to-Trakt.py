import csv
import configparser
import requests
import time
import pandas as pd
import os
import shutil
import sys
import traceback
import Levenshtein
import re
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def archive_old_files(script_dir):
    """
    将旧的输出文件和日志文件移动到 'old_documents' 子目录
    
    Args:
        script_dir (str): 脚本所在的目录路径
    """
    # 创建 old_documents 子目录（如果不存在）
    old_docs_dir = os.path.join(script_dir, 'old_documents')
    os.makedirs(old_docs_dir, exist_ok=True)

    # 定义需要归档的文件列表（包括临时和输出文件）
    files_to_archive = [
        # 输出文件
        "trakt_formatted.csv",
        "trakt_formatted_movies.csv",
        "trakt_formatted_shows.csv",
        "trakt_formatted_movies_watched.csv",
        "trakt_formatted_shows_watched.csv",
        "trakt_formatted_movies_watchlist.csv",
        "trakt_formatted_shows_watchlist.csv",
        
        # 临时文件
        "temp_trakt_formatted.csv",
        "temp_trakt_formatted_movies.csv", 
        "temp_trakt_formatted_shows.csv",
        "temp_trakt_formatted_movies_watched.csv", 
        "temp_trakt_formatted_shows_watched.csv",
        "temp_trakt_formatted_movies_watchlist.csv", 
        "temp_trakt_formatted_shows_watchlist.csv",
        
        # 日志文件
        "match_success.csv",
        "match_failed.csv"
    ]

    # 获取当前时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 遍历并归档文件
    for filename in files_to_archive:
        file_path = os.path.join(script_dir, filename)
        if os.path.exists(file_path):
            # 创建带时间戳的新文件名
            new_filename = f"{timestamp}_{filename}"
            archive_path = os.path.join(old_docs_dir, new_filename)
            
            try:
                shutil.move(file_path, archive_path)
                print(f"[归档] 已将 {filename} 移动到 {new_filename}")
            except Exception as e:
                print(f"[警告] 无法归档 {filename}: {e}")

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.ini")

# 读取配置文件
def read_config():
    config = configparser.ConfigParser()
    
    # 如果配置文件不存在，创建默认配置
    if not os.path.exists(CONFIG_PATH):
        # 使用多行字符串来保留注释
        config_content = '''\
# 配置文件说明：此文件用于 Bangumi to Trakt 转换脚本的设置
#True/False

[General]
# 输入文件名 (必填项)
input_file = 请输入你的文件名.csv

# 是否开启Movies（电影）/Shows（剧集）分类导出
separate_export = True

# 是否开启已看/想看分类导出（watched 和 watchlist 分别导出）
detailed_export = True

# 是否优先使用 TMDb ID（而非 IMDb ID）
prefer_tmdb_id = True

# 是否禁用年份匹配
disable_year_match = False

# 首行ID标识符方案
# 为1时使用tmdb或imdb(智能判断)
# 为2时使用tmdb_id或imdb_id(智能判断)
# 1适用于第三方脚本导入，2适用于官方导入
id_format = 1

[TMDb]
# TMDb API Key (必填项)
api_key = 请输入你的API Key(API密钥)

[Statuses]
# Bangumi条目状态定义
# 你期望导入trakt“历史”的
watched_statuses = 看过,读过,听过

# 你期望导入trakt“列表/收藏”的
watchlist_statuses = 在看,在读,在听,想看,想读,想听

# 被忽略的状态/你期望被忽略不导入的
ignored_statuses = 搁置,抛弃,在玩,想玩,玩过
'''
        
        # 直接写入包含注释的完整文件内容
        with open(CONFIG_PATH, 'w', encoding='utf-8') as configfile:
            configfile.write(config_content)
    
    # 读取配置文件
    config.read(CONFIG_PATH, encoding='utf-8')
    return config

# 从配置中加载配置项
config = read_config()

# 输入和输出文件路径（相对路径）
INPUT_CSV = os.path.join(SCRIPT_DIR, config.get('General', 'input_file'))
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "trakt_formatted.csv")
OUTPUT_MOVIES_CSV = os.path.join(SCRIPT_DIR, "trakt_formatted_movies.csv")
OUTPUT_SHOWS_CSV = os.path.join(SCRIPT_DIR, "trakt_formatted_shows.csv")
OUTPUT_MOVIES_WATCHED_CSV = os.path.join(SCRIPT_DIR, "trakt_formatted_movies_watched.csv")
OUTPUT_SHOWS_WATCHED_CSV = os.path.join(SCRIPT_DIR, "trakt_formatted_shows_watched.csv")
OUTPUT_MOVIES_WATCHLIST_CSV = os.path.join(SCRIPT_DIR, "trakt_formatted_movies_watchlist.csv")
OUTPUT_SHOWS_WATCHLIST_CSV = os.path.join(SCRIPT_DIR, "trakt_formatted_shows_watchlist.csv")
OUTPUT_WATCHED_CSV = os.path.join(SCRIPT_DIR, "trakt_formatted_watched.csv")
OUTPUT_WATCHLIST_CSV = os.path.join(SCRIPT_DIR, "trakt_formatted_watchlist.csv")

TEMP_CSV = os.path.join(SCRIPT_DIR, "temp_trakt_formatted.csv")
TEMP_MOVIES_CSV = os.path.join(SCRIPT_DIR, "temp_trakt_formatted_movies.csv")
TEMP_SHOWS_CSV = os.path.join(SCRIPT_DIR, "temp_trakt_formatted_shows.csv")
TEMP_MOVIES_WATCHED_CSV = os.path.join(SCRIPT_DIR, "temp_trakt_formatted_movies_watched.csv")
TEMP_SHOWS_WATCHED_CSV = os.path.join(SCRIPT_DIR, "temp_trakt_formatted_shows_watched.csv")
TEMP_MOVIES_WATCHLIST_CSV = os.path.join(SCRIPT_DIR, "temp_trakt_formatted_movies_watchlist.csv")
TEMP_SHOWS_WATCHLIST_CSV = os.path.join(SCRIPT_DIR, "temp_trakt_formatted_shows_watchlist.csv")
TEMP_WATCHED_CSV = os.path.join(SCRIPT_DIR, "temp_trakt_formatted_watched.csv")
TEMP_WATCHLIST_CSV = os.path.join(SCRIPT_DIR, "temp_trakt_formatted_watchlist.csv")

# 匹配日志文件
MATCH_SUCCESS_LOG = os.path.join(SCRIPT_DIR, "match_success.csv")
MATCH_FAILED_LOG = os.path.join(SCRIPT_DIR, "match_failed.csv")

# 打印详细错误信息
def print_error_details():
    print("发生错误，详细信息：")
    print("-" * 50)
    traceback.print_exc()
    print("-" * 50)

# 转换日期格式为 ISO 8601
def convert_to_iso8601(date_str):
    try:
        # 尝试多种日期格式
        date_formats = [
            "%Y-%m-%d",  # YYYY-MM-DD
            "%Y/%m/%d",  # YYYY/MM/DD
            "%Y.%m.%d",  # YYYY.MM.DD
            "%Y-%m-%d %H:%M:%S",  # YYYY-MM-DD HH:MM:SS
            "%Y-%m-%d %H:%M",  # YYYY-MM-DD HH:MM
            "%Y-%m-%dT%H:%M:%S%z"  # ISO 8601 with timezone
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                
                # 处理带时区的 ISO 8601 格式
                if '%z' in fmt:
                    # 转换为 UTC
                    dt = dt.astimezone(timezone.utc)
                else:
                    # 对于没有时区的日期，添加 UTC 时区
                    dt = dt.replace(tzinfo=timezone.utc)
                
                # 使用 isoformat() 确保正确的 ISO 8601 格式
                converted = dt.isoformat().replace('+00:00', 'Z')
                return converted
            except ValueError:
                continue
        
        print(f"警告：无法解析日期: {date_str}")
        return None
    except Exception as e:
        print(f"日期转换错误: {e}")
        print_error_details()
        return None

# 新增评分转换函数
def convert_rating(rating_str):
    """
    将用户评价转换为 trakt 平台的评分
    """
    try:
        # 移除非数字字符
        rating_str = ''.join(filter(str.isdigit, str(rating_str)))
        
        if not rating_str:
            return ""
        
        rating = int(rating_str)
        
        # 将 10 分制转换为 trakt 的 10 分制
        return str(rating)
    except (ValueError, TypeError):
        return ""

# 其余的 get_imdb_id 函数保持原样，仅在 query_tmdb 中增加 disable_year_match 处理
def get_imdb_id(title_cn, title_jp, year=None, is_tv=False, prefer_tmdb=False, max_retries=3):
    # 从配置中获取 API Key
    TMDB_API_KEY = config.get('TMDb', 'api_key')
    # 获取是否禁用年份匹配的配置
    DISABLE_YEAR_MATCH = config.getboolean('General', 'disable_year_match')
	
    def create_robust_session():
        """
        创建一个具有重试机制的robust会话
        """
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,  # 总重试次数
            status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的HTTP状态码
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # 允许重试的方法
            backoff_factor=0.5  # 重试间隔时间指数增长
        )
        
        # 创建适配器
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        # 绑定适配器
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def calculate_similarity(str1, str2):
        """
        计算两个字符串的相似度
        使用 Levenshtein 距离计算相似度百分比
        """
        if not str1 or not str2:
            return 0
        
        # 归一化处理（去除空格和特殊字符）
        str1 = ''.join(char for char in str1 if char.isalnum())
        str2 = ''.join(char for char in str2 if char.isalnum())
        
        # 计算 Levenshtein 距离
        distance = Levenshtein.distance(str1.lower(), str2.lower())
        max_len = max(len(str1), len(str2))
        
        # 计算相似度百分比
        similarity = (1 - distance / max_len) * 100
        return similarity

    def query_tmdb(title, search_type, title_language):
        try:
            session = create_robust_session()
            
            search_url = f"https://api.themoviedb.org/3/search/{search_type}"
            params = {
                "api_key": TMDB_API_KEY,
                "query": title,
                "language": title_language
            }
    
            # 使用session进行请求，设置更长的超时时间
            response = session.get(search_url, params=params, timeout=(5, 15))
            
            # 检查响应
            response.raise_for_status()
            
            data = response.json()

            if "results" in data and len(data["results"]) > 0:
                # 获取原始搜索名称（中文或日文）
                original_titles = [title_cn, title_jp]
                
                # 处理匹配逻辑
                best_matches = []
                for item in data["results"]:
                    # 获取 API 返回的标题（尝试多个字段）
                    api_titles = [
                        item.get('name', ''),
                        item.get('original_name', ''),
                        item.get('title', ''),
                        item.get('original_title', '')
                    ]
                    
                    # 计算最大相似度
                    max_similarity = 0
                    api_match_title = ''
                    for orig_title in original_titles:
                        for api_title in api_titles:
                            similarity = calculate_similarity(orig_title, api_title)
                            if similarity > max_similarity:
                                max_similarity = similarity
                                api_match_title = api_title
                    
                    # 年份匹配（如果未禁用年份匹配）
                    year_match = False
                    if not DISABLE_YEAR_MATCH and year and max_similarity >= 50:
                        if search_type == 'tv':
                            year_match = item.get('first_air_date', '').startswith(str(year))
                        else:
                            year_match = item.get('release_date', '').startswith(str(year))
                    
                    # 添加到最佳匹配列表
                    best_matches.append({
                        'item': item,
                        'similarity': max_similarity,
                        'year_match': year_match,
                        'match_title': api_match_title
                    })
                
                # 根据是否禁用年份匹配选择排序方式
                if DISABLE_YEAR_MATCH:
                    # 仅根据相似度排序
                    best_matches.sort(key=lambda x: x['similarity'], reverse=True)
                else:
                    # 保持原有的排序逻辑
                    best_matches.sort(
                        key=lambda x: (x['similarity'] >= 50, x['year_match'], x['similarity']), 
                        reverse=True
                    )
                
                # 选择最佳匹配
                if best_matches and best_matches[0]['similarity'] >= 50:
                    best_match = best_matches[0]['item']
                    tmdb_id = best_match["id"]
                    
                    # 查询 IMDb ID
                    external_url = f"https://api.themoviedb.org/3/{search_type}/{tmdb_id}/external_ids"
                    try:
                        session = create_robust_session()
                        external_response = session.get(external_url, params={"api_key": TMDB_API_KEY}, timeout=(10, 30))
                        external_response.raise_for_status()
                        external_data = external_response.json()
                    except requests.exceptions.RequestException as e:
                        print(f"外部ID查询错误: {e}")
                        external_data = {}
                    
                    imdb_id = external_data.get("imdb_id")
                    
                    if imdb_id:
                        return {
                            'tmdb': str(tmdb_id),
                            'imdb': imdb_id,
                            'match_name': best_matches[0]['match_title'],
                            'similarity': best_matches[0]['similarity'],
                            'type': search_type
                        }
                    else:
                        return {
                            'tmdb': str(tmdb_id),
                            'imdb': None,
                            'match_name': best_matches[0]['match_title'],
                            'similarity': best_matches[0]['similarity'],
                            'type': search_type
                        }
            
            return None
        except requests.exceptions.RequestException as e:
            print(f"查询错误: {e}")
            return None

    # 为 get_imdb_id 添加重试机制
    for attempt in range(max_retries):
        try:
            # 处理包含特殊字符的标题的部分标题获取
            def split_title(title):
                # 保留更多有意义的标题部分
                # 尝试保留更多关键词，同时去除括号、版本等信息
                for split_char in ['：', ':', '（', '(', ' ']:
                    if split_char in title:
                        parts = title.split(split_char)
                        # 优先保留第一部分，但排除一些无意义的前缀
                        if parts[0] not in ['Re', '第', '第一', '第二', '第三', '第四', '第五']:
                            return parts[0]
                return title
            
            def clean_title(title):
                # 去除特定的版本、季数等信息
                title = re.sub(r'第\S*季', '', title)  # 去除"第X季"
                title = re.sub(r'第\S*期', '', title)  # 去除"第X期"
                title = re.sub(r'[（\(].+[）\)]', '', title)  # 去除括号及其内容
                title = re.sub(r'^\s*Re[:：]\s*', '', title)  # 去除开头的"Re:"
                return title.strip()

            # 如果中文名和日文名都为空，直接返回 None
            if not title_cn and not title_jp:
                return None

            # 搜索顺序优化
            tv_search_patterns = []
            movie_search_patterns = []

            # 1. 完整日文名搜索 (TV)
            if title_jp and title_jp.strip():
                tv_search_patterns.extend([
                    (title_jp, 'tv', 'ja')
                ])

            # 2. 部分日文名搜索 (TV)
            part_jp = split_title(title_jp) if title_jp else None
            if part_jp and len(part_jp) > 2:
                tv_search_patterns.extend([
                    (part_jp, 'tv', 'ja')
                ])

            # 3. 完整中文名搜索 (TV)
            if title_cn and title_cn.strip():
                tv_search_patterns.extend([
                    (title_cn, 'tv', 'zh-CN')
                ])

            # 4. 部分中文名搜索 (TV)
            part_cn = split_title(title_cn) if title_cn else None
            if part_cn and len(part_cn) > 2:
                tv_search_patterns.extend([
                    (part_cn, 'tv', 'zh-CN')
                ])

            # Movie 搜索模式（仅在 TV 搜索全部失败后使用）
            # 1. 完整日文名搜索 (Movie)
            if title_jp and title_jp.strip():
                movie_search_patterns.extend([
                    (title_jp, 'movie', 'ja')
                ])

            # 2. 部分日文名搜索 (Movie)
            if part_jp and len(part_jp) > 2:
                movie_search_patterns.extend([
                    (part_jp, 'movie', 'ja')
                ])

            # 3. 完整中文名搜索 (Movie)
            if title_cn and title_cn.strip():
                movie_search_patterns.extend([
                    (title_cn, 'movie', 'zh-CN')
                ])

            # 4. 部分中文名搜索 (Movie)
            if part_cn and len(part_cn) > 2:
                movie_search_patterns.extend([
                    (part_cn, 'movie', 'zh-CN')
                ])

            # 首先尝试 TV 搜索
            for title, search_type, language in tv_search_patterns:
                result = query_tmdb(title, search_type, language)
                if result:
                    return result

            # 如果 TV 搜索全部失败，再尝试 Movie 搜索
            for title, search_type, language in movie_search_patterns:
                result = query_tmdb(title, search_type, language)
                if result:
                    return result

            return None
        except requests.exceptions.RequestException as e:
            print(f"网络错误，第 {attempt + 1} 次尝试失败: {e}")
            time.sleep(2)
        except Exception as e:
            print(f"查询错误，第 {attempt + 1} 次尝试失败: {e}")
            time.sleep(2)
    
    return None

# main 函数中增加 rating 处理
def main():
    # 在读取配置和处理文件之前调用归档函数
    archive_old_files(SCRIPT_DIR)
    
    # 从配置文件读取配置项
    PREFER_TMDB_ID = config.getboolean('General', 'prefer_tmdb_id')
    SEPARATE_EXPORT = config.getboolean('General', 'separate_export')
    DETAILED_EXPORT = config.getboolean('General', 'detailed_export')
    ID_FORMAT = config.get('General', 'id_format', fallback='1')

    # 调整文件打开策略
    files_to_open = [(TEMP_CSV, 'w'), (MATCH_SUCCESS_LOG, 'w'), (MATCH_FAILED_LOG, 'w')]
    
    # 根据 SEPARATE_EXPORT 和 DETAILED_EXPORT 动态调整文件打开策略
    if not SEPARATE_EXPORT and DETAILED_EXPORT:
        # 当不分类但需要详细导出时
        files_to_open.extend([
            (TEMP_WATCHED_CSV, 'w'),  # 新增：统一的已看文件
            (TEMP_WATCHLIST_CSV, 'w')  # 新增：统一的想看文件
        ])
    elif SEPARATE_EXPORT:
        # 原有的分类文件
        files_to_open.extend([
            (TEMP_MOVIES_CSV, 'w'), 
            (TEMP_SHOWS_CSV, 'w')
        ])
        
        # 详细导出时添加更多文件
        if DETAILED_EXPORT:
            files_to_open.extend([
                (TEMP_MOVIES_WATCHED_CSV, 'w'), 
                (TEMP_SHOWS_WATCHED_CSV, 'w'),
                (TEMP_MOVIES_WATCHLIST_CSV, 'w'), 
                (TEMP_SHOWS_WATCHLIST_CSV, 'w')
            ])

    # 根据ID_FORMAT调整表头
    def get_headers(ID_FORMAT, PREFER_TMDB_ID):
        if ID_FORMAT == '2':
            return ["tmdb_id" if PREFER_TMDB_ID else "imdb_id", "watched_at", "watchlisted_at", "rating", "rated_at"]
        else:  # ID_FORMAT == '1'
            return ["tmdb" if PREFER_TMDB_ID else "imdb", "watched_at", "watchlisted_at", "rating", "rated_at"]

    headers = get_headers(ID_FORMAT, PREFER_TMDB_ID)
    
    # 动态生成头部配置
    headers_config = {
        'main': headers,
        'movies': headers,
        'shows': headers,
        'movies_watched': headers,
        'shows_watched': headers,
        'movies_watchlist': headers,
        'shows_watchlist': headers,
        'watched': headers,    # 新增：统一的已看文件头
        'watchlist': headers   # 新增：统一的想看文件头
    }

    try:
        print(f"尝试读取文件: {INPUT_CSV}")
        df = pd.read_csv(INPUT_CSV, encoding="utf-8")
        
        print(f"[信息] 读取到 {len(df)} 行数据")

        # 初始化计数器
        count_found = 0
        count_not_found = 0
        count_ignored = 0
        count_duplicate = 0
        count_movies = 0
        count_shows = 0
        count_movies_watched = 0
        count_shows_watched = 0
        count_movies_watchlist = 0
        count_shows_watchlist = 0
        count_watched = 0  # 新增：统一的已看计数
        count_watchlist = 0  # 新增：统一的想看计数

        processed_entries = set()

        # 打开文件和写入器（仅打开配置中需要的文件）
        file_handles = {}
        writers = {}
        for file_path, mode in files_to_open:
            file_handles[file_path] = open(file_path, mode=mode, newline='', encoding="utf-8", buffering=1)
        
        # 动态创建写入器
        writers = {}
        if TEMP_CSV in file_handles:
            writers['main'] = csv.writer(file_handles[TEMP_CSV])
            writers['main'].writerow(headers_config['main'])
        
        # 根据配置添加特定写入器
        if not SEPARATE_EXPORT and DETAILED_EXPORT:
            # 当不分类但需要详细导出时
            if TEMP_WATCHED_CSV in file_handles:
                writers['watched'] = csv.writer(file_handles[TEMP_WATCHED_CSV])
                writers['watched'].writerow(headers_config['watched'])
            
            if TEMP_WATCHLIST_CSV in file_handles:
                writers['watchlist'] = csv.writer(file_handles[TEMP_WATCHLIST_CSV])
                writers['watchlist'].writerow(headers_config['watchlist'])
        
        elif SEPARATE_EXPORT:
            # 原有的分类文件写入器
            if TEMP_MOVIES_CSV in file_handles:
                writers['movies'] = csv.writer(file_handles[TEMP_MOVIES_CSV])
                writers['movies'].writerow(headers_config['movies'])
            
            if TEMP_SHOWS_CSV in file_handles:
                writers['shows'] = csv.writer(file_handles[TEMP_SHOWS_CSV])
                writers['shows'].writerow(headers_config['shows'])
            
            # 详细导出时
            if DETAILED_EXPORT:
                if TEMP_MOVIES_WATCHED_CSV in file_handles:
                    writers['movies_watched'] = csv.writer(file_handles[TEMP_MOVIES_WATCHED_CSV])
                    writers['movies_watched'].writerow(headers_config['movies_watched'])
                
                if TEMP_SHOWS_WATCHED_CSV in file_handles:
                    writers['shows_watched'] = csv.writer(file_handles[TEMP_SHOWS_WATCHED_CSV])
                    writers['shows_watched'].writerow(headers_config['shows_watched'])
                
                if TEMP_MOVIES_WATCHLIST_CSV in file_handles:
                    writers['movies_watchlist'] = csv.writer(file_handles[TEMP_MOVIES_WATCHLIST_CSV])
                    writers['movies_watchlist'].writerow(headers_config['movies_watchlist'])
                
                if TEMP_SHOWS_WATCHLIST_CSV in file_handles:
                    writers['shows_watchlist'] = csv.writer(file_handles[TEMP_SHOWS_WATCHLIST_CSV])
                    writers['shows_watchlist'].writerow(headers_config['shows_watchlist'])

        success_writer = csv.writer(file_handles[MATCH_SUCCESS_LOG])
        failed_writer = csv.writer(file_handles[MATCH_FAILED_LOG])
        
        success_writer.writerow(["中文名", "日文名", "匹配ID", "匹配名称", "相似度", "类型"])
        failed_writer.writerow(["中文名", "日文名", "失败原因"])

        # 读取状态
        watched_statuses = config.get('Statuses', 'watched_statuses').split(',')
        watchlist_statuses = config.get('Statuses', 'watchlist_statuses').split(',')
        ignored_statuses = config.get('Statuses', 'ignored_statuses').split(',')
        
        # 逐行处理并写入
        for index, row in df.iterrows():
            try:
                # 使用pandas的方法严格处理空值
                title_cn = row.get("中文", "")
                title_jp = row.get("日文", "")

                # 严格的空值检查
                if pd.isna(title_cn):
                    title_cn = ""
                if pd.isna(title_jp):
                    title_jp = ""

                # 转换为字符串并去除两端空白
                title_cn = str(title_cn).strip()
                title_jp = str(title_jp).strip()

                is_tv = str(row.get("类型", "")).strip() == "动画"
                status = str(row.get("状态", "")).strip()
                watched_at = str(row.get("更新时间", "")).strip()
                
                # 新增：处理评分
                rating = convert_rating(row.get("我的评价", ""))
                
                try:
                    year = int(str(row.get("放送", "")).split('-')[0]) if str(row.get("放送", "")) else None
                except (ValueError, TypeError):
                    year = None

                print(f"处理行 {index}: 中文名={title_cn}, 日文名={title_jp}, 状态={status}, 年份={year}")
                
                # 跳过被忽略的状态
                if status in ignored_statuses:
                    count_ignored += 1
                    print(f"忽略状态为 {status} 的条目")
                    failed_writer.writerow([title_cn, title_jp, f"被忽略的状态: {status}"])
                    file_handles[MATCH_FAILED_LOG].flush()
                    continue
                
                # 如果两个标题都为空，跳过此行
                if not title_cn and not title_jp:
                    print("标题为空，跳过")
                    count_not_found += 1
                    failed_writer.writerow([title_cn, title_jp, "标题为空"])
                    file_handles[MATCH_FAILED_LOG].flush()
                    continue
                
                # 根据配置返回正确的ID
                def get_id_column(match_result, ID_FORMAT, PREFER_TMDB_ID):
                    if ID_FORMAT == '2':
                        # 对于ID_FORMAT为2的情况，使用不同的键名映射
                        return match_result['tmdb'] if PREFER_TMDB_ID else match_result['imdb']
                    else:  # ID_FORMAT == '1'
                        return match_result['tmdb'] if PREFER_TMDB_ID else match_result['imdb']

                match_result = get_imdb_id(title_cn, title_jp, year, is_tv, prefer_tmdb=PREFER_TMDB_ID)
                
                if match_result:
                    imdb_id = get_id_column(match_result, ID_FORMAT, PREFER_TMDB_ID)
                    
                # 在处理每一行的循环中，替换原有的重复检查逻辑
                if match_result:
                    imdb_id = get_id_column(match_result, ID_FORMAT, PREFER_TMDB_ID)
                    media_type = match_result.get('type', 'unknown')
                    
                    # 创建一个唯一的条目标识，包括ID、媒体类型和状态
                    entry_key = (imdb_id, media_type, '已看' if status in watched_statuses else '想看')
                    
                    # 检查是否已处理过完全相同的条目
                    if entry_key in processed_entries:
                        print(f"跳过重复条目：{title_cn} / {title_jp}，ID: {imdb_id}，类型: {media_type}，状态: {status}")
                        
                        # 在匹配失败日志中记录重复条目
                        failed_writer.writerow([
                            title_cn, 
                            title_jp, 
                            f"重复条目，ID: {imdb_id}，类型: {media_type}，状态: {status}"
                        ])
                        file_handles[MATCH_FAILED_LOG].flush()
                        
                        count_duplicate += 1  # 增加重复计数
                        continue
                    
                    # 将此条目添加到已处理集合
                    processed_entries.add(entry_key)

                    match_name = match_result.get('match_name', '')
                    similarity = match_result.get('similarity', 0)
                    media_type = match_result.get('type', 'unknown')
                    
                    iso_watched_at = convert_to_iso8601(watched_at)
                    
                    # 通用文件写入逻辑
                    if status in watched_statuses:
                        writers['main'].writerow([
                            imdb_id,
                            iso_watched_at or "",
                            "",
                            rating,
                            iso_watched_at or "" if rating else ""
                        ])
                        
                        # 不分类，但需要详细导出
                        if not SEPARATE_EXPORT and DETAILED_EXPORT:
                            writers['watched'].writerow([
                                imdb_id,
                                iso_watched_at or "",
                                "",
                                rating,
                                iso_watched_at or "" if rating else ""
                            ])
                            count_watched += 1
                        
                        elif SEPARATE_EXPORT:
                            if media_type == 'movie':
                                writers['movies'].writerow([
                                    imdb_id,
                                    iso_watched_at or "",
                                    "",
                                    rating,
                                    iso_watched_at or "" if rating else ""
                                ])
                                count_movies += 1
                                
                                if DETAILED_EXPORT:
                                    writers['movies_watched'].writerow([
                                        imdb_id,
                                        iso_watched_at or "",
                                        "",
                                        rating,
                                        iso_watched_at or "" if rating else ""
                                    ])
                                    count_movies_watched += 1
                            
                            elif media_type == 'tv':
                                writers['shows'].writerow([
                                    imdb_id,
                                    iso_watched_at or "",
                                    "",
                                    rating,
                                    iso_watched_at or "" if rating else ""
                                ])
                                count_shows += 1
                                
                                if DETAILED_EXPORT:
                                    writers['shows_watched'].writerow([
                                        imdb_id,
                                        iso_watched_at or "",
                                        "",
                                        rating,
                                        iso_watched_at or "" if rating else ""
                                    ])
                                    count_shows_watched += 1
                    
                    elif status in watchlist_statuses:
                        writers['main'].writerow([
                            imdb_id,
                            "",
                            iso_watched_at or "",
                            rating,
                            iso_watched_at or "" if rating else ""
                        ])
                        
                        # 不分类，但需要详细导出
                        if not SEPARATE_EXPORT and DETAILED_EXPORT:
                            writers['watchlist'].writerow([
                                imdb_id,
                                "",
                                iso_watched_at or "",
                                rating,
                                iso_watched_at or "" if rating else ""
                            ])
                            count_watchlist += 1
                        
                        elif SEPARATE_EXPORT:
                            if media_type == 'movie':
                                writers['movies'].writerow([
                                    imdb_id,
                                    "",
                                    iso_watched_at or "",
                                    rating,
                                    iso_watched_at or "" if rating else ""
                                ])
                                count_movies += 1
                                
                                if DETAILED_EXPORT:
                                    writers['movies_watchlist'].writerow([
                                        imdb_id,
                                        "",
                                        iso_watched_at or "",
                                        rating,
                                        iso_watched_at or "" if rating else ""
                                    ])
                                    count_movies_watchlist += 1
                            
                            elif media_type == 'tv':
                                writers['shows'].writerow([
                                    imdb_id,
                                    "",
                                    iso_watched_at or "",
                                    rating,
                                    iso_watched_at or "" if rating else ""
                                ])
                                count_shows += 1
                                
                                if DETAILED_EXPORT:
                                    writers['shows_watchlist'].writerow([
                                        imdb_id,
                                        "",
                                        iso_watched_at or "",
                                        rating,
                                        iso_watched_at or "" if rating else ""
                                    ])
                                    count_shows_watchlist += 1
                    
                    success_writer.writerow([
                        title_cn, 
                        title_jp, 
                        imdb_id, 
                        match_name, 
                        f"{similarity:.2f}%",
                        media_type
                    ])
                    file_handles[MATCH_SUCCESS_LOG].flush()
                    
                    count_found += 1
                else:
                    count_not_found += 1
                    print(f"未找到 ID：{title_cn} / {title_jp}")
                    failed_writer.writerow([
                        title_cn, 
                        title_jp, 
                        "未找到匹配ID（尝试了TV和电影搜索）"
                    ])
                    file_handles[MATCH_FAILED_LOG].flush()
                
                # 将所有文件缓冲区刷新
                for file_handle in file_handles.values():
                    file_handle.flush()
                
                time.sleep(0.3)
            
            except Exception as row_error:
                print(f"处理第 {index} 行时出错: {row_error}")
                print_error_details()
                failed_writer.writerow([title_cn, title_jp, str(row_error)])
                file_handles[MATCH_FAILED_LOG].flush()
                continue

        # 关闭所有文件句柄
        for file_handle in file_handles.values():
            file_handle.close()
        # 重命名临时文件为最终输出文件
        if os.path.exists(TEMP_CSV):
            shutil.move(TEMP_CSV, OUTPUT_CSV)
        
        # 根据配置重命名其他临时文件
        if SEPARATE_EXPORT:
            if os.path.exists(TEMP_MOVIES_CSV):
                shutil.move(TEMP_MOVIES_CSV, OUTPUT_MOVIES_CSV)
            if os.path.exists(TEMP_SHOWS_CSV):
                shutil.move(TEMP_SHOWS_CSV, OUTPUT_SHOWS_CSV)
            
            if DETAILED_EXPORT:
                if os.path.exists(TEMP_MOVIES_WATCHED_CSV):
                    shutil.move(TEMP_MOVIES_WATCHED_CSV, OUTPUT_MOVIES_WATCHED_CSV)
                if os.path.exists(TEMP_SHOWS_WATCHED_CSV):
                    shutil.move(TEMP_SHOWS_WATCHED_CSV, OUTPUT_SHOWS_WATCHED_CSV)
                if os.path.exists(TEMP_MOVIES_WATCHLIST_CSV):
                    shutil.move(TEMP_MOVIES_WATCHLIST_CSV, OUTPUT_MOVIES_WATCHLIST_CSV)
                if os.path.exists(TEMP_SHOWS_WATCHLIST_CSV):
                    shutil.move(TEMP_SHOWS_WATCHLIST_CSV, OUTPUT_SHOWS_WATCHLIST_CSV)
        
        # 对于不分类但详细导出的情况
        if not SEPARATE_EXPORT and DETAILED_EXPORT:
            if os.path.exists(TEMP_WATCHED_CSV):
                shutil.move(TEMP_WATCHED_CSV, OUTPUT_WATCHED_CSV)
            if os.path.exists(TEMP_WATCHLIST_CSV):
                shutil.move(TEMP_WATCHLIST_CSV, OUTPUT_WATCHLIST_CSV)
        # 统计输出需要调整
        print("[完成] 处理完成：")
        print(f"- 找到 {count_found} 部作品的 ID")
        print(f"- {count_not_found} 部作品未找到 ID")
        print(f"- {count_ignored} 部作品因状态被忽略")
        print(f"- {count_duplicate} 部作品因重复被跳过")
        
        if not SEPARATE_EXPORT and DETAILED_EXPORT:
            print(f"- 已看作品：{count_watched} 部")
            print(f"- 想看作品：{count_watchlist} 部")
        
        elif SEPARATE_EXPORT:
            print(f"- {count_movies} 部电影")
            print(f"- {count_shows} 部电视节目")
            
            if DETAILED_EXPORT:
                print(f"  - 已看电影：{count_movies_watched} 部")
                print(f"  - 想看电影：{count_movies_watchlist} 部")
                print(f"  - 已看电视节目：{count_shows_watched} 部")
                print(f"  - 想看电视节目：{count_shows_watchlist} 部")
        
        print(f"[输出] 结果已保存至 {OUTPUT_CSV}")
        
        # 这里还需要补充其他输出路径的打印
        
        print(f"[日志] 匹配成功日志：{MATCH_SUCCESS_LOG}")
        print(f"[日志] 匹配失败日志：{MATCH_FAILED_LOG}")

        # 添加一个暂停，防止窗口立即关闭
        input("处理完成，按回车键退出...")

    except Exception as e:
        print("整体处理过程出错:")
        print_error_details()
        input("发生错误，按回车键退出...")

if __name__ == "__main__":
    main()