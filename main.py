import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
import re


#START_URL = 'https://ys.mihoyo.com/main/character/mondstadt?char=0'
START_URL = "https://genshin.hoyoverse.com/en/character/mondstadt?char=0"


class HtmlReader:
    def __init__(self) -> None:
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/68.0.3440.106 Safari/537.36",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh,en-US;q=0.9,en;q=0.8",
        }
        self.timeout = 10

    def get_html(self, url: str) -> str:
        try:
            r = requests.get(url, headers=self.headers, timeout=self.timeout)
            return r.text
        except ConnectionError as e:
            print(f"Cannot reach {url}. {e}")
            return None

    def download(self, url: str, path: Path) -> None:
        r = requests.get(url, headers=self.headers, timeout=self.timeout)
        if r.status_code == 200:
            with path.open("wb") as f:
                for chunk in r:
                    f.write(chunk)
        else:
            print(f"Cannot download {url}")


class DynamicHtmlReader:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--log-level=3")
        self.url = ""
        self.driver = webdriver.Chrome(options=options)

    def get_html(self, url: str) -> str:
        self.driver.implicitly_wait(2)
        self.driver.get(url)
        self.driver.find_element(By.CLASS_NAME, "character__city")

        self.url = self.driver.current_url
        return self.driver.page_source

    def close(self):
        self.driver.close()


def main():
    d_reader = DynamicHtmlReader()
    reader = HtmlReader()
    html = d_reader.get_html(START_URL)
    soup = BeautifulSoup(html, "lxml")
    hostname = urlparse(START_URL).netloc

    # 输出文件夹
    output_dir_full = Path("full")
    if not output_dir_full.exists():
        output_dir_full.mkdir()

    output_dir_face = Path("face")
    if not output_dir_face.exists():
        output_dir_face.mkdir()

    def get_chars_in_city(url: str, city: str, html=None):
        if not html:
            _reader = DynamicHtmlReader()
            html = _reader.get_html("https://" + url)
            _reader.close()
        soup = BeautifulSoup(html, "lxml")

        output_full = output_dir_full / city
        if not output_full.exists():
            output_full.mkdir()
        output_face = output_dir_face / city
        if not output_face.exists():
            output_face.mkdir()

        full_imgs = soup("img", class_="character__person")
        face_img_cont = soup("ul", class_="character__page--render")
        face_imgs = face_img_cont[0].find_all("img")
        names_p = face_img_cont[0].find_all("p")

        for i, name_p in enumerate(names_p):
            filename = name_p.contents[0] + ".png"
            reader.download(full_imgs[i]["src"], output_dir_full / city / filename)
            reader.download(face_imgs[i]["src"], output_dir_face / city / filename)

    # 获取所有城市
    first_iter = True
    for li in soup("li", class_="character__city"):
        a = li.a
        if not a:
            continue
        city_name = a.string.strip()
        print(a.string, a["href"])
        city_url = hostname + a["href"]
        if first_iter:
            get_chars_in_city(city_url, city_name, html)
            first_iter = False
        else:
            get_chars_in_city(city_url, city_name)

    d_reader.close()


if __name__ == "__main__":
    main()
