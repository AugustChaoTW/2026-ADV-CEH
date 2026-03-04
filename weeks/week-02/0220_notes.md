# 進階駭客攻防 0220 notes



## 1. [runme.py](https://play.picoctf.org/practice/challenge/250)

### 藍方

1. 建立 nginx
2. 把檔案 [runme.py](https://artifacts.picoctf.net/c/34/runme.py) 放在指定位置

```
mousepad /var/www/html/index.html
# or use 
nano /var/www/html/index.html
# or use
vi /var/www/html/index.html
```

add following to index.html

```html
<a href="runme.py">runme.py</a>
```

get `runme.py`

```bash
wget https://artifacts.picoctf.net/c/34/runme.py
```

reload http://localhost

4. 提供程式所在位置

> http://10.0.2.15/runme.py

#### install NGINX

**step 1:**
if you are using root permission terminal, you don't need `sudo` 
```bash
sudo apt update # (as root)
sudo apt install nginx
sudo systemctl start nginx 
```

**step 2:**
open firefox to http://localhost

**step 3:**
to modify html in `/var/www/html/index.html`, use this command

```bash
echo "hihi" > /var/www/html/index.html
```


### 紅方
1. get `runme.py` using wget
2. `python runme.py`



## 2. [patchme.py](https://play.picoctf.org/practice/challenge/287)

### 藍方

1. 建立 nginx
2. 把檔案 [patchme.flag.py](https://artifacts.picoctf.net/c/201/patchme.flag.py) and [flag.txt.enc](https://artifacts.picoctf.net/c/201/flag.txt.enc) 放在指定位置
3. 提供程式所在位置


### 紅方


skip to next class
