# Bangumi-to-Trakt
从Bangumi迁移至Trakt / 导出Bangumi记录到Trakt / CSV文件格式转换

### 预览
<img src="https://github.com/user-attachments/assets/3f322a78-9385-4b3f-988a-b13b47e2660d" width="800px">

<img src="https://github.com/user-attachments/assets/9f84a3cc-2d87-41b9-b03f-4d0affdf7852" width="800px">
<img src="https://github.com/user-attachments/assets/6ffe8154-e907-4fdf-a075-9f1aeeb13de1" width="800px">

<img src="https://github.com/user-attachments/assets/5822bdc2-b15a-4475-a69f-23c27ea8e665" width="800px">
<img src="https://github.com/user-attachments/assets/efb879a4-67bb-40ea-aba8-a6bdf59e7f5f" width="800px">

## 方案：

使用[Bangumi](https://github.com/czy0729/Bangumi)客户端的本地备份功能导出CSV文件 → 使用本项目转换CSV格式内容为Trakt支持的格式内容 → 使用[trakt](https://github.com/xbgmsharp/trakt)项目将CSV导入Trakt.tv(官方导入也支持但条目成功率不如这个)

本项目将提供全程保姆级教程

### 你需要准备的：

* Python环境

* [Bangumi](https://github.com/czy0729/Bangumi) 本地备份导出后的.csv文件

* [TMDB API](https://www.themoviedb.org/settings/api)（注册登录任意申请）（我暂时提供此API）

* [Trakt API](https://trakt.tv/oauth/applications)（任意创建）

## 开始使用
* 下载本项目和[trakt](https://github.com/xbgmsharp/trakt)项目并解压

   下载[本项目](https://github.com/wan0ge/Bangumi-to-Trakt/archive/refs/heads/master.zip)

   下载[trakt](https://github.com/xbgmsharp/trakt/archive/refs/heads/master.zip)

* Python安装所需库
```
pip install requests pandas python-Levenshtein python-dateutil simplejson
```

* 使用[Bangumi](https://github.com/czy0729/Bangumi)本地备份功能导出CSV文件

* 将导出CSV文件放入本项目文件夹内（\Bangumi-to-Trakt-master\Bangumi×××××××_××××-××-××_××-××-××.csv）

* 修改本项目config.ini配置文件，只需要填写文件名和TMDb API Key就能使用
 
* 启动Bangumi-to-Trakt.py开始转换然后等待

* 使用[trakt](https://github.com/xbgmsharp/trakt)项目将CSV导入（CSV放入该项目文件夹内）

* 导入观看过的Movies（电影）到历史记录，并根据原日期标记
```
python import_trakt.py -c config.ini -f tmdb -i trakt_formatted_movies_watched.csv -l history -t movies -w
```
* 导入未观看的Movies（电影）到观看列表
```
python import_trakt.py -c config.ini -f tmdb -i trakt_formatted_movies_watchlist.csv -l watchlist -t movies
```
* 导入观看过的Shows（剧集）到历史记录，并根据原日期标记
```
python import_trakt.py -c config.ini -f tmdb -i trakt_formatted_shows_watched.csv -l history -t shows -w
```
* 导入未观看的Shows（剧集）到观看列表
```
python import_trakt.py -c config.ini -f tmdb -i trakt_formatted_shows_watchlist.csv -l watchlist -t shows
```
* 导入movies评级
```
python import_trakt.py -c config.ini -f tmdb -i trakt_formatted_movies.csv -l ratings -t movies -r
```
* 导入Shows评级
```
python import_trakt.py -c config.ini -f tmdb -i trakt_formatted_shows.csv -l ratings -t Shows -r
```

#### 本项目生成文件说明
本项目在配置默认全开的情况下生成文件高达``9``个
* `match_failed.csv`：条目匹配失败日志
* `match_success.csv`：条目匹配成功日志
* `trakt_formatted.csv`：未分类的所有转换成功条目
* `trakt_formatted_movies.csv`：所有Movies（电影）条目
* `trakt_formatted_movies_watched.csv`：Movies（电影）中看过的的条目
* `trakt_formatted_movies_watchlist.csv`：Movies（电影）中未看完/未看过的的条目
* `trakt_formatted_shows.csv`：所有Shows（剧集）条目
* `trakt_formatted_shows_watched.csv`：Shows（剧集）中看过的的条目
* `trakt_formatted_shows_watchlist.csv`：Shows（剧集）中未看完/未看过的的条目

#### 本项目支持的csv文件格式（"中文"或"日文"为必须）
```
"ID","类型","中文","日文","放送","排名","评分","话数","看到","状态","标签","我的评价","我的简评","私密","更新时间"
277727,"动画","时光碎片","フラグタイム","2020-05-13",5059,6.5,1,"","看过","百合 剧场版","","","","2025-03-22T03:38:45+08:00"
174584,"动画","轻拍翻转小魔女","フリップフラッパーズ","2016-10-06",928,7.5,13,13,"看过","原创 奇幻 百合","","","","2025-03-22T01:04:17+08:00"
```
#### 本项目转换后的csv文件格式
```
tmdb,watched_at,watchlisted_at,rating,rated_at
630027,2025-03-21T19:38:45Z,,,
68272,2025-03-21T17:04:17Z,,,
```

## 给小白的详细使用说明
* 先安装Python：[Python安装教程-哔哩哔哩](https://www.bilibili.com/video/av421893699)(不要忘记勾选 "Add Python to PATH")
* win+x打开Windows PowerShell一键安装所需Python库
```
pip install requests pandas python-Levenshtein python-dateutil simplejson
```
* 申请[TMDB API](https://www.themoviedb.org/settings/api)：[TMDB API Key申请 - 绿联NAS私有云](https://www.ugnas.com/tutorial-detail/id-226.html)(随便填，申请就过)
* 申请[Trakt API](https://trakt.tv/oauth/applications)：名称和描述随便填，Redirect uri(重定向uri)填写``urn:ietf:wg:oauth:2.0:oob``其余留空，然后点击保存
* 将TMDB API密钥填入本项目config.ini配置文件
* 在[trakt](https://github.com/xbgmsharp/trakt)项目文件夹内地址栏输入`cmd`输入命令创建config.ini配置文件
```
python export_trakt.py
```
* 然后打开将Trakt API的Client ID和Client Secret分别填入对应项
* 然后cmd输入命令使用 PIN 码方法对 Trakt.tv API 进行验证，它将生成一个 access_token 和 refresh_token。脚本会生成一个授权链接，需要复制在浏览器中打开，然后将 PIN 码粘贴回脚本。生成的访问令牌和刷新令牌会自动保存到配置文件 config.ini 中。
```
python export_trakt.py
```
* [开始使用](https://github.com/wan0ge/Bangumi-to-Trakt?tab=readme-ov-file#%E5%BC%80%E5%A7%8B%E4%BD%BF%E7%94%A8)
