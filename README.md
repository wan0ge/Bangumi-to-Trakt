# Bangumi-to-Trakt
从Bangumi迁移至Trakt / 导出Bangumi记录到Trakt / CSV文件格式转换


## 方案：

使用[Bangumi](https://github.com/czy0729/Bangumi)客户端的本地备份功能导出CSV文件→使用本项目转换CSV格式内容为Trakt支持的格式内容→使用[trakt](https://github.com/xbgmsharp/trakt)项目将CSV导入Trakt.tv（官方导入也支持但条目成功率不如这个）

本项目将提供全程保姆级教程

### 你需要准备的：

* Python环境

* [Bangumi](https://github.com/czy0729/Bangumi) 本地备份导出后的.csv文件

* [TMDB API](https://www.themoviedb.org/settings/api)（注册登录任意申请）（我暂时提供此API）

* [Trakt API](https://trakt.tv/oauth/applications)（任意创建）

## 开始使用
* 将导出CSV文件放入本项目文件夹内（\Bangumi-to-Trakt-master\Bangumi×××××××_××××-××-××_××-××-××.csv）

* 修改本项目config.ini配置文件，只需要填写文件名和TMDb API Key就能使用
 
* 启动Bangumi-to-Trakt.py开始转换

* 使用[trakt](https://github.com/xbgmsharp/trakt)项目将CSV导入

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
